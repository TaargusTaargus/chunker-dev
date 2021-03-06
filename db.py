from sqlite3 import connect
from os.path import sep, join
from state import CHUNKER_WORK_DIR

CHUNKER_CHUNKDB_NAME = "chunks.db"
CHUNKER_CHUNKDB_PATH = join( CHUNKER_WORK_DIR, CHUNKER_CHUNKDB_NAME ) 
CHUNKER_USERDB_NAME = "users.db"
CHUNKER_USERDB_PATH = join( CHUNKER_WORK_DIR, CHUNKER_USERDB_NAME )

class BaseDB:

  def __init__( self, db_name ):
    self.db_name = db_name
    self.db = connect( db_name, check_same_thread=False )
    self.cursor = self.db.cursor()


  def __del__( self ):
    self.db.close() 


  def fill_db_from_dict( self, dict, table_name ):
    placeholders = ', '.join( [ '?' ] * len( dict ) )
    columns = ', '.join( dict.keys() )
    sql = "REPLACE INTO %s ( %s ) VALUES ( %s )" % ( table_name, columns, placeholders ) 
    self.cursor.execute( sql, dict.values() )
    self.db.commit()  


  def fill_dicts_from_db( self, keys, where, table_name, like=False, entries=None, distinct=None ):
    results = self.get_objects_from_db( keys, where, table_name, like, distinct=distinct )
    keys = [ key[ 0 ] for key in self.cursor.description ]
    return [ dict( zip( keys, result ) ) for result in ( results[ :entries] if entries else results ) ] 


  def get_objects_from_db( self, keys, where, table_name, like, distinct=None ): 
    query_keys = ', '.join( keys ) if len( keys ) > 0 else '*' 
    if where:
      where_clause = ' WHERE ' + ' AND '.join( ( '%s' + ( ' LIKE ' if like else '=' ) + "'%s"  + ( "%%'" if like else "'" ) ) % e for e in zip( where.keys(), where.values() ) )  
    else:
      where_clause = ''
    
    if distinct:
      distinct_clause = "DISTINCT"
    else:
      distinct_clause = ""

    #print( "select %s %s FROM %s %s" % ( distinct_clause, query_keys, table_name, where_clause ) )
    return self.cursor.execute( 'SELECT %s %s FROM %s %s' % ( distinct_clause, query_keys, table_name, where_clause ) ).fetchall()



class UserDB( BaseDB ):

  USER_TABLE = "users"
  GiB_DIVISOR = 1073741824

  def __init__( self ):
    BaseDB.__init__( self, CHUNKER_USERDB_PATH )
    tables = [ t for t, in self.cursor.execute( "SELECT name FROM sqlite_master WHERE type='table'" ).fetchall() ]        

    if self.USER_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.USER_TABLE + " ( username text, cred_path text, \
                                                                                 chunk_dir text, UNIQUE( username ) ) " )
    try:
      self.db.commit()
    except:
      print( "ERROR: was unable to create database " + db_name + " ..." )


  def add_user( self, username, cred_path, chunk_dir ):
    self.cursor.execute( "INSERT INTO " + self.USER_TABLE + " ( username, cred_path, chunk_dir ) VALUES ( '" + username + "', '"
                         + cred_path + "', '" + chunk_dir + "' )" )
    self.db.commit()


  def update_user( self, username, used_bytes, quota_bytes ):
    self.cursor.execute( "UPDATE " + self.USER_TABLE + " SET "
                          + "quota_bytes=" + str( quota_bytes ) + ", quota_gib=" + str( float ( int( quota_bytes ) /self.GiB_DIVISOR ) ) + "," 
                          + " used_bytes=" + str( used_bytes ) + ", used_gib=" + str( float( int( used_bytes ) / self.GiB_DIVISOR ) )
                          + " WHERE username='" + username + "'" )
    self.db.commit()


  def get_users( self, keys=[ 'username', 'quota_gib', 'used_gib' ], where=None ):
    return self.get_objects_from_db( keys, where, self.USER_TABLE, False )

 
  def list_user_info( self ):
    total_quota, total_used = 0, 0
    userinfo = self.get_users()
    if len( userinfo ) > 0:
      print( "LINKED ACCOUNT:" )
      for username, quota_gib, used_gib in userinfo:
        quota_gib = quota_gib if quota_gib else 0
        used_gib = used_gib if used_gib else 0
        print( username + ": " + str( used_gib ) + " GB of " + str( quota_gib  ) + " GB used." )
        total_quota = total_quota + quota_gib
        total_used = total_used + used_gib
      print( "\nTotal Used Space: " + str( total_used ) + " GB of " + str( total_quota ) + " GB used." )
    else:
      print( "You have not linked any accounts to chunker." )



class ChunkDB( BaseDB ):

