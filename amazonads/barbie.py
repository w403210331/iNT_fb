#!/bin/env python8.6
# coding: utf-8

import json

import conf
import rediscli
import amazonapi

handle = amazonapi.AmazonAPI( conf.aws_key,
                              conf.aws_secret,
                              conf.aws_associate_tag,
                              Version = '2013-08-01',
                              )

#product = handle.lookup( ItemId = 'B00IQ8MWBS' )

products = handle.search( Keywords='Barbie', SearchIndex='Toys' )
#products = handle.search( Keywords='iPhone', SearchIndex='Electronics' )

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
              'publication_date',
              'release_date',
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
        nodes = []

        if br.name is None:
            continue

        nodes.append( str( br.name ) )

        anc = br.ancestor
        while True:
            if anc is None:
                break

            if anc.name is not None:
                nodes.append( str( anc.name ) )
            anc = anc.ancestor

        nodes.reverse()

        print ' -> '.join( nodes )

    print '-*-*' * 20
    print

    if i == 5:
        break
