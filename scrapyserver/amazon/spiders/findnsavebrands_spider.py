
import csv
import time
import json

import scrapy
from amazon.utils import genlog
from amazon.item.findnsave import FindnsaveBrandItem
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'findnsave_brands' )
genlog.logger = logger

class FindnsaveBrandsSpider(scrapy.Spider):

    logger = logger

    name = 'findnsavebrands'
    allowed_domains = ( "findnsave.com", )
    location = 'newyork'
    rooturl = "http://%s.findnsave.com" % location

    start_urls = [ rooturl + "/brands/" ]

    #csv_fd = open( '/tmp/brands.csv', 'w' )
    #csv.writer( csv_fd ).writerow( [ 'id', 'cid', 'name', 'href' ] )

    def parse(self, response):

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
                _b, bid, id = href.strip( '/' ).split( '/' )
            except:
                continue

            #csv.writer( self.csv_fd ).writerow( [ id, bid, name, href ] )

            d = FindnsaveBrandItem()
            d['id'] = id
            d['name'] = name
            d['nameid'] = bid
            d['uri'] = href

            yield d

        next_url = self.brand_next_page( response )
        if next_url is None:
            return

        yield scrapy.http.Request( url = next_url, callback = self.parse,
                                   dont_filter = True )

    def brand_next_page( self, response ):
        nexturl = f_xpath( response, '//div[@class="pagination"]/span[@class="next"]' )
        if nexturl is None:
            return None

        uri = fx_extract( nexturl, './a[contains(text(), "Next")]/@href' )
        if not uri:
            return None

        return self.rooturl + uri

