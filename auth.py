from os import makedirs
from os.path import exists, expanduser, join
from oauth2client.file import Storage
from oauth2client import client, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from boxsdk import Client, OAuth2
from sys import version
from state import flags	
from db import UserDB
from copy import deepcopy

class Credentials:
 
  APPLICATION_NAME = "Filesystem Chunker"
  AVAILABLE = [ 'box', 'drive' ]
  DRIVE_SECRET_FILE = "/home/johnson/dev/python/chunker/chunker-dev/conf/client_secret_drive.json"
  DEFAULT_CRED_DIR = join( expanduser( "~" ), ".chunker" )
  DEFAULT_CRED_FILE = "credentials"
  DEFAULT_USER_DB = join( DEFAULT_CRED_DIR, "users.db" )
  SCOPE = "https://www.googleapis.com/auth/drive"
 
  def __init__( self, credential_file ): 
    if flags[ 'storage_mode' ] not in self.AVAILABLE:
      print( 'ERROR: invalid storage mode, availabe modes are ' +                                                                     
             ', '.join( self.AVAILABLE ) + ' ...' )                                                                                   
 
    self.udb = UserDB( self.DEFAULT_USER_DB ) 
    self.credential_path = credential_file 
    self.storage = flags[ 'storage_mode' ]

    if self.storage == 'box':                                                                                                         
      with open( credential_file, 'r' ) as cnfg:                                                                                      
        self.CLIENT_ID = cnfg.readline()
        self.CLIENT_SECRET = cnfg.readline()
        self.ACCESS_TOKEN = cnfg.readline()

      oauth2 = OAuth2( self.CLIENT_ID, self.CLIENT_SECRET, access_token = self.ACCESS_TOKEN )
      self.client = Client( oauth2 )

    elif self.storage == 'drive':
      gauth = GoogleAuth()
      gauth.LoadClientConfigFile( self.DRIVE_SECRET_FILE )
      gauth.LoadCredentialsFile( self.__get_credentials__() )
      self.client = GoogleDrive( gauth )
      self.__update_db__( self.client )
      self.udb.list_users()

  def __update_db__( self, client ):
    about = client.GetAbout()
    self.udb.update_user( about[ 'user' ][ 'emailAddress' ], about[ 'quotaBytesUsed' ], about[ 'quotaBytesTotal' ] )


  def __get_credentials__( self ):
    if self.credential_path:
      if exists( self.credential_path ):
        return self.credential_path
      else:
        print( "could not find credential file " + self.credential_path + " ... " )   
   
    credential_path = join( self.DEFAULT_CRED_DIR, self.DEFAULT_CRED_FILE )

    if not exists( self.DEFAULT_CRED_DIR ):
      makedirs( self.DEFAULT_CRED_DIR )
    if exists( credential_path ):
      return credential_path 

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
    return credential_path


  def get_client( self ):
    if self.storage == 'box':
      return deepcopy( self.client )
    else:
      return deepcopy( self.client )

