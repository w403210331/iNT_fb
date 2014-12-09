# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class FindnsaveAreaItem( Item ):
    area  = Field()
    short = Field()
    state = Field()
    url   = Field()

class FindnsaveStoreItem( Item ):
    id = Field()
    name = Field()
    nameid = Field()
    uri = Field()

class FindnsaveBrandItem( Item ):
    id = Field()
    name = Field()
    nameid = Field()
    uri = Field()

class FindnsaveCategoryItem( Item ):
    id = Field()
    name = Field()
    nameid = Field()
    uri = Field()

class FindnsaveSaleItem( Item ):
    area = Field()
    id = Field()
    name = Field()
    priceCurrency = Field()
    price = Field()
    priceRegular = Field()
    priceUtilDate = Field()
    priceOff = Field()
    retailer = Field()
    category = Field()
    brand = Field()
    desc = Field()
