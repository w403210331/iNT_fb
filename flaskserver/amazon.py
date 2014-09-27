
import time
import json
import logging
import StringIO
import mimetypes

import conf
from rediscli import get_cli
from amazonapi import AmazonAPI
import genlog
logger = genlog.logger

import xlwt
from werkzeug.datastructures import Headers
from flask import Flask, Response, \
            request, abort, redirect, url_for, \
            render_template, session, flash

PAGE_ITEMS = conf.PAGE_ITEMS

app = Flask( __name__ )
app.secret_key = conf.SECRET_KEY

def safe( func ):
    def wrapper( *args, **argkv ):
        try:
            return func( *args, **argkv )
        except Exception, e:
            logger.exception( repr( e ) )
            return None

    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    wrapper.__module__ = func.__module__

    return wrapper

app.route = safe( app.route )

@safe
def load_ignore():
    with open( conf.IGNORE_FILE, 'r' ) as f:
        return [ l.strip() for l in f ]

@safe
def add_ignore_word( word ):
    with open( conf.IGNORE_FILE, 'a' ) as f:
        f.write( word + '\n' )

def _dict_product( product ):

    return dict(
            asin = product.asin,
            title = product.title,
            price_and_currency = product.price_and_currency,
            sales_rank = product.sales_rank,
            offer_url = product.offer_url,
            author = product.author,
            authors = product.authors,
            creators = product.creators,
            publisher = product.publisher,
            label = product.label,
            manufacturer = product.manufacturer,
            brand = product.brand,
            isbn = product.isbn,
            large_image_url = product.large_image_url,
            medium_image_url = product.medium_image_url,
            small_image_url = product.small_image_url,
            reviews = product.reviews,
            list_price = product.list_price, )

def time_delay( t ):

    minute = 60
    hour = minute * 60
    day = hour * 24

    t = time.time() - t
    t = int( t )

    s = ''
    if t >= day:
        s += str( t / day ) + 'D/'
        t = t % day
    if t >= hour:
        s += str( t/ hour ) + 'H/'
        t = t % hour
    if t >= minute:
        s += str( t/ minute ) + 'M'

    return s

@safe
def get_product( product_id ):

    logger.info( 'get : ' + product_id )

    handle = AmazonAPI( conf.aws_key,
                        conf.aws_secret,
                        conf.aws_associate_tag, )
    product = handle.lookup( ItemId = product_id )

    d = _dict_product( product )

    cli = get_cli()
    k = conf.KEY_REVIEW.format( p = product.asin )
    d[ 'crawl' ] = True if cli.exists( k ) else False

    k = conf.KEY_PRODUCT_TASK.format( p = product.asin )
    if cli.exists( k ):
        r = cli.get( k )
        d[ 'delay' ] = time_delay( json.loads( r )[ 'ctime' ] )
    else:
        d[ 'delay' ] = None

    if d[ 'reviews' ] and d[ 'reviews' ][ 0 ]:
        d[ 'reviews' ] = d[ 'reviews' ][ 1 ]

    return d

@safe
def get_search_products( Keywords, SearchIndex, num = 10, **argkv ):

    logger.info( 'search : ' + repr( ( Keywords, SearchIndex, num, argkv ) ) )

    handle = AmazonAPI( conf.aws_key,
                        conf.aws_secret,
                        conf.aws_associate_tag, )

    products = handle.search( Keywords = Keywords,
                              SearchIndex = SearchIndex, **argkv )

    cli = get_cli()

    items = []
    for product in products:
        d = _dict_product( product )

        k = conf.KEY_REVIEW.format( p = product.asin )
        d[ 'crawl' ] = True if cli.exists( k ) else False

        k = conf.KEY_PRODUCT_TASK.format( p = product.asin )
        if cli.exists( k ):
            r = cli.get( k )
            d[ 'delay' ] = time_delay( json.loads( r )[ 'ctime' ] )
        else:
            d[ 'delay' ] = None

        if d[ 'reviews' ] and d[ 'reviews' ][ 0 ]:
            d[ 'reviews' ] = d[ 'reviews' ][ 1 ]

        items.append( d )
        if len( items ) == num:
            return items

