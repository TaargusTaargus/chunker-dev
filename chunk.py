from chunkdb import ChunkDB
from multiprocessing import Process
from os import sep, lstat, symlink, readlink, utime, chmod, chown, chdir, listdir, stat, getcwd, walk
from os.path import islink, isfile, join, isdir, abspath
from utilities import relpath, ensure_path
from random import randint
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from random import randint
from hashlib import md5
from sys import getdefaultencoding
from state import flags

EMPTY_CHUNK_NAME="empty"

class Chunk:
     
  END_OF_CHUNK = '~'

  def __init__( self, name='' ):
    self.used = 0
    self.string = ''
    self.meta = []
    self.chunk_name = name

 
  def concatenate( self, file_handle, str ):
    self.string += str
    
    meta = {}
    
    meta[ 'file_handle' ] = file_handle
    meta[ 'start_in_chunk' ] = self.used
    meta[ 'end_in_chunk' ] = self.used + len( str ) - 1  
    self.meta.append( meta )   
    self.used += len( str )

  def encode( self, charset=getdefaultencoding() ):
    try:
      self.string = self.string.encode( charset )
    except: 
      self.string = b64encode( self.string )
      charset = "b64"
    return charset

  def decode( self, encoding ):
    if encoding == "b64":
      self.string = b64decode( self.string )
    else:
      try:
        self.string = self.string.encode( encoding )
      except:
        print( "WARNING: encountered issue encoding " + self.chunk_name + " contents might be corrupted ... " )
        self.string = self.string.encode( encoding, "replace" )

  def encrypt( self, key, iv ):
    encryptor = AES.new( key, AES.MODE_CBC, iv )
    self.string += self.END_OF_CHUNK
    self.used += len( self.END_OF_CHUNK )
    if self.used % 16 != 0:
      self.string += ' ' * ( 16 - self.used % 16 )
    self.string = encryptor.encrypt( self.string )
 

  def decrypt( self, key, iv ):
    decryptor = AES.new( key, AES.MODE_CBC, iv )
    self.string = decryptor.decrypt( self.string ).rstrip()  
    self.string = self.string[ :( -1 * len( self.END_OF_CHUNK ) ) ]


