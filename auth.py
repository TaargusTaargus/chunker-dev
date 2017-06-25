from os import makedirs, rename
from os.path import exists, expanduser, join
from oauth2client.file import Storage
from oauth2client import client, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from boxsdk import Client, OAuth2
from sys import version
from state import flags, CHUNKER_WORK_DIR
from db import UserDB
from utilities import drive_makedirs
from copy import deepcopy

APPLICATION_NAME = "chunker"
CHUNKER_SCOPE = "https://www.googleapis.com/auth/drive"
DEFAULT_CREDFILE_PATH = join( CHUNKER_WORK_DIR, "credentials" )
DEFAULT_DRIVE_CHUNKDIR = ".chunker"
DRIVE_SECRET_FILE = "/home/jhonson/Development/python/chunker-dev/conf/client_secret_drive.json"

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
 
  def __init__( self ):  
    self.udb = UserDB()  


  def __authorize__( self, cred_path ):
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile( DRIVE_SECRET_FILE )
    gauth.LoadCredentialsFile( cred_path )
    return GoogleDrive( gauth )


  def __insert_user__( self, client, cred_path, chunk_dir ):
    about = client.GetAbout()
    new_path = about[ 'user' ][ 'emailAddress' ].split( "@" )[ 0 ]
    rename( cred_path, join( CHUNKER_WORK_DIR, new_path ) ) 
    self.udb.add_user( about[ 'user' ][ 'emailAddress' ], new_path, chunk_dir )


  def __update_user__( self, client ):
    about = client.GetAbout()
    self.udb.update_user( about[ 'user' ][ 'emailAddress' ], about[ 'quotaBytesUsed' ], about[ 'quotaBytesTotal' ] )


  def expand( self ):
    #create working directory
    credential_path = DEFAULT_CREDFILE_PATH
    store = Storage( credential_path )
    credentials = store.get()
    if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets( DRIVE_SECRET_FILE, CHUNKER_SCOPE )
      flow.user_agent = APPLICATION_NAME
      tools.run_flow( flow, store, tools.argparser.parse_args( args = [ '--noauth_local_webserver' ] ) )
      print( 'storing credentials to ' + credential_path + " ... ")
    
    cli = self.__authorize__( credential_path )
    cdir = drive_makedirs( cli, DEFAULT_DRIVE_CHUNKDIR ) 
    self.__insert_user__( cli, credential_path, cdir ) 


  def get_all_clients( self ):
    clients = []
    for name, path, cdir in self.udb.get_users( keys = [ 'username', 'cred_path', 'chunk_dir' ] ):
      path = join( CHUNKER_WORK_DIR, path )
      client = self.__authorize__( path )
      self.__update_user__( client )
      clients.append( Client( client, name, cdir ) )
    return clients

