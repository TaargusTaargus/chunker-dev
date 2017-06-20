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
from utilities import drive_makedirs
from copy import deepcopy

class Client:

  def __init__( self, client, username, cdir ):
    self.client = client
    self.username = username
    self.cdir = cdir


  def get_chunk_dir( self ):
    return self.cdir

 
  def get_client( self ):
    return self.client

  
  def get_username( self ):
    return self.username



class Authorizer:
 
  APPLICATION_NAME = "Filesystem Chunker"
  AVAILABLE = [ 'box', 'drive' ]
  DRIVE_SECRET_FILE = "/home/johnson/dev/python/chunker/chunker-dev/conf/client_secret_drive.json"
  DEFAULT_CRED_DIR = join( expanduser( "~" ), ".chunker" )
  DEFAULT_CHUNK_DIR = ".chunker"
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


  def __insert_user__( self, client, cred_path, chunk_dir ):
    about = client.GetAbout()
    new_path = about[ 'user' ][ 'emailAddress' ].split( "@" )[ 0 ]
    rename( cred_path, join( self.DEFAULT_CRED_DIR, new_path ) ) 
    print( "new_path: " + new_path )
    print( "chunk_dir: " + chunk_dir )
    self.udb.add_user( about[ 'user' ][ 'emailAddress' ], new_path, chunk_dir )


  def __update_user__( self, client ):
    about = client.GetAbout()
    self.udb.update_user( about[ 'user' ][ 'emailAddress' ], about[ 'quotaBytesUsed' ], about[ 'quotaBytesTotal' ] )


  def expand( self ):
    #create working directory
    credential_path = self.DEFAULT_CRED_FILE
    store = Storage( credential_path )
    credentials = store.get()
    if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets( self.DRIVE_SECRET_FILE, self.SCOPE )
      flow.user_agent = self.APPLICATION_NAME
      #if version > (2,6)
      tools.run_flow( flow, store, tools.argparser.parse_args(args=[ '--noauth_local_webserver' ]) )
      #else: 
      #    tools.run( flow, store )
      print( 'storing credentials to ' + credential_path + " ... ")
    
    cli = self.__authorize__( credential_path )
    cdir = drive_makedirs( cli, self.DEFAULT_CHUNK_DIR ) 
    self.__insert_user__( cli, credential_path, cdir ) 


  def get_all_clients( self ):
    clients = []
    for name, path, cdir in self.udb.get_users( keys = [ 'username', 'cred_path', 'chunk_dir' ] ):
      path = join( self.DEFAULT_CRED_DIR, path )
      client = self.__authorize__( path )
      self.__update_user__( client )
      clients.append( Client( client, name, cdir ) )
    return clients

