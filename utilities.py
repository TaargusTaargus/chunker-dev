from time import sleep
from os import makedirs, sep
from os.path import isdir
from os.path import relpath as os_relpath
from state import flags

def drive_makedirs( client, path ):
  abs_path = format_path( path )[ :-1 ]
  root = "root"
  for part in abs_path.split( sep ):
    flag = False
    for e in client.ListFile( { 'q': "'" + root + "' in parents" } ).GetList():
      if e[ 'title' ] == part:
        flag = True
        root = e[ 'id' ]
    if not flag:
      file = client.CreateFile( { 'title': part, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [ { 'id': root } ] } )
      file.Upload()
      root = file[ 'id' ]
  return root 


def lsplit( list, key, val ):
  w, wo = [], []
  while list:
    el = list.pop()
    if( el[ key ] == val ):
      w.append( el )
    else:
      wo.append( el )
  return w, wo


def relpath( path1, path2 ):
  path = path1 if path2 == '' else os_relpath( path1, path2 )
  return path if path != '.' else ''


def ensure_path( path ):
  if not isdir( path ):
    makedirs( path )


# formats a path to: path/ (no slash at beginning and slash at end)
def format_path( path ):
  if len( path ):

    if path[ 0 ] == sep:
      path = path[ 1: ]
    
    if len( path ) and path[ -1 ] != sep:
      path = path + sep
    
  return path


def persistent_try( function, args, description ):
  count = 10
  while True:
    try:
      return function( *args )
    except Exception as e:
      if count == 0:
        print( "ERROR: hit retry limit " + description + " ... " )
        print( "REASON: " + str( e ) )
        return None
      else:
        print( 'WARNING: encountered issue ' + description
              + ' with ' + flags[ 'storage_mode' ] + ', will retry ...' )
      sleep( 2 )

    count = count - 1
