#!/usr/bin/env python2.6
# coding: utf-8
'''
Author : Slasher ( mcq.sejust@gmail.com )
'''

import redis
import conf

def get_cli():

    return redis.StrictRedis( conf.REDIS_IP, conf.REDIS_PORT )

