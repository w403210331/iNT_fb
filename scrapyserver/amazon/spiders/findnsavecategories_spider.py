
import csv
import time
import json

import scrapy
from amazon.utils import genlog
from amazon.item.findnsave import FindnsaveCategoryItem
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'findnsave_categories' )
genlog.logger = logger

class FindnsaveCategoriesSpider(scrapy.Spider):

    logger = logger

    name = 'findnsavecategories'
    allowed_domains = ( "findnsave.com", )
    location = 'newyork'
    rooturl = "http://%s.findnsave.com" % location

    start_urls = [ rooturl + "/categories/" ]

    #csv_fd = open( '/tmp/categories.csv', 'w' )
    #csv.writer( csv_fd ).writerow( [ 'id', 'cid', 'name', 'href' ] )

    def parse(self, response):

        logger.info( 'fetch : ' + response.url )
        catgos = f_xpath( response, '//ul[contains(@class, "listing") ' + \
                                    ' and contains(@class, "grouping")' + \
                                    ' and contains(@class, "infinite")]' ).xpath( './li' )

        for ctg in catgos:
            ctg = f_xpath( ctg, './/div[@class="chiclet-actions"]/a' )
            if not ctg:
                continue

            href = fx_extract( ctg, './@href' )
            name = fx_extract( ctg, './@title' )
            name = self.parse_categorie_name( name )

            try:
                _c, cid, id = href.strip( '/' ).split( '/' )
            except:
                continue

            #csv.writer( self.csv_fd ).writerow( [ id, cid, name, href ] )

            d = FindnsaveCategoryItem()
            d['id'] = id
            d['name'] = name
            d['nameid'] = cid
            d['uri'] = href

            yield d

        next_url = self.categorie_next_page( response )
        if next_url is None:
            return

        yield scrapy.http.Request( url = next_url, callback = self.parse,
                                   dont_filter = True )

    def categorie_next_page( self, response ):
        nexturl = f_xpath( response, '//div[@class="pagination"]/span[@class="next"]' )
        if nexturl is None:
            return None

        uri = fx_extract( nexturl, './a[contains(text(), "Next")]/@href' )
        if not uri:
            return None

        return self.rooturl + uri

    @safe
    def parse_categorie_name( self, name ):
        if len( name ) > len( 'Shop All ' ) + len( ' Sales' ):
            name = name[ len( 'Shop All ' ):-len( ' Sales' ) ]

        return name
