#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pymysql
#import easysqllite as sql

class simpleclient( object ):

    dbargsort = ( 'host', 'port', 'user', 'passwd', 'db', )

    def __init__( self, db ):

        db_tmp = db.copy()

        for item in db_tmp.keys():
            if item not in self.dbargsort:
                db_tmp.pop( item )

        self.conn = pymysql.connect( **db_tmp )
        #self.edb = sql.Database(db)

    def simplequery( self, query ):

        cur = self.conn.cursor()
        cur.execute( query )
        dsc = cur.description
        dsc = [ d[0] for d in dsc ]

        rst = cur.fetchall()
        cur.close()

        return [ dict( zip( dsc, r ) ) for r in rst ]
