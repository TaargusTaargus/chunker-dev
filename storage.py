from StringIO import StringIO
from gzip import open as g_open
from utilities import ensure_path, persistent_try
from time import sleep
from os.path import join
from state import flags

class Storage:

  def __init__( self, clients ):
    self.storage = flags[ 'storage_mode' ]
    self.client_dict = { client.get_username(): client for client in clients }
    self.client_list = clients
    self.iterator = 0


  def __get_client__( self, username ): 
    return self.client_dict[ username ]

 
  def __next_client__( self ):
    self.iterator = self.iterator + 1
    return self.client_list[ self.iterator % len( self.client_list ) ]


  def __download_from_drive__( self, client, id ):
    return client.get_client().CreateFile( { 'id': id } ).GetContentString()


  def __upload_to_drive__( self, client, chunk ):
    file = client.get_client().CreateFile( { 'title': chunk.chunk_name, 'parents': [{ 'id': client.get_chunk_dir() }] } )
    file.SetContentString( chunk.string )
    file.Upload()
    return file[ 'id' ]


  def purge_chunks( self, entries ):
    for username, cid in entries:
      self.__get_client__( username ) \
            .get_client() \
            .CreateFile( { 'id': cid } ) \
            .Delete()


  def read_chunk( self, username, id ):
    return persistent_try( self.__download_from_drive__, [ self.__get_client__( username ), id ], 'downloading' )


  def write_chunk( self, chunk ):
    client = self.__next_client__()
    return client.get_username(), persistent_try( self.__upload_to_drive__, [ client, chunk ], 'uploading' )
