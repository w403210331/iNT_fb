
import time
import json

import scrapy
from amazon.items import AmazonReviewItem
from amazon.utils.genlog import logger
from amazon.utils.rediscli import get_cli, RedisLock, RedisLockError
from amazon.settings import KEY_PRODUCTS, KEY_REVIEW, KEY_PRODUCT_TASK, CRAWL_PRODUCT_TIMEOUT
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

@safe
def get_product_task( prdid ):

    cli = get_cli()
    d = cli.get( KEY_PRODUCT_TASK.format( p = prdid ) )
    if d is None:
        return None

    try:
        return json.loads( d )
    except Exception as e:
        logger.info( 'get task: {p} {d} {e}'.format(
                    p = prdid, d = repr( d ), e = repr( e ) ) )

@safe
def set_product_task( prdid ):

    task = { 'prdid' : prdid,
             'ctime' : time.time() }
    task_k = KEY_PRODUCT_TASK.format( p = prdid )

    cli = get_cli()
    cli.set( task_k, json.dumps( task ) )

@safe
def del_product_reviews( prdid ):

    k = KEY_REVIEW.format( p = prdid )

    cli = get_cli()
    if cli.exists( k ):
        cli.delete( k )

def product_is_timeout( prdid ):

    task = get_product_task( prdid )
    if task is None:
        return True

    if time.time() - task.get( 'ctime', 0 ) >= CRAWL_PRODUCT_TIMEOUT * 24 * 3600:
        return True

    return False

def next_product_url():

    cli = get_cli()
    while True:

        product = cli.lpop( KEY_PRODUCTS )
        if product is None:
            logger.info( 'no product in queue ...' )
            time.sleep( 5 )
            continue

        try:
            product = json.loads( product )[ 'asin' ]

            if not product_is_timeout( product ):
                logger.info( 'product : ' + product + \
                                ' is not timeout, {day} days'.format(
                                        day = CRAWL_PRODUCT_TIMEOUT ) )
                continue

            set_product_task( product )
            del_product_reviews( product )

            logger.info( 'next product : ' + product )
            return 'http://www.amazon.com/ss/customer-reviews/' + product

        except Exception as e:
            logger.exception( repr( e ) )

class AmazonSpider(scrapy.Spider):

    name = 'amazon'
    allowed_domains = ( "www.amazon.com", )

    url_prev = 'http://www.amazon.com/ss/customer-reviews/'

    start_urls = [
            "http://www.amazon.com/ss/customer-reviews/B00IQ8MWBS",
            ]
    #start_urls = [ next_product_url() ]

    def empty_item( self ):

        d = AmazonReviewItem()
        for k in ( 'prdid', 'rid', 'text', 'help_text', 'date',
                   'reviewer', 'reviewer_from', 'rfrom' ):
            d[ k ] = ''

        for k in ( 'num_help_review', 'star' ):
            d[ k ] = None

        return d

    def next_page( self, response ):

        nexturl = f_xpath( response, '//table[@class="CMheadingBar"]/tr/td[1]/div/span' )
        if nexturl is None:
            return None

        return fx_extract( nexturl, './a[contains(text(), "Next")]/@href' )

    def parse(self, response):
        #with open( '/tmp/amazon.html', 'w' ) as f:
        #    f.write( response.body )

        logger.info( 'fetch : ' + response.url )
        prdid = response.url.split( '?' )[ 0 ].split( '/' )[ -1 ]

        review = f_xpath( response, '//table[@id="productReviews"]/tr/td' )
        if review is None:
            yield scrapy.http.Request( url = next_product_url(),
                                       callback = self.parse )

        rids = xpath_extract( review, './a/@name' )
        details = xpath( review, './div' )

        lenth = min( len( rids ), len( details ) )
        for i in xrange( lenth ):

            rdetail = details[ i ]
            divs = xpath( rdetail, './div' )

            # max of len( divs ) is 7, ( 0 - 6 )
            # 0 : number of helpful review
            # 1 : star, helpful text, date
            # 2 : reviewer, reviewer from
            # 3 : from
            # 4 : free product
            # 5 : reviewText
            # 6 : helpful?

            d = self.empty_item()
            d[ 'prdid' ] = prdid
            d[ 'rid' ] = rids[ i ]
            d[ 'text' ] = ' '.join( xpath_extract( rdetail,
                                    './div[@class="reviewText"]/text()' ) )

            while len( divs ) > 0:
                div = divs[ 0 ]
                divs = divs[ 1: ]

                text = div.extract()

                if 'people found the following review helpful' in text:
                    d[ 'num_help_review' ] = self.parse_num_help_review( div )
                    continue

                if 'out of' in text and 'stars' in text and '</nobr>' in text:
                    d[ 'star' ], d[ 'help_text' ], d[ 'date' ] = \
                                self.parse_star_help_date( div )
                    continue

                if 'By' in text and 'See all my reviews' in text:
                    d[ 'reviewer' ], d[ 'reviewer_from' ] = \
                                self.parse_reviewer_from( div )
                    continue

                if 'This review is from' in text:
                    d[ 'rfrom' ] = self.parse_from( div )

                break

            yield d

        next_url = self.next_page( response ) or \
                        next_product_url()

        # see http://doc.scrapy.org/en/latest/topics/request-response.html
        yield scrapy.http.Request( url = next_url, callback = self.parse,
                                   dont_filter = True )


    @safe
    def parse_num_help_review( self, div ):

        # text : 3 of 3 people found the following review helpful

        text = fx_extract( div, './text()' )
        if text is None:
            return None

        text = text.strip().split()
        return ( int( text[ 0 ] ), int( text[ 2 ] ) )

    @safe
    def _parse_star( self, div ):

        # text : 5.0 out of 5 stars

        star = fx_extract( div, './span[1]/span/span/text()' )
        if star is None:
            return None
        else:
            star = star.strip().split()
            star = ( float( star[ 0 ] ), float( star[ 3 ] ) )

            return star
    @safe
    def parse_star_help_date( self, div ):
        return ( self._parse_star( div ),
                 fx_extract( div, './span[2]/b/text()' ) or '',
                 fx_extract( div, './span[2]/nobr/text()' ) or '' )

    @safe
    def parse_reviewer_from( self, div ):
        return ( fx_extract( div, './div/div[2]/a/span/text()' ) or '',
                 ( fx_extract( div, './div/div[2]/text()' ) or '' ).strip( ' -' ) )

    @safe
    def parse_from( self, div ):
        return fx_extract( div, './b/text()' ) or ''


