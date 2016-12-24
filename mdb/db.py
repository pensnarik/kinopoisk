# -*- coding: utf-8 -*-

import psycopg2
import psycopg2.extensions
import psycopg2.extras
import logging

from mdb.singleton import Singleton

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)


@Singleton
class Database(object):

    def connect(self, conn):
        logger.info('Connecting to database')
        self.conn = psycopg2.connect(conn)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    def close(self):
        self.conn.close()

    def query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return data

    def query_dict(self, query, params=None):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        return [row for row in data]

    def query_value(self, query, params=None):
        result = self.query_dict(query, params)
        if result:
            return result[0][0]
        else:
            return None

    def execute(self, query, params):
        logger.info('SQL: %s' % query)
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        cursor.close()
        return