@safe
def yield_review( prdid ):

    if prdid is None:
        return

    cli = get_cli()
    k = conf.KEY_REVIEW.format( p = prdid )
    if not cli.exists( k ):
        return

    lenth = cli.llen( k )
    start, stop = 0, PAGE_ITEMS - 1
    while start <= lenth:
        rws = cli.lrange( k, start, stop )
        start = start + PAGE_ITEMS
        stop = stop + PAGE_ITEMS

        for r in rws:
            yield json.loads( r )

@safe
def order_review_words( prdid, num ):

    rw_iter = yield_review( prdid )
    if rw_iter is None:
        return []

    IGNORE_WORDS = load_ignore()

    words = {}
    for rw in rw_iter:

        text = rw.get( 'help_text', '' ) + ' ' + \
                rw.get( 'text', '' )

        text = text.split()
        for t in text:
            t = t.lower().strip( conf.STRIPCHARS )
            if t in IGNORE_WORDS or ( not t ):
                continue

            if t not in words:
                words[ t ] = 0
            words[ t ] += 1

    kvs = words.items()
    kvs.sort( key = lambda x:x[ 1 ], reverse = True )

    return kvs[ :num ]

@safe
def get_reviews( prdid, page ):

    if prdid is None:
        return None, None, None

    cli = get_cli()
    k = conf.KEY_REVIEW.format( p = prdid )
    if not cli.exists( k ):
        return None, None, None

    nums = cli.llen( k )
    if nums % PAGE_ITEMS == 0:
        pages = nums / PAGE_ITEMS
    else:
        pages = nums / PAGE_ITEMS + 1

    rws = cli.lrange( k, ( page - 1 ) * PAGE_ITEMS,
                         page * PAGE_ITEMS - 1 )
    rws = [ json.loads( r ) for r in rws ]

    return rws, pages, nums

@safe
def get_reviews_has_keywords( prdid, keywords, key = 'or' ):

    if prdid is None:
        return None

    keywords = keywords or []
    if not keywords:
        return get_reviews( prdid, 1 )[ 0 ]

    rw_iter = yield_review( prdid )
    if rw_iter is None:
        return None

    rws = []
    for rw in rw_iter:

        text = rw.get( 'help_text', '' ) + ' ' + \
                rw.get( 'text', '' )

        text = text.lower()
        if key == 'or':
            for keyword in keywords:
                if keyword in text:
                    rws.append( rw )
                    break
        elif key == 'and':
            for keyword in keywords:
                if keyword not in text:
                    break
            else:
                rws.append( rw )

    return rws

def add_color_keyword( s, fm ):
    # replace 'the' and 'The'
    # to <font color="red">the</font>
    # to <font color="red">The</font>

    if not fm:
        return s

    to = '<font color="red">' + fm + '</font>'
    s = s.replace( fm, to )

    fm = fm[ 0 ].upper() + fm[ 1: ]
    to = '<font color="red">' + fm + '</font>'

    return s.replace( fm, to )

@safe
def search_reviews_has_keywords( prdid, keywords, key = 'or' ):

    rws = get_reviews_has_keywords( prdid, keywords, key )
    if not rws:
        return []

    for rw in rws:

        for k in ( 'help_text', 'text' ):
            text = rw[ k ]
            for kw in keywords:
                text = add_color_keyword( text, kw )
            rw[ k ] = text

    return rws

def url_for_pass( *argv, **argkv ):
    return conf.URL_FOR_PASS + url_for( *argv, **argkv )

@app.route( '/ignore_word/<word>', methods = [ 'GET', 'POST' ] )
def ignore_word( word = None ):
    if word is None:
        logger.debug( 'Not Set Word' )
        return "Error: Not Set Word"

    IGNORE_WORDS = load_ignore()

    wds = word.strip().split()
    for w in wds:
        if w in IGNORE_WORDS:
            continue

        add_ignore_word( w )

    text = "OK, ignored ( " + word + ' )'
    logger.info( text )

    return text

