from auth import Authorizer
from db import ChunkDB, UserDB
from manager import DownloadManager, UploadManager
from storage import Storage
from utilities import ensure_path, format_path
from state import CHUNKER_WORK_DIR 

class Launcher:

  def __init__( self, flags ):
    self.flags = flags


  def init( self ):
    ensure_path( CHUNKER_WORK_DIR ) 
    Authorizer().expand()


  def list( self ):
    UserDB().list_users()
    ChunkDB( self.flags[ 'database_name' ] ) \
    		.list_files( self.flags[ 'work_dir' ] )


  def purge( self ):
    Storage( Authorizer().get_all_clients() ) \
      .purge_chunks(   
        ChunkDB( self.flags[ 'database_name' ] ) \
				  .purge_path( self.flags[ 'work_dir' ] )
      )


  def download( self ):
    DownloadManager( self.flags[ 'database_name' ], \
											self.flags[ 'thread_count' ] ) \
									 .download( self.flags[ 'work_dir' ] )


  def upload( self ):
    UploadManager( self.flags[ 'database_name' ], \
										self.flags[ 'thread_count' ] ) \
								 .upload( self.flags[ 'work_dir' ] )
