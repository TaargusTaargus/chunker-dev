from StringIO import StringIO
from gzip import open as g_open
from utilities import ensure_path, persistent_try
from time import sleep
from os import makedirs
from os.path import join
from state import flags


class FilePair:

  def __init__( self, source, dest ):
    self.fsource = source
    self.fdest = dest


class Filesystem:

  def __init__( self, client, root ):
    self.storage = flags[ 'storage_mode' ]
    self.client = client
    self.root = root
    self.dirs = { self.root : self.__mkdir__( root ) }


  def __box_mkdir__( self, abs_pth ):
    abs_pth = abs_pth[ 1: ] if abs_pth[ 0 ] == '/' else abs_pth
    abs_pth = abs_pth[ :-1 ] if abs_pth[ -1 ] == '/' else abs_pth
    root = "0"
    for rel_path in abs_pth.split( "/" ):
      flag = False
      for e in self.client.folder( root ).get_items( 10000 ):
        if e.name == rel_path:
          flag = True
          root = e.id
      if not flag:
        print( "ERROR: was unable to find box directory " + rel_path + "..." )
    return root


  def __drive_mkdir__( self, abs_pth ):
    abs_pth = abs_pth[ 1: ] if abs_pth[ 0 ] == '/' else abs_pth
    abs_pth = abs_pth[ :-1 ] if abs_pth[ -1 ] == '/' else abs_pth
    root = "root"
    for rel_path in abs_pth.split( "/" ):
      flag = False;
      for e in self.client.ListFile({'q': "'" + root + "' in parents"}).GetList():
        if e[ 'title' ] == rel_path:
          flag = True
          root = e[ 'id' ]
      if not flag:
        print( "WARNING: was unable to find drive directory " + rel_path + ", creating new ..." )
        file = self.client.CreateFile( { 'title': rel_path, 'mimeType': 'application/vnd.google-apps.folder',
                              'parents': [ { 'id': root } ] } )
        file.Upload()
        root = file[ 'id' ]
    return root		

  def __local_mkdir__( self, abs_path ):
    makedirs( abs_path )
    return abs_path


  def __mkdir__( self, folder_path ):
    if self.storage == 'box':
      return persistent_try( self.__box_mkdir__, [ folder_path ], 'resolving folder' )
    elif self.storage == 'drive':
      return persistent_try( self.__drive_mkdir__, [ folder_path ], 'resolving folder' )
    elif self.storage == 'local':
      return self.__local_mkdir__( folder_path )


  def mkdir( self, directory ):
    if directory not in self.dirs:
      self.dirs[ directory ] = self.__mkdir__( join( self.root, directory ) )

  def get_file_pair( self, key ):
    try: 
      return FilePair( key, self.dirs[ key ] )
    except:
      return FilePair( key, self.dirs[ self.root ] )
