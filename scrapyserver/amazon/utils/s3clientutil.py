import httplib

import s3client

def authedclient():

    h = client( 'earthpics',
                'SINA0000001001K26C1N',
                '06bc6c92b37c83befcffd1161712aa2a815855fd' )
    h.need_auth = True

    return h

def client( project, accesskey, secretkey ):

    return s3client.S3( accesskey, secretkey, project )

def get_http_resp_get_file( s3client, key, query = None, headers = None ):

    verb = 'GET'
    uri = s3client._get_uri( verb, key, query_string = query, requst_header = headers )
    resp = s3client._requst( verb, uri, headers or {} )

    if resp.status != httplib.OK:
        raise s3client.S3HTTPCodeError, s3client._resp_format( resp )

    return resp

def get_http_conn_put_file( s3client, key, query = None, headers = None ):

    verb = 'PUT'
    uri = s3client._get_uri( verb, key, query_string = query, requst_header = headers )
    header = s3client._fix_requst_header( verb, headers or {} )

    conn = s3client._http_handle()
    conn.putrequest( verb, uri )
    for k in header:
        conn.putheader( k, header[ k ] )
    conn.endheaders()

    return conn

def put_file_from_socket( s3client, key, httpresp, query = None, headers = None ):

    resp_headers = dict( httpresp.getheaders() )

    send_headers = {}
    send_headers[ 'Content-Length' ] = resp_headers.get( 'content-length' ) or '0'
    if 'content-type' in resp_headers:
        send_headers[ 'Content-Type' ] = resp_headers[ 'content-type' ]

    send_headers.update( headers or {} )

    conn = get_http_conn_put_file( s3client, key, query, send_headers )

    while True:
        data = httpresp.read( s3client.S3.CHUNK )
        if data == '':
            break
        conn.send( data )

    resp = conn.getresponse()

    if resp.status != httplib.OK:
        raise s3client.S3HTTPCodeError, s3client._resp_format( resp )

    return s3client._resp_format( resp )

def put_file_from_url( s3client, key, url, query = None, headers = None ):

    is_https = False
    if url.startswith( 'http://' ):
        url = url[ len( 'http://' ): ]
    elif url.startswith( 'https://' ):
        url = url[ len( 'https://' ): ]
        is_https = True

    host_uri = url.split( '/', 1 )
    host = host_uri[ 0 ]
    uri = '/'
    if len( host_uri ) == 2:
        uri = '/' + host_uri[ 1 ]

    if is_https:
        h = httplib.HTTPSConnection( host, 443, timeout = 60 )
    else:
        h = httplib.HTTPConnection( host, 80, timeout = 30 )

    h.putrequest( 'GET', uri )
    h.endheaders()

    resp = h.getresponse()

    if resp.status != httplib.OK:
        raise httplib.HTTPException, 'read from %s, response code: %d' % ( url, resp.status, )

    return put_file_from_socket( s3client, key, resp, query, headers )

