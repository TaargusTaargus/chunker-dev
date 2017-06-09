from multiprocessing import Process, Queue
from os.path import join, abspath, isfile, isdir, relpath, normpath, basename
from os import walk, remove
from chunkdb import ChunkDB
from storage import Storage
from chunk import Chunker, Unchunker
from state import flags
from fs import Filesystem
from utilities import dwalk, ensure_path

class Manager( object ):

  def __init__( self, total_procs ):
    self.proc_list = [ None ] * total_procs
    self.total = total_procs
    self.counter = 0 
    for np in range( total_procs ):
      self.proc_list[ np ] = self.init_proc( np )

  def init_proc( self, proc_num ):
    return None

  def wait( self ):
    return None

  def run( self ):
    for proc in self.proc_list:
      proc.start()
    self.wait()



class UploadManager( Manager ):
  
  def __init__( self, credentials, db_name, total_procs=1 ):
    self.cred = credentials
    self.db = ChunkDB( db_name )
    self.fs = None
    Manager.__init__( self, total_procs )

  def init_proc( self, np ):
    p_db = ChunkDB( self.db.db_name + str( np ) )
    storage = Storage( self.cred.get_client() )
    return Chunker( p_db, storage )
   
  def __load__( self, file_name, abs_path, fpair ):
    try:
      entry = self.db.fill_dicts_from_db( [ '*' ], { "file_handle": join( fpair.fsource, file_name ) }, ChunkDB.FILE_TABLE, entries=1 ).pop()
    except:
      entry = None
    self.proc_list[ self.counter ].queue( file_name, abs_path, fpair, entry )
    self.counter = ( self.counter + 1 ) % self.total
 
  def wait( self ):
    while len( self.proc_list ):
      proc = self.proc_list.pop( 0 )
      if not proc.is_alive():
        self.db.copy_other_db( proc.meta_db )
        remove( proc.meta_db.db_name )
      else:
        self.proc_list.append( proc )

  def upload( self, read_path ):
    #find all files within a directory, ignoring any existing chunk or metadata files
    all_files = []
    self.fs = Filesystem( self.cred.get_client(), basename( normpath( read_path ) ) )
    read_path = abspath( read_path )

    if isfile( read_path ):
      print( "ERROR: will only operate on directories ..." )
      return
    elif not isdir( read_path ):
      print( "ERROR: " + read_path + " does not exist ..." )
      return
    else:
      for root, dirs, files in walk( read_path, topdown=False, followlinks=False ):
        rel = relpath( root, read_path )
        rel = rel if rel[ 0 ] != '.' or len( rel ) > 1 else rel[ 1: ]
        
        print( "root: " + root )
  
        print( "rel: " + rel )
       
      
        if not flags[ 'collapse_flag' ] and rel:
          self.fs.mkdir( rel )
          for dir in dirs:
            self.__load__( dir, root, self.fs.get_filepair( rel ) )

        for file in files:
          self.__load__( file, root, self.fs.get_filepair( rel ) )

    self.run() 


class DownloadManager( Manager ):
  
  def __init__( self, credentials, db_name=None, total_procs=1 ):
    self.cred = credentials
    self.db = ChunkDB( db_name ) if db_name else None
    self.fs = None
    Manager.__init__( self, total_procs )


  def init_proc( self, np ):
    storage = Storage( self.cred.get_client() )
    return Unchunker( self.db, storage )

   
  def __load__( self, file_name, abs_path, fpair ):
    try:
      entry = self.db.fill_dicts_from_db( [ '*' ], { "file_handle": join( fpair.fsource, file_name ) }, ChunkDB.FILE_TABLE, entries=1 ).pop()
    except:
      entry = None
    self.proc_list[ self.counter ].to_chunk( file_name, abs_path, fpair, entry )
    self.counter = ( self.counter + 1 ) % self.total

 
  def wait( self ):
    while len( self.proc_list ):
      proc = self.proc_list.pop( 0 )
      if not proc.is_alive():
        proc.meta_db.list_all_files()
        self.db.copy_other_db( proc.meta_db )
        remove( proc.meta_db.db_name )
      else:
        self.proc_list.append( proc )

  def download( self, read_path ):
    #find all files within a directory, ignoring any existing chunk or metadata files
    all_files = []
    self.fs = Filesystem( self.cred.get_client(), basename( normpath( read_path ) ) )
    read_path = abspath( read_path )
    ensure_path( read_path )

		### filesystem only handles remote now
    ### download does not write to database     
    
    for path, id, files, dirs in dwalk( self.cred.get_client(), self.fs.get_filepair().fdest ):
      if not flags[ 'collapse_flag' ] and path:
        ensure_path( join( read_path, path ) )
   
      print( "root: " + path ) 
      print( "files:" )
      print( [ e[ 'title' ] for e in files ] )
      print( "dirs:" )
      print( [ e[ 'title' ] for e in dirs ] )


