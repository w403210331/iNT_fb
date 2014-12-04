
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

    def _parse_date(self, response):
        date = f_xpath( response, '//div[contains(@class, "offer-pdp-hd") ' + \
                                   ' and contains(@class, "clearfix")]' )
        starts = ''
        expiration = ''
        if not date:
            return starts, expiration

        st = f_xpath( date, './/div[@class="offer-right"]' )
        if st:
            starts = fx_extract( st, './h2/text()' ) or ''

        exp = f_xpath( date, './/div[contains(@class, "expiration") ' + \
                               ' and contains(@class, "with-date") ]' )
        if exp:
            expiration = fx_extract( exp, './div/text()' ) or ''
        return starts, expiration

    def _parse_callout(self, p):
        callout = f_xpath( p, './div[@class="callout"]' )

        pct_off = ''
        if callout:
            pct = fx_extract( callout, './span[@class="pct"]/text()' ) or ''
            off = fx_extract( callout, './span[@class="off"]/text()' ) or ''
            pct_off = (pct + ' ' + off).strip()

        return pct_off

    def _parse_large_img(self, p):
        return fx_extract( p, './div[@class="offer-left"]' + \
                              '/div[contains(@class, "large")]' + \
                              '/img/@src' ) or ''

    def _parse_price(self, p):
        price = f_xpath( p, './div[@class="product-price"]' )
        p_c = fx_extract( price, './/span[@itemprop="priceCurrency"]/@content' ) or ''
        p_p = fx_extract( price, './/span[@class="price"]/@content' ) or '-1'
        p_r = fx_extract( price, './/span[@class="regular-price"]/text()' ) or ''
        p_u = fx_extract( price, './/span[@itemprop="priceValidUntil"]/@content' ) or ''
        try:
            float( p_p )
        except Exception:
            p_p = '-1'

        if p_c == 'USD':
            if '$' in p_r:
                p_r = p_r.split('$')[1].split()[0]

        return p_c, p_p, p_r, p_u

    def _parse_desc(self, p):
        desc = f_xpath( p, './div[@class="offer-descriptions"]' )
        desc = ' '.join( [ x.strip() for x in \
                    xpath_extract( desc, './/div[@class="offer-description"]/text()' ) ] )

        return desc

    def _parse_retailer_category_brand(self, p):
        retailer = (fx_extract( p, './p[@class="retailer"]/a/text()' ) or '').strip()
        category = (fx_extract( p, './p[@class="parentCategory"]/a/text()' ) or '').strip()
        brand    = (fx_extract( p, './p[@class="brand"]/a/text()' ) or '').strip()

        return retailer, category, brand

    @safe
    def parse_one_sale(self, response):
        #with open( '/tmp/findnsave_sales_one.html', 'w' ) as f:
        #    f.write( response.body )

        sale = f_xpath( response, '//div[contains(@class, "offer-description-wrapper") ' + \
                                   ' and contains(@class, "clearfix")]' )
        if not sale:
            return

        starts, expiration = self._parse_date( response )
        pct_off = self._parse_callout( sale )
        lg_img = self._parse_large_img( sale )

        sr = f_xpath( sale, './div[@class="offer-right"]' )
        name = fx_extract( sr, './h1[@itemprop="name"]/text()' )
        if name is None:
            logger.debug( 'not crawl name in : ' + response.url )
            return

        p_c, p_p, p_r, p_u = self._parse_price( sr )
        desc = self._parse_desc( sr )
        retailer, category, brand = self._parse_retailer_category_brand( sr )

        data = [ response.meta[ 'id' ], name,
                    p_c, p_p, p_r, p_u, pct_off,
                    starts, expiration,
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
