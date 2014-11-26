
import json

import scrapy
from amazon.utils import genlog
from amazon.utils.s3clientutil import authedclient, put_file_from_url
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'earthpics' )

class EarthPicsSpider(scrapy.Spider):

    name = 'earthpics'
    allowed_domains = ( "earthpics.me", )
    start_urls = [ "http://earthpics.me/" ]

    prefix_len = len( 'http://earthpics.me/' )

    @safe
    def parse_one_top( self, response ):

        logger.info( 'fetch : ' + response.url )

        img = f_xpath( response, '//div[contains(@class, "inner-main-content")]' )

        meta = {}
        meta[ 'name' ] = fx_extract( img, './div/h3/text()' ).strip().strip('#')
        meta[ 'img'  ] = fx_extract( img, './/div[@class="inner-image"]/img/@src' )
        meta[ 'key'  ] = meta[ 'img' ][ self.prefix_len: ]
        meta[ 'from' ] = fx_extract( img, './/div[@class="inner-image"]/a/@href' )
        meta[ 'desc' ] = fx_extract( img, './div/p/text()' )

        curr_meta = response.meta
        curr_meta[ 'top' ].append( meta )

        nexturl = self.next_top_img( response )
        if nexturl:
            yield scrapy.http.Request( url = nexturl,
                                       callback = self.parse_one_top,
                                       meta = curr_meta,
                                       dont_filter = True )
        else:
            cli = authedclient()
            cli.upload_data( curr_meta[ 'key' ], json.dumps( curr_meta ),
                        headers = { 'Content-Type' : 'text/json' } )
            logger.info( 'upload : ' + curr_meta[ 'key' ] )

            for meta in curr_meta[ 'top' ]:
                put_file_from_url( cli, meta[ 'key' ], meta[ 'img' ] )
                logger.info( 'upload : %s from %s' % ( meta[ 'key' ], meta[ 'img' ] ) )

    def parse(self, response):

        logger.info( 'fetch : ' + response.url )
        tops = f_xpath( response, '//ul[contains(@class, "thumbnails")]' ).xpath( './li' )

        for top in tops:
            top = f_xpath( top, './div[@class="thumbnail"]' )
            if not top:
                continue

            name = fx_extract( top, './p/strong/text()' )
            href = fx_extract( top, './a/@href' ).strip()

            curr_meta = {}
            curr_meta[ 'name' ] = name
            curr_meta[ 'url' ] = href
            curr_meta[ 'key' ] = 'meta/' + href[ self.prefix_len: ] + '.json'
            curr_meta[ 'top' ] = []

            yield scrapy.http.Request( url = href,
                                       callback = self.parse_one_top,
                                       meta = curr_meta,
                                       dont_filter = True )

    def next_top_img( self, response ):
        urls = f_xpath( response, '//div[contains(@style, "margin-bottom")]' ).xpath( './div' )[1:]
        for url in urls:
            nxt = fx_extract( url, './a[contains(text(), "Next")]/@href' )
            if nxt:
                return nxt

