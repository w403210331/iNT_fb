
from scrapy import log

class Logger( object ):

    DEBUG    = log.DEBUG
    INFO     = log.INFO
    WARNING  = log.WARNING
    CRITICAL = log.CRITICAL
    ERROR    = log.ERROR

    def __init__( self ):
        self.logger = log

    def msg( self, msg, level = log.INFO ):
        self.logger.msg( msg, level = level )

    def debug( self, msg ):
        self.logger.msg( msg, level = log.DEBUG )

    def info( self, msg ):
        self.logger.msg( msg, level = log.INFO )

    def warning( self, msg ):
        self.logger.msg( msg, level = log.WARNING )
    warn = warning

    def critical( self, msg ):
        self.logger.msg( msg, level = log.CRITICAL )

    def error( self, msg ):
        self.logger.msg( msg, level = log.ERROR )

logger = Logger()
