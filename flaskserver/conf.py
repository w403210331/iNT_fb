
aws_key           = 'AKIAJNUNB45S2LAXFO7Q'
aws_secret        = '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'
aws_associate_tag = 'slasher0f-20'

PIDFILE = '/var/run/amazon_flask.pid'
#HOST = '218.30.108.79'
HOST = '127.0.0.1'
PORT = 7001
PROCESS_NUM = 16

LISTTYPE = ( type(()), type([]) )

#configure
URL_FOR_PASS = 'http://218.30.108.79:7000'
PAGE_ITEMS = 10
STRIPCHARS = """,.!?:()[]{}"'"""

ARGS_SHOW_REVIEW = ( ( 'error', None ),
                     ( 'reviews', [] ),
                     ( 'product_id', None ),
                     ( 'page', None ),
                     ( 'pages', None ),
                     ( 'nums', None ), )

EXCEL_KEYS = ( ( 'prdid', 'ASIN', 0  ),
               ( 'rid', 'Review ID', 1 ),
               ( 'reviewer', 'Reviewer', 2 ),
               ( 'date', 'Date', 3 ),
               ( 'num_help_review', 'Help Review Number', 4 ),
               ( 'star', 'star', 5 ),
               ( 'rfrom', 'Review From', 6 ),
               ( 'reviewer_from', 'Reviewer From', 7 ),
               ( 'help_text', 'Help Text', 8 ),
               ( 'text', 'Text', 9 ), )

SECRET_KEY = 'slasher'

REDIS_IP   = '172.16.108.79'
REDIS_PORT = 6379

KEY_PRODUCTS     = 'amazon.products'
KEY_PRODUCT_TASK = 'amazon.product.{p}.task'
KEY_REVIEW       = 'amazon.review.{p}'

APP_LOG_DIR     = '/usr/home/shenjie1/amazonapi/flaskserver/logs/'
APP_LOG_NAME    = 'amazon_flask'
ACCESS_LOG_NAME = APP_LOG_DIR + 'flask.access.log'

IGNORE_FILE = '/usr/home/shenjie1/amazonapi/flaskserver/ignore.txt'

dbconf = { 'host' : '172.16.108.79',
           'port' : 3306,
           'user' : 'amazon',
           'passwd' : 'A2a596d6',
           'db' : 'Amazon', }