# database table names
  CHUNK_TABLE = "chunks"
  FILE_TABLE = "files"
  DIRECTORY_TABLE = "directories"
  SYMLINK_TABLE = "links"
  PERMISSIONS_TABLE = "permissions"


  def __init__( self, db_name=":memory:" ):
    BaseDB.__init__( self, db_name if db_name else CHUNKER_CHUNKDB_PATH )
    tables = [ t for t, in self.cursor.execute( "SELECT name FROM sqlite_master WHERE type='table'" ).fetchall() ]

    if self.PERMISSIONS_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.PERMISSIONS_TABLE + ''' ( file_handle text, file_owner text,
                                                                            file_permissions text, file_group text,
                                                                            file_mod_time text ) ''' )
                                                                      

    if self.CHUNK_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.CHUNK_TABLE + ''' ( pid int, corder int,
                                                                      username text, chunk_id text,
                                                                      start_in_chunk text, end_in_chunk text,
                                                                      file_handle text, encoding text,
                                                                      hash_key text, init_vec text )''' )

    if self.FILE_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.FILE_TABLE + ''' (  file_path text, file_handle text,
                                                                      UNIQUE( file_handle ) )''' )

    if self.DIRECTORY_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.DIRECTORY_TABLE
                             + ''' ( directory_handle text, UNIQUE( directory_handle ) ) ''' )

    if self.SYMLINK_TABLE not in tables:
      self.cursor.execute( "CREATE TABLE " + self.SYMLINK_TABLE
                            + ''' ( link_path text, link_handle text, link_dest text,
                                    UNIQUE( link_handle ) ) ''' )

    try:
      self.db.commit()
    except:
      print( "ERROR: was unable to create database " + db_name + " ..." ) 



  def copy_other_db( self, chunkdb ):
    for table in self.PERMISSIONS_TABLE, self.CHUNK_TABLE, self.FILE_TABLE, self.SYMLINK_TABLE, self.DIRECTORY_TABLE:
      for entry in chunkdb.fill_dicts_from_db( [ '*' ], {}, table ):
        self.fill_db_from_dict( entry, table )

 
  def delete_file_chunk_entries( self, file_handle ):
    self.cursor.execute( 'DELETE FROM ' + self.CHUNK_TABLE + " WHERE file_handle='" + file_handle + "'" )
    self.db.commit()


  def get_chunk_file_entries( self, chunk_id ):
    entries = self.cursor.execute( "SELECT ct.start_in_chunk, ct.end_in_chunk, pt.* FROM " + self.CHUNK_TABLE
                                   + " ct INNER JOIN " + self.PERMISSIONS_TABLE 
                                   + " pt ON ct.file_handle = pt.file_handle"
                                   + " WHERE ct.chunk_id = '" + chunk_id + "'" ).fetchall() 
    return [ key[ 0 ] for key in self.cursor.description ], entries


  def get_directory_permissions( self, file_handle='' ):
    entries = self.cursor.execute( "SELECT pt.* FROM " + self.DIRECTORY_TABLE
                                   + " dt INNER JOIN " + self.PERMISSIONS_TABLE
                                   + " pt ON dt.directory_handle = pt.file_handle"
																	 + " WHERE dt.directory_handle LIKE '" + file_handle + "%%'"  ).fetchall()
    return [ key[ 0 ] for key in self.cursor.description ], entries 


  def get_related_chunks( self, file_path='' ):
    return self.cursor.execute( 'SELECT DISTINCT pid, chunk_id FROM ' + self.CHUNK_TABLE 
                                + " WHERE file_handle LIKE '" + file_path + "%'"
                                + " ORDER BY corder" ).fetchall()  


  def get_related_symlinks( self, cols=[ 'link_path', 'link_handle', 'link_dest' ], where={ 'link_path': '' }, like=True ): 
    return self.fill_dicts_from_db( cols, where, self.SYMLINK_TABLE, like )


  def get_related_directories( self, cols=[ 'directory_handle' ], where={ 'directory_handle': '' }, like=True ):
    return self.fill_dicts_from_db( cols, where, self.DIRECTORY_TABLE, like )


  def get_related_files( self, cols=[ 'file_handle' ], where={ 'file_path': '' }, like=True ):
    return self.fill_dicts_from_db( cols, where, self.FILE_TABLE, like )


  def purge_path( self, file_path='' ):
    entries = self.cursor.execute( "SELECT DISTINCT username, chunk_id FROM " + self.CHUNK_TABLE
																		+ " WHERE file_handle LIKE '" + file_path + "%%'" ).fetchall()
    self.cursor.execute( "DELETE FROM " + self.CHUNK_TABLE + " WHERE file_handle LIKE '" + file_path + "%%'" )
    self.cursor.execute( "DELETE FROM " + self.FILE_TABLE + " WHERE file_handle LIKE '" + file_path + "%%'" )
    self.cursor.execute( "DELETE FROM " + self.DIRECTORY_TABLE + " WHERE directory_handle LIKE '" + file_path + "%%'" )
    self.cursor.execute( "DELETE FROM " + self.SYMLINK_TABLE + " WHERE link_path LIKE '" + file_path + "%%'" )
    self.cursor.execute( "DELETE FROM " + self.PERMISSIONS_TABLE + " WHERE file_handle LIKE '" + file_path + "%%'" )
    self.db.commit()
    return entries


  def list_files( self, path ):
    print( "FILES:" )
    for entry in self.get_related_files( where = { 'file_path': path } ):
      print( sep + entry[ 'file_handle' ] )

    print( "SYMLINKS:" )
    for entry in self.get_related_symlinks( where = { 'link_path': path } ):
      print( sep + entry[ 'link_handle' ] + " -> " + entry[ 'link_dest' ] )

    print( "DIRECTORIES:" )
    for entry in self.get_related_directories( where = { 'directory_handle': path } ):
      print( sep + entry[ 'directory_handle' ] )



