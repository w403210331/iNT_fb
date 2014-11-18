
import csv
import time
import json

import scrapy
#from amazon.items import AmazonReviewItem
from amazon.utils import genlog
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
#from amazon.settings import KEY_PRODUCTS, KEY_REVIEW, KEY_PRODUCT_TASK, CRAWL_PRODUCT_TIMEOUT
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'findnsave_stores' )

class FindnsaveStoresSpider(scrapy.Spider):

    name = 'findnsavestores'
    allowed_domains = ( "findnsave.com", )
    location = 'newyork'
    rooturl = "http://%s.findnsave.com" % location

    start_urls = [ rooturl + "/stores/" ]

    csv_fd = open( '/tmp/stores.csv', 'w' )

    def parse(self, response):
        #with open( '/tmp/findnsave_stores.html', 'w' ) as f:
        #    f.write( response.body )

        logger.info( 'fetch : ' + response.url )
        stores = f_xpath( response, '//ul[contains(@class, "listing") ' + \
                                    ' and contains(@class, "grouping")' + \
                                    ' and contains(@class, "infinite")]' ).xpath( './li' )

        for st in stores:
            sto = f_xpath( st, './/div[@class="chiclet-actions"]/a' )
            if not sto:
                continue

            href = fx_extract( sto, './@href' )
            name = fx_extract( sto, './@title' )
            name = self.parse_store_name( name )

            try:
                _s, nid, id = href.strip( '/' ).split( '/' )
            except:
                continue

            print href, nid, id, repr(name)
            csv.writer( self.csv_fd ).writerow( [ id, nid, name, href ] )

        next_url = self.store_next_page( response )
        print next_url
        if next_url is None:
            return

        yield scrapy.http.Request( url = next_url, callback = self.parse,
                                   dont_filter = True )

    def store_next_page( self, response ):
        nexturl = f_xpath( response, '//div[@class="pagination"]/span[@class="next"]' )
        if nexturl is None:
            return None

        uri = fx_extract( nexturl, './a[contains(text(), "Next")]/@href' )
        if not uri:
            return None

        return self.rooturl + uri

    @safe
    def parse_store_name( self, name ):
        if len( name ) > len( 'Shop All ' ) + len( ' Sales' ):
            name = name[ len( 'Shop All ' ):-len( ' Sales' ) ]

        return name