class Chunker( Process ):

  CHUNK_EXTENSION='.chk'
  
  def __init__( self, db, storage ):
    # threading related stuff
    Process.__init__( self )
    self.chunk_queue = { 'dir': [], 'file': [], 'link': [] }

    # handling user flags
    self.encrypt = flags[ 'encrypt_flag' ]
    self.iv = None if not self.encrypt else ''.join( str( randint( 0, 9 ) ) for _ in range( 16 ) )
    self.verbose = flags[ 'verbose_flag' ]
    self.collapse = flags[ 'collapse_flag' ]
    self.force = flags[ 'force_flag' ]

    # database initialization
    self.meta_db = db
    self.storage = storage

    # chunk accounting
    self.chunk_count = len( self.meta_db.get_related_chunks() )
    self.chunk_size = flags[ 'chunk_size' ]
    self.curr = None


  def __record_permissions__( self, handle, file_stats ):
    self.meta_db.fill_db_from_dict( { 'file_handle': handle,
                                      'file_owner' : file_stats.st_uid,
                                      'file_permissions' : file_stats.st_mode,
                                      'file_group' : file_stats.st_gid,
                                      'file_mod_time': file_stats.st_mtime }, self.meta_db.PERMISSIONS_TABLE )
 


  def write_chunk( self, chunk_dir ):
    if not self.curr:
      return
   
    if self.encrypt:
      key = str( md5( self.curr.string ).hexdigest() )
      self.curr.encrypt( key, self.iv )
    encoding = self.curr.encode()

    if self.verbose:
      print( 'writing chunk ' + self.curr.chunk_name + ' ...' ) 

    
    chunk_name = self.storage.write_chunk( self.curr, chunk_dir ) if self.curr.used > 0 else EMPTY_CHUNK_NAME 

    for e in self.curr.meta:
      # add all meta-data not obvious at chunk-level
      e[ 'chunk_order' ] = self.chunk_count
      e[ 'chunk_id' ] = chunk_name
      e[ 'hash_key' ] = key if self.encrypt else ''
      e[ 'init_vec' ] = self.iv if self.encrypt else ''
      e[ 'encoding' ] = encoding
      self.meta_db.fill_db_from_dict( e, self.meta_db.CHUNK_TABLE )

      self.chunk_count += 1
      self.curr = Chunk( str( self.chunk_count ) + '-' + str( self.pid ) + self.CHUNK_EXTENSION ) 
      
     
  def chunk_file( self, read_handle, fpair, file_name, entry ): 
    file_handle = join( fpair.fsource, file_name )
    try:
      file = open( read_handle, 'rb' )
      file_contents = file.read()
      file.close()
    except:
      print( "ERROR: unable to open file " + read_handle + ", skipping ..." )
      return
    
    try:
      file_stats = stat( read_handle )
    except:
      print( "ERROR: unable to find statistics on " + read_handle + ", skipping ..." )
      return
    
    checksum = str( md5( file_contents ).hexdigest() )

    # if there has been no changes to the file since it was last uploaded
    if entry and entry[ 'file_checksum' ] == checksum:
      if self.verbose:
        if self.force:
				  print( file_handle + " unchanged since last chunking, however forcing upload ... " )
        else:
          print( file_handle + " unchanged since last chunking, ignoring ... " )
          return
   
    # remove any leftover pieces
    self.meta_db.delete_file_chunk_entries( file_handle ) 

    if self.verbose:
      print( "chunking file " + read_handle + " ..." )
  
 
    # record permissions
    self.__record_permissions__( file_handle, file_stats )
             
    self.meta_db.fill_db_from_dict( { 'file_path' : fpair.fsource,
                              'file_handle' : file_handle,
                              'file_checksum' : checksum }, self.meta_db.FILE_TABLE ) 
    
    file_size = file_stats.st_size
    if not self.chunk_size: 
      self.curr.concatenate( file_handle, file_contents )
      self.curr.chunk_name = file_name
      self.write_chunk( fpair.fdest )
      return 

    cnt = 0
    if file_size == 0:
      self.curr.concatenate( file_handle, file_contents )

    while file_size > 0:

      if self.curr.used >= self.chunk_size:
        self.write_chunk()

      n = self.chunk_size - self.curr.used if self.chunk_size - self.curr.used < file_size else file_size
      self.curr.concatenate( file_handle, file_contents[ cnt : ( cnt + n ) ] )
      file_size -= n
      cnt += n


  def chunk_symlink( self, read_handle, rel_path, link_name, link_dest ):
    try:
      file_stats = lstat( read_handle )
      meta = { 'link_path' : rel_path,
               'link_handle' : join( rel_path, link_name ),
               'link_dest' : link_dest }
    except:
      print( "ERROR: unable to find statistics on " + read_handle + ", skipping ..." )
      return

    if self.verbose:
      print( "chunking symlink " + read_handle + " ..." )
      print( "WARNING: chunker will not descend into " + link_dest + " ..." )

    self.meta_db.fill_db_from_dict( meta, self.meta_db.SYMLINK_TABLE )    
 

  def chunk_directory( self, read_handle, rel_handle ):
    try:
      file_stats = stat( read_handle )
      self.__record_permissions__( rel_handle, file_stats )
      meta = { 'directory_path' : rel_handle }
    except:
      print( "ERROR: unable to find statistics on " + read_handle + ", skipping ..." )
      return         
  
    if self.verbose:
      print( "chunking directory " + read_handle + " ..." )

    self.meta_db.fill_db_from_dict( meta, self.meta_db.DIRECTORY_TABLE )   

  
  def queue( self, file_name, abs_path, fpair, db_entry ):
    file_handle = join( abs_path, file_name )
    if isdir( file_handle ):
      self.__queue_dir__( file_handle, join( fpair.fsource, file_name ) )
    else:
      if islink( file_handle ):
        self.__queue_link__( file_name, file_handle, fpair )
      else:
        self.__queue_file__( file_handle, fpair, file_name, db_entry )
  
  
  def __queue_dir__( self, handle, rel_handle ):
    self.chunk_queue[ 'dir' ].append( ( handle, rel_handle ) )


  def __queue_file__( self, file_name, abs_path, fpair, entry ):
    self.chunk_queue[ 'file' ].append( ( file_name, abs_path, fpair, entry ) )


  def __queue_link__( self, file_name, file_handle, fpair ):
    self.chunk_queue[ 'link' ].append( ( file_handle, fpair.fsource, file_name, readlink( file_handle ) ) )
 
  
  def run( self ):
    self.curr = Chunk( str( self.chunk_count ) + '-' + str( self.pid ) + self.CHUNK_EXTENSION )
    last = None
    
    for handle, rel_handle in self.chunk_queue[ 'dir' ]:
      self.chunk_directory( handle, rel_handle )
  
    for file_handle, fpair, file_name, entry in self.chunk_queue[ 'file' ]:
      self.chunk_file( file_handle, fpair, file_name, entry ) 
      last = fpair.fdest
 
    if self.curr.used > 0:
      self.write_chunk( last )

    for handle, source, fname, dest in self.chunk_queue[ 'link' ]:
      self.chunk_symlink( handle, source, fname, dest )

    self.chunk_queue = []
         

