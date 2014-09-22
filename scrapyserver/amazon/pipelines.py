# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pprint
pp = pprint.pprint

import json

import scrapy
from amazon.utils.util import safe
from amazon.utils.genlog import logger
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
from amazon.settings import KEY_REVIEW

class AmazonReviewPipeline(object):

    def __init__(self):
        pass

    @safe
    def process_item(self, item, spider):

        cli = get_cli()

        prdid = item.get( 'prdid' )
        if not prdid:
            return

        key = KEY_REVIEW.format( p = prdid )
        cli.rpush( key, json.dumps( dict( item ) ) )

        logger.debug( repr( dict( item ) ) )
