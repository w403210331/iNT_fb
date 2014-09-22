# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AmazonReviewItem( scrapy.Item ):
    # define the fields for your item here like:
    # name = scrapy.Field()

    prdid = scrapy.Field()

    rid = scrapy.Field()
    text = scrapy.Field()

    num_help_review = scrapy.Field()

    star = scrapy.Field()
    help_text = scrapy.Field()
    date = scrapy.Field()

    reviewer = scrapy.Field()
    reviewer_from = scrapy.Field()

    rfrom = scrapy.Field()

class AmazonProductItem( scrapy.Item ):

    pass
