# -*- coding: utf-8 -*-

# Scrapy settings for amazon project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

SERVER_NAME = 'server_1'

BOT_NAME = 'amazon'

SPIDER_MODULES = ['amazon.spiders']
NEWSPIDER_MODULE = 'amazon.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'amazon (+http://www.yourdomain.com)'

# log
APP_LOG_DIR = '/usr/home/shenjie1/amazonapi/scrapyserver/amazon/logs/'
APP_LOG_NAME = 'amazon'
LOG_FILE = APP_LOG_DIR + 'scrapy.log'
LOG_LEVEL = 'DEBUG'
LOG_ENABLED = True
LOG_ENCODING = 'utf-8'

# pipelines
ITEM_PIPELINES = { 'amazon.pipelines.AllPipeline' : 100 }

# redis
REDIS_IP   = '172.16.108.79'
REDIS_PORT = 6379
# keys
KEY_PRODUCTS     = 'amazon.products'
KEY_PRODUCT_TASK = 'amazon.product.{p}.task'
KEY_REVIEW       = 'amazon.review.{p}'

CRAWL_PRODUCT_TIMEOUT = 10 # days

# web servive
WEBSERVICE_ENABLED = True
WEBSERVICE_LOGFILE = APP_LOG_DIR + 'access.log'
WEBSERVICE_PORT    = 6080
WEBSERVICE_HOST    = '172.16.108.79'

