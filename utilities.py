from time import sleep
from os import makedirs
from os.path import isdir
from os.path import relpath as os_relpath
from state import flags

def relpath( path1, path2 ):
  path = path1 if path2 == '' else os_relpath( path1, path2 )
  return path if path != '.' else ''


def ensure_path( path ):
  if not isdir( path ):
    makedirs( path )

def persistent_try( function, args, description ):
  count = 10
  while True:
    try:
      return function( *args )
    except Exception as e:
      if count == 0:
        print( "ERROR: hit retry limit " + description + " with " + self.storage + " ... " )
        print( "REASON: " + str( e ) )
        return None
      else:
        print( 'WARNING: encountered issue ' + description
              + ' with ' + flags[ 'storage_mode' ] + ', will retry ...' )
      sleep( 2 )

    count = count - 1
