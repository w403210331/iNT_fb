
from amazon.utils.genlog import logger

first_item = lambda v : v[ 0 ] if v else None

def xpath( selector, path_str ):
    return selector.xpath( path_str )

def first_item_xpath( selector, path_str ):
    return first_item( xpath( selector, path_str ) )
f_xpath = first_item_xpath

def xpath_extract( selector, path_str ):
    return selector.xpath( path_str ).extract()

def first_item_xpath_extract( selector, path_str ):
    return first_item( xpath_extract( selector, path_str ) )
fx_extract = first_item_xpath_extract


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

def safe_with_log( logger ):
    def _safe( func ):
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

    return _safe

def escape(v):

    if type(v) == type(u''):
        return v.encode('utf8')

    return v
