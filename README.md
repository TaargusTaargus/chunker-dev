# chunker-release
the release version of chunker

               COMMANDS: 
               chunker upload [OPTIONS...] [DIR]
               chunker download [OPTIONS...] [WRITE-DIR] [DIR]
               chunker ls-all [DB-NAME]
               chunker help [COMMAND]

              GENERAL OPTIONS:
                -s [mode]
                  determines storage location: box, drive (default)
                -m [db]
                  specify the database file to write to/read from
                -v, --verbose
                  more verbose output from chunk
              UPLOAD OPTIONS:
                -t [# of threads]
                  request threading with specified total threads spawned 
                -e, --encrypt
                  enable encryption
                -c [size]
                  chunk all files within [size] byte chunks
                -cf, --collapse
                  collapse the filesystem on upload
                -f, --force
                  force upload regardless of filesystem
     
