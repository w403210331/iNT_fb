#!/usr/bin/env python2.6
# coding: utf-8

import os
import os.path
import sys
import fcntl
from stat import ST_DEV, ST_INO
import logging
import logging.handlers
import traceback
import time

from amazon.settings import APP_LOG_NAME, APP_LOG_DIR

DEFAULT_FORMAT = "[%(asctime)s,%(process)d-%(thread)d,%(filename)s,%(lineno)d,%(levelname)s] %(message)s"

DEFAULT_DATETIME_FORMAT = '%m%d-%H:%M:%S'

stdHandlerSet = set()

APPNAME = APP_LOG_NAME
LOG_FILENAME = os.path.join( APP_LOG_DIR, APPNAME + '.out' )

# an util to prevent evaluating arguments of logging statement
def iflog( lvl ): return logger.getEffectiveLevel() <= lvl

logging.NOTIFIED = 25
logging.addLevelName( logging.NOTIFIED, 'NOTIFIED' )

class ctimeFormatter( logging.Formatter ):

    def formatTime( self, record, datefmt=None ):
        return str(int(time.time()))

def reset_defaults( appname = None ):

    global APPNAME
    global LOG_FILENAME

    APPNAME = APP_LOG_NAME
    LOG_FILENAME = os.path.join( APP_LOG_DIR, APPNAME + '.out' )

    return

class S3LogHandler( logging.handlers.WatchedFileHandler ):

    # let fd close when exec()
    def _open( self ):
        _stream = logging.handlers.WatchedFileHandler._open( self )
        fd = _stream.fileno()

        r = fcntl.fcntl( fd, fcntl.F_GETFD, 0 )
        r = fcntl.fcntl( fd, fcntl.F_SETFD, r | fcntl.FD_CLOEXEC )
        return _stream


    def emit(self, record):

        try:
            stat = os.stat(self.baseFilename)
            changed = (stat[ST_DEV] != self.dev) or (stat[ST_INO] != self.ino)
        except OSError, e:
            stat = None
            changed = 1

        if changed and self.stream is not None:
            self.stream.flush()
            self.stream.close()
            self.stream = self._open()
            if stat is None:
                stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]
        logging.FileHandler.emit(self, record)

def createlogger ( appname = None, level = logging.DEBUG,
                   format = None, formatter = logging.Formatter ):

    if appname != None :
        filename = os.path.join( APP_LOG_DIR, appname + '.out' )
    else:
        filename = LOG_FILENAME

    logname = appname or 'genlogger'

    logger = logging.getLogger( logname )
    logger.setLevel( level )

    handler = S3LogHandler( filename )

    format = format or DEFAULT_FORMAT

    _formatter = formatter( format )

    handler.setFormatter(_formatter)

    logger.handlers = []
    logger.addHandler( handler )

    return logger

def add_std_handler( logger, stream = None, format = None, datefmt = None ):

    stream = stream or sys.stdout

    if stream in stdHandlerSet:
        return logger

    stdHandlerSet.add( stream )

    stdhandler = logging.StreamHandler( stream )
    stdhandler.setFormatter(
            logging.Formatter( format or DEFAULT_FORMAT,
                               datefmt ) )

    logger.addHandler( stdhandler )

    return logger

if os.name != 'nt' :
    logger = createlogger()
else :
    logger = None

def trace_error( e ):
    logger.error( traceback.format_exc() )
    logger.error( repr( e ) )


def stack_list( offset=0 ):
    offset += 1 # count this function as 1

    # list of ( filename, line-nr, in-what-function, statement )
    x = traceback.extract_stack()
    return x[ : -offset ]

def format_stack( stacks ):
    stacks = [ ( os.path.basename(x[0]), ) + x[1:]
               for x in stacks ]
    x = [ "{0}:{1} in {2} {3}".format( *xx ) for xx in stacks ]
    x = ' --- '.join( x )
    return x


def stack_str( offset=0 ):
    offset += 1 # count this function as 1
    return format_stack( stack_list( offset ) )


def deprecate( lgr=None, mes='' ):
    lgr = lgr or logger

    if mes != '':
        mes = mes + ' '
    lgr.warn( mes + "Deprecated: " + stack_str( offset=1 ) )

def setdefaultlogger():

    global logger

    logger = createlogger()

    logger.debug( '  genlog Reopened' )
