#!/usr/bin/env python2.6
# coding: utf-8

import os
if os.name != 'nt' : # can be runned in windows for autodoc
    import fcntl
else :
    fcntl = None


class FileLockError( IOError ) : pass


def open_lock_file( filename, block = False, returnPID = False ):

    # NOTE: open() truncates the file by default if 'w' is in flags.
    #       Use os.open which does not truncate file  unless os.O_TRUNC
    #       specified.
    fd = os.open( filename, os.O_RDWR | os.O_CREAT )

    try:
        flag = fcntl.LOCK_EX if block \
                else fcntl.LOCK_EX | fcntl.LOCK_NB

        fcntl.lockf( fd, flag )

        if returnPID:
            return fd
        else:
            return os.fdopen( fd, 'w+r' )

    except IOError as e:
        os.close( fd )
        if e[0] == 11:
            # errno is 11 means that lock is occupied by other process
            raise FileLockError( filename )

def read_file( fn ):
    with open( fn, 'r' ) as f:
        return f.read()

escape = lambda v : v.encode('utf8') if type(v) == type(u'') else v
unescape = lambda v : v.decode('utf8') if type(v) == type('') else v

