from sqlite3 import connect
from os.path import sep
 
class ChunkDB:

# database table names
  CHUNK_TABLE = "chunks"
  FILE_TABLE = "files"
  DIRECTORY_TABLE = "directories"
  SYMLINK_TABLE = "links"
  PERMISSIONS_TABLE = "permissions"


  def __init__( self, db_name=":memory:" ):
    self.db_name = db_name
    self.meta_db = connect( db_name, check_same_thread=False )
    self.cursor = self.meta_db.cursor()
    tables = [ t for t, in self.cursor.execute( "SELECT name FROM sqlite_master WHERE type='table'" ).fetchall() ]
    self.update = bool( len( tables ) )

    if self.PERMISSIONS_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.PERMISSIONS_TABLE + ''' ( file_handle text, file_owner text,
                                                                            file_permissions text, file_group text,
                                                                            file_mod_time text ) ''' )
                                                                      

    if self.CHUNK_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.CHUNK_TABLE + ''' ( chunk_order int, chunk_id text,
                                                                      file_handle text, start_in_chunk text,
                                                                      end_in_chunk text, encoding text,
                                                                      hash_key text, init_vec text )''' )

    if self.FILE_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.FILE_TABLE + ''' (  file_path text, file_handle text,
                                                                      file_checksum text, UNIQUE( file_handle ) )''' )

    if self.DIRECTORY_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.DIRECTORY_TABLE
                             + ''' ( directory_path text, UNIQUE( directory_path ) ) ''' )

    if self.SYMLINK_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.SYMLINK_TABLE
                            + ''' ( link_path text, link_handle text, link_dest text,
                                    UNIQUE( link_handle ) ) ''' )

    try:
      self.meta_db.commit()
    except:
      print( "ERROR: was unable to create database " + db_name + " ..." ) 


  def __del__( self ):
    self.meta_db.close() 


  def copy_other_db( self, chunkdb ):
    for table in self.PERMISSIONS_TABLE, self.CHUNK_TABLE, self.FILE_TABLE, self.SYMLINK_TABLE, self.DIRECTORY_TABLE:
      for entry in chunkdb.fill_dicts_from_db( [ '*' ], {}, table ):
        self.fill_db_from_dict( entry, table )


  def fill_db_from_dict( self, dict, table_name ):
    placeholders = ', '.join( [ '?' ] * len( dict ) )
    columns = ', '.join( dict.keys() )
    sql = "REPLACE INTO %s ( %s ) VALUES ( %s )" % ( table_name, columns, placeholders ) 
    self.cursor.execute( sql, dict.values() )
    self.meta_db.commit()  

  def fill_dicts_from_db( self, keys, where, table_name, like=False, entries=None ):
    results = self.get_objects_from_db( keys, where, table_name, like )
    keys = [ key[ 0 ] for key in self.cursor.description ]
    return [ dict( zip( keys, result ) ) for result in ( results[ :entries] if entries else results ) ] 


  def get_objects_from_db( self, keys, where, table_name, like ): 
    query_keys = ', '.join( keys ) if len( keys ) > 0 else '*' 
    if where:
      where_clause = ' WHERE ' + ' AND '.join( ( '%s' + ( ' LIKE ' if like else '=' ) + "'%s"  + ( "%%'" if like else "'" ) ) % e for e in zip( where.keys(), where.values() ) )  
    else:
      where_clause = ''
    return self.cursor.execute( 'SELECT %s FROM %s %s' % ( query_keys, table_name, where_clause ) ).fetchall()

 
  def delete_file_chunk_entries( self, file_handle ):
    self.cursor.execute( 'DELETE FROM ' + self.CHUNK_TABLE + " WHERE file_handle='" + file_handle + "'" )
    self.meta_db.commit()


  def get_chunk_file_entries( self, chunk_id ):
    entries = self.cursor.execute( "SELECT ct.start_in_chunk, ct.end_in_chunk, pt.* FROM " + self.CHUNK_TABLE
                                   + " ct INNER JOIN " + self.PERMISSIONS_TABLE 
                                   + " pt ON ct.file_handle = pt.file_handle"
                                   + " WHERE ct.chunk_id = '" + chunk_id + "'" ).fetchall() 
    return [ key[ 0 ] for key in self.cursor.description ], entries


  def get_related_chunks( self, file_path='' ):
    return self.cursor.execute( 'SELECT DISTINCT chunk_id FROM ' + self.CHUNK_TABLE 
                                + " WHERE file_handle LIKE '" + file_path + "%'"
                                + " ORDER BY chunk_order" ).fetchall()  


  def get_related_symlinks( self, cols=[ 'link_path', 'link_handle', 'link_dest' ], where={ 'link_path': '' }, like=True ):
    return self.get_objects_from_db( cols, where, self.SYMLINK_TABLE, like )


  def get_related_directories( self, cols=[ 'directory_path' ], where={ 'directory_path': '' }, like=True ):
    return self.get_objects_from_db( cols, where, self.DIRECTORY_TABLE, like )


  def get_related_files( self, cols=[ 'file_handle' ], where={ 'file_path': '' }, like=True ):
    return self.get_objects_from_db( cols, where, self.FILE_TABLE, like )


  def list_all_files( self ):
    print( "FILES:" )
    for handle, in self.get_related_files( ):
      print( sep + handle )

    print( "SYMLINKS:" )
    for path, handle, dest in self.get_related_symlinks( ):
      print( sep + handle + " -> " + dest )

    print( "DIRECTORIES:" )
    for directory, in self.get_related_directories( ):
      print( sep + directory )