class Unchunker ( Process ):

  def __init__( self, db, storage ):
    Process.__init__( self )

    # handling user flags
    self.verbose = flags[ 'verbose_flag' ]

    # database initialization
    self.meta_db = db  
    self.storage = storage

    # queueing for parallelism
    self.queue = []


  def __restore_meta_data__( self, handle, meta ):
    try:
      chmod( handle, int( meta[ 'file_permissions' ] ) )
    except:
      print( "ERROR: unable to write permissions to " + handle + " ... " )

    try:
      chown( handle, int( meta[ 'file_owner' ] ), int( meta[ 'file_group' ] ) )
    except:
      print( "ERROR: unable to change ownership of " + handle + " ... " )

    utime( handle, ( float( meta[ 'file_mod_time' ] ), float( meta[ 'file_mod_time' ] ) ) )


  def read_chunk( self, chunk_name, write_directory, object_path ):
    chunk = Chunk()
    keys, files = self.meta_db.get_chunk_entries( chunk_name, object_path )
    if chunk_name == EMPTY_CHUNK_NAME:
      chunk.string = "~"
    else:
      chunk.string = self.storage.read_chunk( chunk_name )

    
    if len( files ) >= 1:
      chunk.decode( files[ 0 ][ 5 ] )
      if files[ 0 ][ 6 ] and files[ 0 ][ 7 ]:
        chunk.decrypt( files[ 0 ][ 6 ], files[ 0 ][ 7 ] )
    else:
      print( "WARNING: was unable to retrieve file information on " + chunk_name + " ..." )
      

    current_handle = None
    for row in files:
      meta = dict( zip( keys, row ) )
      self.unchunk_file( meta[ 'file_handle' ], 
                         chunk.string[ int( meta[ 'start_in_chunk' ] ) : int( meta[ 'end_in_chunk' ] ) + 1 ], 
                         write_directory,
                         object_path )
       

  def unchunk_file( self, file_handle, file_part, write_directory, rel_path ):
    meta = self.meta_db.fill_dicts_from_db( [], { 'file_handle': file_handle }, self.meta_db.FILE_TABLE ).pop() 
    ensure_path( join( write_directory, relpath( meta[ 'file_path' ], rel_path ) ) )
     
    if self.verbose:
      print( 'unchunking ' + file_handle + ' ...' )

    write_handle = join( write_directory, relpath( file_handle, rel_path ) )
    if isfile( write_handle ):
      file = open( write_handle, 'rb' )
      file_part = file.read() + file_part
      file.close()
    
    file = open( write_handle, 'wb' )
    file.write( file_part )     
    file.close()
    self.__restore_meta_data__( write_handle, meta )


  def unchunk_symlink( self, read_handle, write_handle, link_dest ):
    if self.verbose:
      print( 'unchunking symlink ' + read_handle + ' ...' )
     
    symlink( link_dest, write_handle )   


  def unchunk_directory( self, read_handle, write_handle ):
    meta = self.meta_db.fill_dicts_from_db( [], { 'directory_path': read_handle }, self.meta_db.DIRECTORY_TABLE ).pop()

    if self.verbose:
      print( 'unchunking directory ' + read_handle + ' ...' )
   
    self.__restore_meta_data__( write_handle, meta )     
 

  def unchunk( self, write_directory, object_path, db_entry, type ):
   
    # first create all folders and directores, and add permission to files
    if type == 'file':
      self.read_chunk( db_entry, write_directory, object_path )
 
    # create all symlinks
    if type == 'link':
      link_path, link_handle, link_dest = db_entry
      link_path = relpath( link_path, object_path ) 
      self.unchunk_symlink( link_handle, join( write_directory, relpath( link_handle, object_path ) ), link_dest )

    # place permissions onto folders after everything is created
    if type == 'directory':
      directory_path = db_entry
      write_file_path = join( write_directory, relpath( directory_path, object_path ) )
      self.unchunk_directory( directory_path, write_file_path )
 

 
  def queue( self, write_dir, object_path, db_entry, type ):
    self.queue.append( ( write_dir, object_path, db_entry, type ) )


  def run( self ):
    for wdir, path, entry, type in self.queue:
      unchunk( wdir, path, entry, type ) 
