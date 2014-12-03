
import csv
import time
import json

import scrapy
from amazon.utils import genlog
from amazon.item.findnsave import FindnsaveAreaItem
from amazon.utils.util import first_item, safe, \
                              xpath, f_xpath, first_item_xpath, \
                              xpath_extract, fx_extract, first_item_xpath_extract

logger = genlog.createlogger( 'findnsave_location' )
genlog.logger = logger

class FindnsaveLocationSpider(scrapy.Spider):

    logger = logger

    name = 'findnsavelocation'
    allowed_domains = ( "findnsave.com", )
    rooturl = "http://findnsave.com"

    start_urls = [ rooturl + "/?markets=1" ]

    def parse(self, response):

        logger.info( 'fetch : ' + response.url )
        states = f_xpath( response, '//select[@id="states-dropdown"]' ).xpath( './option' )

        sts = {}
        for st in states:
            st_short = fx_extract( st, './@value' )
            st_name = fx_extract( st, './text()' )

            if not st_short:
                continue

            if st_short not in sts:
                sts[ st_short ] = st_name

        states = xpath( response, '//ul[contains(@class, "hide") ' + \
                                  ' and contains(@class, "clearfix")]' )

        #state_fd = open( '/tmp/state_url.csv', 'w' )
        #csvw = csv.writer( state_fd )
        for st in states:
            st_short = fx_extract( st, './@id' )
            locs = st.xpath( './li' )
            for loc in locs:
                url = fx_extract( loc, './a/@href' )
                area = fx_extract( loc, './a/text()' )
                #csvw.writerow( [ st_short, sts.get( st_short, '' ), area, url ] )

                if st_short not in sts:
                    continue

                d = FindnsaveAreaItem()
                d[ 'area'  ] = area
                d[ 'short' ] = st_short
                d[ 'state' ] = sts[ st_short ]
                d[ 'url'   ] = url

                yield d

