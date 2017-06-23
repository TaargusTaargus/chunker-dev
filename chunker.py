from auth import Authorizer
from db import ChunkDB, UserDB
from manager import DowndloadManager, UploadManager
from storage import Storage

class Launcher:

  def __init__( self, flags ):
    self.flags = flags


  def init():
    Authorizer().expand()


  def list():
    UserDB().list_users()
    ChunkDB( self.flags[ 'database_name' ] ) \
    		.list_files( self.flags[ 'work_dir' ] )


  def purger():
     
    ChunkDB( self.flags[ 'database_name' ] ) \
				.remove_related_chunks( self.flags[ 'work_dir' ] )


  def download():
    DownloadManager( self.flags[ 'database_bame' ], \
											self.flags[ 'thread_count' ] ) \
									 .download( self.flags[ 'work_dir' ] )


  def upload():
    UploadManager( self.flags[ 'database_name' ], \
										self.flags[ 'thread_count' ] ) \
								 .upload( self.flags[ 'work_dir' ] )
