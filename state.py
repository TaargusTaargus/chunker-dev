from os.path import join, expanduser

flags = { 
	'verbose_flag': None,
	'collapse_flag': None,
	'force_flag': None,
	'encrypt_flag': None,
	'chunk_size': None,
	'storage_mode': 'drive'
}

CHUNKER_WORK_DIR_NAME = ".chunker"
CHUNKER_WORK_DIR = join( expanduser( "~" ), CHUNKER_WORK_DIR_NAME )
