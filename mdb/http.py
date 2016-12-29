# -*- encoding: utf-8 -*-

import sys
import os
import time
import hashlib
import logging
import requests
from requests.exceptions import ConnectionError, ReadTimeout
import codecs
import __main__
from random import randint

import mdb.helpers
import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GetPageError(Exception):
    pass


class Downloader():
    """
    Реализует интерфейс для получения страниц сайта напрямую или через кеш
    """
    @staticmethod
    def get(url, method='GET', salt=None, data=None):
        display_url = url if salt is None else '%s:%s' % (url, salt,)
        if Downloader.is_url_in_cache(url, salt):
            logger.info('Reading %s from cache...' % display_url)
            return Downloader.get_from_cache(url, salt)
        else:
            logger.info('Downloading %s' % display_url)
            tries_left = 100
            response = None

            while tries_left > 0:
                try:
                    sleep_time = randint(1, config.sleep_time)
                    logger.info('Sleeping %s, tries left: %s' % (sleep_time, tries_left))
                    time.sleep(sleep_time)

                    if method == 'GET':
                        response = requests.get(url, timeout=5, headers=mdb.helpers.headers)
                    elif method == 'POST':
                        response = requests.post(url, timeout=5, headers=mdb.helpers.headers,
                                                 data=data)
                    else:
                        raise Exception('Unknown method: %s' % method)

                    if 'captchaimg' in response.text:
                        raise GetPageError('Banned')
                    break
                except (ConnectionError, OSError, GetPageError, ReadTimeout):
                    tries_left = tries_left - 1
                    seconds_to_sleep = 100 * (100 - tries_left)
                    logger.warning('Will sleep %s seconds due to connection error' %
                                   seconds_to_sleep)
                    time.sleep(seconds_to_sleep)

            if response.status_code == 200 and response is not None:
                Downloader.write_to_cache(url, salt, response.text)
                return response.text
            else:
                return None

    @staticmethod
    def get_from_cache(url, salt):
        logger.info(Downloader.get_cached_filename(url, salt))
        if sys.version_info[0] >= 3:
            f = open(Downloader.get_cached_filename(url, salt), 'rt')
            data = f.read()
            f.close()
            return data
        else:
            with codecs.open(Downloader.get_cached_filename(url, salt), 'r', encoding='utf-8') as f:
                data = f.read()
            return data

    @staticmethod
    def write_to_cache(url, salt, data):
        if sys.version_info[0] >= 3:
            f = open(Downloader.get_cached_filename(url, salt), 'wt')
            f.write(data)
            f.close()
        else:
            with codecs.open(Downloader.get_cached_filename(url, salt), 'w', encoding='utf-8') as f:
                f.write(data)
        logger.info('Saved to cache as %s' % Downloader.get_cached_filename(url, salt))

    @staticmethod
    def get_cache_path():
        return os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'cache')

    @staticmethod
    def get_cached_filename(url, salt):
        if salt is not None:
            key = ('%s:%s' % (url, salt,)).encode('utf8')
        else:
            key = url.encode('utf8')

        return os.path.join(Downloader.get_cache_path(), hashlib.md5(key).hexdigest())

    @staticmethod
    def is_url_in_cache(url, salt):
        return os.path.exists(Downloader.get_cached_filename(url, salt))
