
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

logger = genlog.createlogger( 'findnsave_brands' )

class FindnsaveBrandsSpider(scrapy.Spider):

    name = 'findnsavebrands'
    allowed_domains = ( "findnsave.com", )
    location = 'newyork'
    rooturl = "http://%s.findnsave.com" % location

    start_urls = [ rooturl + "/brands/" ]

    def parse(self, response):
        #with open( '/tmp/findnsave_brands.html', 'w' ) as f:
        #    f.write( response.body )

        logger.info( 'fetch : ' + response.url )
        brands = f_xpath( response, '//ul[contains(@class, "brands") ' + \
                                    ' and contains(@class, "columnize")' + \
                                    ' and contains(@class, "clearfix")]' ).xpath( './li' )

        for br in brands:
            br = f_xpath( br, './a' )
            if not br:
                continue

            href = fx_extract( br, './@href' )
            name = fx_extract( br, './text()' )

            try:
                _b, nid, id = href.strip( '/' ).split( '/' )
            except:
                continue

            print href, nid, id, repr(name)

        next_url = self.brand_next_page( response )
        print next_url
        if next_url is None:
            return

        yield scrapy.http.Request( url = next_url, callback = self.parse,
                                   dont_filter = True )

    def brand_next_page( self, response ):
        return None

