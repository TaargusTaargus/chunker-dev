from os import makedirs, rename
from os.path import exists, expanduser, join
from oauth2client.file import Storage
from oauth2client import client, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from boxsdk import Client, OAuth2
from sys import version
from state import flags	
from db import UserDB

class Credentials:
 
  APPLICATION_NAME = "Filesystem Chunker"
  AVAILABLE = [ 'box', 'drive' ]
  DRIVE_SECRET_FILE = "/home/johnson/dev/python/chunker/chunker-dev/conf/client_secret_drive.json"
  DEFAULT_CRED_DIR = join( expanduser( "~" ), ".chunker" )
  DEFAULT_CRED_FILE = join( DEFAULT_CRED_DIR, "credentials" )
  DEFAULT_USER_DB = join( DEFAULT_CRED_DIR, "users.db" )
  SCOPE = "https://www.googleapis.com/auth/drive"
 
  def __init__( self ):  
    self.udb = UserDB( self.DEFAULT_USER_DB )  


  def __authorize__( self, cred_path ):
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile( self.DRIVE_SECRET_FILE )
    gauth.LoadCredentialsFile( cred_path )
    return GoogleDrive( gauth )


  def __insert_user__( self, client, cred_path ):
    about = client.GetAbout()
    new_path = about[ 'user' ][ 'emailAdress' ].split( "@" )[ 0 ]
    rename( cred_path, join( DEFAULT_CRED_DIR, new_path ) ) 
    self.udb.add_user( about[ 'user' ][ 'emailAdress' ], new_path )


  def __update_user__( self, client, cred_path ):
    about = client.GetAbout()
    self.udb.update_user( about[ 'user' ][ 'emailAddress' ], about[ 'quotaBytesUsed' ], about[ 'quotaBytesTotal' ] )


  def expand( self ):
    #create working directory
    store = Storage( self.DEFAULT_CRED_FILE )
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets( self.DRIVE_SECRET_FILE, self.SCOPE )
        flow.user_agent = self.APPLICATION_NAME
        #if version > (2,6)
        tools.run_flow( flow, store, tools.argparser.parse_args(args=[ '--noauth_local_webserver' ]) )
        #else: 
        #    tools.run( flow, store )
        print( 'storing credentials to ' + credential_path + " ... ")
    
    client = self.__authorize__( credential_path )
    self.__insert_user__( client, credential_path ) 


  def get_clients( self ):
    clients = []
    for path in self.udb.get_credetial_paths(): 
      client = self.__authorize__( path )
      self.__update_user__( client, path )
      clients.append( client )
    return clients

