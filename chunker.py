from auth import Authorizer
from db import ChunkDB, UserDB
from manager import DownloadManager, UploadManager
from storage import Storage
from utilities import format_path

class Launcher:

  def __init__( self, flags ):
    self.flags = flags


  def init( self ):
    Authorizer().expand()


  def list( self ):
    UserDB().list_users()
    ChunkDB( self.flags[ 'database_name' ] ) \
    		.list_files( self.flags[ 'work_dir' ] )


  def purge( self ):
    Storage( Authorizer().get_all_clients() ) \
      .purge_chunks(   
        ChunkDB( self.flags[ 'database_name' ] ) \
				  .remove_related_chunks( self.flags[ 'work_dir' ] )
      )


  def download( self ):
    DownloadManager( self.flags[ 'database_name' ], \
											self.flags[ 'thread_count' ] ) \
									 .download( self.flags[ 'work_dir' ] )


  def upload( self ):
    UploadManager( self.flags[ 'database_name' ], \
										self.flags[ 'thread_count' ] ) \
								 .upload( self.flags[ 'work_dir' ] )
