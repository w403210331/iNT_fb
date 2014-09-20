#!/bin/env python8.6
# coding: utf-8

import json

import conf
import rediscli
import amazonapi

handle = amazonapi.AmazonAPI( conf.aws_key,
                              conf.aws_secret,
                              conf.aws_associate_tag,
                              )

#product = handle.lookup( ItemId = 'B00IQ8MWBS' )

products = handle.search( Keywords='Barbie', SearchIndex='Toys' )

cli = rediscli.get_cli()
key = 'amazon.products'

i = 0
for product in products:
    i += 1

    d = {}
    d[ 'asin' ] = product.asin

    #cli.rpush( key, json.dumps( d ) )


    attrs = ( 'price_and_currency',
              'asin',
              'sales_rank',
              'offer_url',
              'author',
              'authors',
              'creators',
              'publisher',
              'label',
              'manufacturer',
              'brand',
              'isbn',
              'eisbn',
              'binding',
              'pages',
              # 'publication_date',
              # 'release_date',
              'edition',
              'large_image_url',
              'medium_image_url',
              'small_image_url',
              'tiny_image_url',
              'reviews',
              'title',
              'list_price', )

    maxlen = max( [ len(k) for k in attrs ] )
    for k in attrs:
        print k.rjust( maxlen ), ':', getattr( product, k )

    for br in product.browse_nodes:
        print br.id
        print br.name
        print br.ancestor.name
        #print ' '.join( [ b.name for b in br.children ] )

    print '-*-*' * 20
    print

    if i == 10:
        break
