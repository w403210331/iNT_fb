
import csv
import time
import json

import scrapy
from amazon.utils import genlog
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'findnsave_sales' )
genlog.logger = logger

class FindnsaveStoresSpider(scrapy.Spider):

    logger = logger

    name = 'findnsavesales'
    allowed_domains = ( "findnsave.com", )
    location = 'newyork'
    rooturl = "http://%s.findnsave.com" % location

    start_urls = [ rooturl + "/store/Walmart/10175/" ]

    #csv_fd = open( '/tmp/newyork_sales.csv', 'w' )
    #writer = csv.writer( csv_fd, delimiter = '\\' )

    jsonfile = open( '/tmp/sales.json', 'a' )

    @safe
    def parse_one_sale(self, response):
        #with open( '/tmp/findnsave_sales_one.html', 'w' ) as f:
        #    f.write( response.body )

        date = f_xpath( response, '//div[contains(@class, "offer-pdp-hd") ' + \
                                   ' and contains(@class, "clearfix")]' )

        right = ''
        expiration = ''
        if date:
            right = f_xpath( date, './/div[@class="offer-right"]' )
            right = fx_extract( right, './h2/text()' ) or ''

            exp = f_xpath( date, './/div[contains(@class, "expiration") ' + \
                                   ' and contains(@class, "with-date") ]' )
            if exp:
                expiration = fx_extract( exp, './div/text()' )

        sale = f_xpath( response, '//div[contains(@class, "offer-description-wrapper") ' + \
                                   ' and contains(@class, "clearfix")]' )
        if not sale:
            return

        #lg_img
        lg_img = fx_extract( sale, './div[@class="offer-left"]/div[contains(@class, "large")]' + \
                                   '/img/@src' ) or ''

        sr = f_xpath( sale, './div[@class="offer-right"]' )

        #name
        name = fx_extract( sr, './h1[@itemprop="name"]/text()' )
        if name is None:
            return

        #price
        price = f_xpath( sr, './div[@class="product-price"]' )
        p_c = fx_extract( price, './/span[@itemprop="priceCurrency"]/@content' ) or ''
        p_p = fx_extract( price, './/span[@itemprop="price"]/@content' ) or '-1'
        p_r = fx_extract( price, './/span[@itemprop="regular-price"]/text()' ) or ''
        p_u = fx_extract( price, './/span[@itemprop="priceValidUntil"]/@content' ) or ''
        try:
            float( p_p )
        except Exception:
            p_p = '-1'

        #desc
        desc = f_xpath( sr, './div[@class="offer-descriptions"]' )
        desc = '|'.join( xpath_extract( desc, './/div[@class="offer-description"]/text()' ) ).strip()

        #retailer
        retailer = fx_extract( sr, './p[@class="retailer"]/a/text()' ) or ''
        retailer = retailer.strip()
        #category
        category = fx_extract( sr, './p[@class="parentCategory"]/a/text()' ) or ''
        category = category.strip()
        #brand
        brand = fx_extract( sr, './p[@class="brand"]/a/text()' ) or ''
        brand = brand.strip()

        data = [ response.meta[ 'id' ], name,
                    p_p, p_c, p_r, p_u,
                    right, expiration,
                    retailer, category, brand,
                    response.url, response.meta[ 'th_img' ], lg_img,
                    desc, ]

        self.jsonfile.write( json.dumps( data ) + '\n' )
        logger.info( 'crawl : `' + name + '` OK' )
        return

    def parse(self, response):
        #with open( '/tmp/findnsave_sales.html', 'w' ) as f:
        #    f.write( response.body )

        logger.info( 'fetch : ' + response.url )
        sales = f_xpath( response, '//ul[contains(@class, "listing") ' + \
                                   ' and contains(@class, "retailer-detail")' + \
                                   ' and contains(@class, "infinite")]' ).xpath(
                                './li[starts-with(@id, "offer-")]' )
        for s in sales:
            s = f_xpath( s, './div' ).xpath( './a' )
            id = fx_extract( s, './@data-offer-id' )
            href = fx_extract( s, './@href' )
            th_img = fx_extract( s, './img/@src' )

            if not ( id and href and th_img ):
                continue

            # TODO : id if in db continue

            if not href.startswith( 'http://' ):
                href = self.rooturl + href

            meta = { 'id' : id,
                     'href' : href,
                     'th_img' : th_img }

            yield scrapy.http.Request( url = href,
                                       callback = self.parse_one_sale,
                                       meta = meta,
                                       dont_filter = True )


        next_url = self.store_next_page( response )
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