@app.route( '/' )
def root():
    return redirect( url_for_pass( 'search' ) )

@app.route( '/add/<product_id>', methods = [ 'GET', 'POST' ] )
def add( product_id = None ):

    try:
        cli = get_cli()

        d = {}
        d[ 'asin' ] = product_id
        cli.rpush( conf.KEY_PRODUCTS, json.dumps( d ) )

        logger.info( 'rpush {p} to {k}'.format(
                        p = product_id, k = conf.KEY_PRODUCTS ) )
    except Exception, e:
        logger.warn( repr( e ) + ', when rpush {p} to {k}'.format(
                        p = product_id, k = conf.KEY_PRODUCTS ) )
        return repr( e )

    return "add to queue ok, wait to crawl..."

@app.route( '/search/', methods = [ 'GET', 'POST' ] )
def search():
    error = None
    if request.method == 'POST':
        keywords = request.form[ 'keywords' ].strip()
        search_index = request.form[ 'select_index' ]
        num = request.form[ 'number' ]

        return redirect( url_for_pass( 'search_product',
                                       keywords = keywords,
                                       search_index = search_index,
                                       num = num ) )

    return render_template( 'search.html', error = error )

@app.route( '/show_product/<product_id>', methods = [ 'GET' ] )
def show_product( product_id = None ):
    error = None
    if product_id is None:
        error = "Invalid Argument : product_id"

    if error:
        return render_template( 'show_product.html',
                                error = error, products = [] )

    prdids = product_id.split()
    products = [ get_product( prdid ) for prdid in prdids ]
    products = [ p for p in products if p ]

    return render_template( 'show_product.html',
                            error = error, products = products )

@app.route( '/show_product_post/', methods = [ 'GET', 'POST' ] )
def show_product_post():
    error = None
    if request.method == 'POST':
        asin = request.form[ 'asin' ].strip()
        products = get_product( asin )
        products = [ products ] if products else []

        return render_template( 'show_product.html',
                                error = error, products = products )

    return render_template( 'show_product.html',
                            error = error, products = [] )

@app.route( '/search_product/<search_index>/<keywords>/<int:num>', methods = [ 'GET' ] )
def search_product( keywords = None, search_index = 'All', num = 10 ):
    error = None
    if num <= 0:
        error = 'Invalid Number: ' + str( num )

    if error:
        return render_template( 'search_product.html',
                                error = error, products = [] )

    prds = get_search_products( keywords, search_index, num ) or []

    return render_template( 'search_product.html',
                            error = error, products = prds )

def render_show_reviews( **argkv ):

    kv = {}
    for k, v in conf.ARGS_SHOW_REVIEW:
        kv[ k ] = argkv[ k ] if k in argkv else v

    return render_template( 'show_reviews.html', **kv )

@app.route( '/show_reviews/<product_id>/<int:page>', methods = [ 'GET' ] )
def show_reviews( product_id = None, page = 1 ):
    error = None
    if page <= 0:
        error = 'Invalid Page: ' + str( page )

    if error:
        return render_show_reviews( error = error )

    rws, pages, nums = get_reviews( product_id, page )
    rws = rws or []

    return render_show_reviews( reviews = rws, product_id = product_id, page = page,
                                pages = pages, nums = nums )

