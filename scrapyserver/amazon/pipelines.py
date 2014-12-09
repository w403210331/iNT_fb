# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pprint
pp = pprint.pprint

import json

import scrapy
from amazon.utils.util import safe, safe_with_log
from amazon.utils.genlog import logger
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
from amazon.settings import KEY_REVIEW, dbconf
from amazon.utils import easysqllite as esql

from amazon.item.amazon import AmazonReviewItem, AmazonProductItem
from amazon.item.findnsave import FindnsaveAreaItem, \
                                  FindnsaveStoreItem, \
                                  FindnsaveBrandItem, \
                                  FindnsaveCategoryItem, \
                                  FindnsaveSaleItem

class AllPipeline(object):

    def __init__(self):
        pass

    @safe
    def process_item(self, item, spider):

        if isinstance(item, AmazonReviewItem):
            return self.process_item_amazon_review(item, spider)
        elif isinstance(item, FindnsaveAreaItem):
            return safe_with_log(spider.logger)(
                        self.process_item_findnsave_area )(item, spider)
        elif isinstance(item, FindnsaveStoreItem):
            return safe_with_log(spider.logger)(
                        self.process_item_findnsave_store )(item, spider)
        elif isinstance(item, FindnsaveBrandItem):
            return safe_with_log(spider.logger)(
                        self.process_item_findnsave_brand )(item, spider)
        elif isinstance(item, FindnsaveCategoryItem):
            return safe_with_log(spider.logger)(
                        self.process_item_findnsave_category )(item, spider)
        elif isinstance(item, FindnsaveSaleItem):
            return safe_with_log(spider.logger)(
                        self.process_item_findnsave_sale )(item, spider)

        else:
            return item

    def process_item_amazon_review(self, item, spider):

        cli = get_cli()

        prdid = item.get( 'prdid' )
        if not prdid:
            return

        key = KEY_REVIEW.format( p = prdid )
        cli.rpush( key, json.dumps( dict( item ) ) )

        logger.debug( repr( dict( item ) ) )

    def process_item_findnsave_area(self, item, spider):

        db = esql.Database( dbconf )

        sql = "select `areaid`, `area`, `short`, `state`, `url` from `findnsave_area`" + \
                " where `area` = '%s' and `state` = '%s'" %  ( item['area'], item['state'] )
        data = db.conn.read( sql )

        if not data:
            db.__getattr__( 'findnsave_area' ).puts( [ dict(item) ] )
            spider.logger.info('insert : ' + repr(dict(item)))
        else:
            if data[0]['url'] != item['url']:
                sql = "update `findnsave_area` set `url`='%s' where `areaid`=%s limit 1" % \
                        ( item['url'], data[0]['areaid'] )
                db.conn.write( sql )
                spider.logger.info('update : from %s to %s' % ( repr(data[0]), repr(dict(item)) ) )

    def process_item_findnsave_store(self, item, spider):
        self.process_item_findnsave_('findnsave_store', item, spider)

    def process_item_findnsave_brand(self, item, spider):
        self.process_item_findnsave_('findnsave_brand', item, spider)

    def process_item_findnsave_category(self, item, spider):
        self.process_item_findnsave_('findnsave_category', item, spider)

    def process_item_findnsave_( self, table, item, spider):

        db = esql.Database( dbconf )
        sql = "select `id`, `name`, `nameid`, `uri` from `%s`" % table + \
                " where `id` = '%s'" %  ( item['id'], )
        data = db.conn.read( sql )

        if not data:
            db.__getattr__( table ).puts( [ dict(item) ] )
            spider.logger.info('insert : ' + repr(dict(item)))
        else:
            if data[0]['name'] != item['name']:
                sql = "update `%s` set `name`='%s' where `id`=%s limit 1" % \
                        ( table, item['name'], data[0]['id'] )
                db.conn.write( sql )
                spider.logger.info('update : from %s to %s' % ( repr(data[0]), repr(dict(item)) ) )

    def process_item_findnsave_sale(self, item, spider):

        table = 'findnsave_sale_t'

        db = esql.Database( dbconf )
        sql = "select * from `%s`" % table + \
                " where `id` = '%s' and `area` = '%s'" %  ( item['id'], item['area'] )
        data = db.conn.read( sql )

        if not data:
            db.__getattr__( table ).puts( [ dict(item) ] )
            spider.logger.info('insert : ' + repr(dict(item)))
        else:
            pass
