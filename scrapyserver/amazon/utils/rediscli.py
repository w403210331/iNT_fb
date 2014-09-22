#!/usr/bin/env python2.6
# coding: utf-8
'''
Author : Slasher ( mcq.sejust@gmail.com )
'''

import os
import sys
import time
import redis
import logging

from amazon.settings import SERVER_NAME, REDIS_IP, REDIS_PORT
from amazon.utils.genlog import logger

LOCK_LONGTIME = 2 * 24 * 3600

def get_cli():

    return redis.StrictRedis( REDIS_IP, REDIS_PORT )

def log_redis_error( fun ):

    def wrapper( *args, **argkv ):
        try:
            return fun( *args, **argkv )
        except redis.exceptions.RedisError, e:
            logger.debug( repr( e ) )
            raise

    return wrapper

class RedisLockError( Exception ): pass

class RedisLock( object ):

    def __init__( self, k, timeout = 3 ):

        self.key = str( k ) + '.lock'
        self.timeout = int( timeout )
        self.cli = get_cli()

    @log_redis_error
    def try_lock( self ):

        now = int( time.time() )
        pid = str( os.getpid() )

        v = '{now} {sv} {pid}'.format( now = now, sv = SERVER_NAME, pid = pid )

        now_sv_pid = self.cli.get( self.key )
        if now_sv_pid is None:
            self.cli.set( self.key, v )
            return True

        try:
            t_now, t_sv, t_pid = now_sv_pid.split()

            #long time ago or process been killed
            if now - int( t_now ) >= LOCK_LONGTIME or \
                    ( SERVER_NAME == t_sv and pid != t_pid ):
                self.cli.set( self.key, v )
                return True
        except Exception, e:
            logger.debug( repr( e ) )
            self.release()

        return False

    def acquire( self ):

        if self.try_lock():
            return
        raise RedisLockError( self.key )

    @log_redis_error
    def release( self ):

        try:
            self.cli.delete( self.key )
        except redis.exceptions.RedisError:
            pass

    def __enter__( self ):
        self.acquire()
        return self

    def __exit__( self, type, value, traceback ):
        self.release()

    def __del__( self ):
        pass


if __name__ == "__main__":

    args = sys.argv[ 1: ]

    cmd = args[ 0 ]
    args = args[ 1: ]

    @log_redis_error
    def run():
        print getattr( get_cli(), cmd )( *args )

    if cmd == 'del':
        keys = get_cli().keys( '*' )
        for k in keys:
            get_cli().delete( k )

    try:
        with RedisLock( '1' ):
            time.sleep( 100 )
    except RedisLockError, e:
        print 'redis lock error:', e