@app.route( '/export_reviews/<product_id>', methods = [ 'GET' ] )
def export_reviews( product_id = None ):
    error = None
    if product_id is None:
        error = 'Invalid ASIN: ' + str( product_id )

    if error:
        return render_show_reviews( error = error )

    response = Response()
    response.status_code = 200

    workbook = xlwt.Workbook( encoding = 'utf-8' )

    prdids = product_id.split( ',' )
    for prdid in prdids:
        sheet = workbook.add_sheet( prdid )

        for k, sk, ix in conf.EXCEL_KEYS:
            sheet.write( 0, ix, sk )

        num = 1
        iter = yield_review( prdid ) or []
        for rw in iter:
            for k, sk, ix in conf.EXCEL_KEYS:
                try:
                    v = rw[ k ] or ''
                    if type( v ) in conf.LISTTYPE:
                        fmt = ','.join( [ '%s' ] * len( v ) )
                        v = fmt % tuple( v )
                    elif type( v ) == type( u'' ):
                        v = v.encode( 'utf-8' )
                except Exception, e:
                    logger.debug( repr( e ) )
                    v = ''

                sheet.write( num, ix, v )

            num += 1

    filename = product_id + '.xls'
    output = StringIO.StringIO()
    workbook.save( output )
    response.data = output.getvalue()

    mimetype_tuple = mimetypes.guess_type( filename )

    #HTTP headers for forcing file download
    response_headers = Headers( {
                    'Pragma': "public",
                    'Expires': '0',
                    'Cache-Control': 'must-revalidate, post-check=0, pre-check=0',
                    'Cache-Control': 'private',
                    'Content-Type': mimetype_tuple[ 0 ] or 'application/vnd.ms-excel',
                    'Content-Disposition': 'attachment; filename=\"%s\";' % filename,
                    'Content-Transfer-Encoding': 'binary',
                    'Content-Length': len( response.data ), } )

    if not mimetype_tuple[ 1 ] is None:
        response.update( { 'Content-Encoding': mimetype_tuple[ 1 ] } )

    response.headers = response_headers

    #as per jquery.fileDownload.js requirements
    response.set_cookie( 'fileDownload', 'true', path = '/' )

    logger.info( 'download %s, %d items' % ( filename, num - 1 ) )

    return response

@app.route( '/show_reviews_has_keyword/<product_id>/<keywords>', methods = [ 'GET' ] )
def show_reviews_has_keyword( product_id = None, keywords = None ):
    error = None
    if product_id is None or keywords is None:
        error = "Invalid Argument : " + repr( ( product_id, keywords ) )

    if error:
        return render_show_reviews( error = error )

    keywords = keywords.lower().split()
    keywords = list( set( keywords ) )
    rws = search_reviews_has_keywords( product_id, keywords ) or []

    return render_show_reviews( reviews = rws, product_id = product_id )

@app.route( '/search_keywords/<product_id>', methods = [ 'GET', 'POST' ] )
def search_keywords( product_id = None ):
    error = None
    if product_id is None:
        error = 'Invalid Argument : product_id is None'

    if error:
        return redirect( url_for_pass( 'show_reviews.html',
                                       error = error, reviews = [],
                                       product_id = None, page = None,
                                       pages = None, nums = None ) )

    if request.method == 'POST':
        keywords = request.form[ 'keywords' ].strip()
        logger.info( 'search_keywords: (' + keywords + ') of ' + product_id )

        if '+' in keywords:
            keywords = keywords.lower().split( '+' )
            key = 'and'
        else:
            keywords = keywords.lower().split()
            key = 'or'

        keywords = list( set( keywords ) )
        rws = search_reviews_has_keywords( product_id, keywords, key ) or []

        return render_show_reviews( reviews = rws, product_id = product_id )

    return render_show_reviews()

@app.route( '/order_words/<product_id>/<int:num>', methods = [ 'GET' ] )
def order_words( product_id = None, num = 1 ):
    error = None
    if num <= 0:
        error = 'Invalid Number: ' + str( num )

    if error:
        return render_template( 'show_review_words.html',
                                error = error, words = [],
                                product_id = None )

    kvs = order_review_words( product_id, num ) or []

    return render_template( 'show_review_words.html',
                            error = error, words = kvs,
                            product_id = product_id )

def set_access_logger():

    access_logger = logging.getLogger( 'werkzeug' )
    handler = logging.FileHandler( conf.ACCESS_LOG_NAME )
    access_logger.addHandler( handler )
    #app.logger.addHandler(handler)

def _run():

    #app.debug = True
    app.run( host = conf.HOST, port = conf.PORT,
             threaded = True,
             #processes = conf.PROCESS_NUM,
             )

def run():
    while True:
        try:
            set_access_logger()
            _run()
        except Exception, e:
            logger.exception( repr( e ) )

        time.sleep( 60 )

if __name__ == '__main__':

    import daemonize
    daemonize.standard_daemonize( run, conf.PIDFILE )

