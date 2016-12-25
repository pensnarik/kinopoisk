# -*- encoding: utf-8 -*-

import sys
import os
import time
import hashlib
import logging
import requests
import codecs
import __main__
from random import randint

import mdb.helpers

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Downloader():
    """
    Реализует интерфейс для получения страниц сайта напрямую или через кеш
    """
    @staticmethod
    def get(url):
        if Downloader.is_url_in_cache(url):
            logger.info('Reading %s from cache...' % url)
            return Downloader.get_from_cache(url)
        else:
            logger.info('Downloading %s' % url)
            tries_left = 10
            response = None

            while tries_left > 0:
                try:
                    sleep_time = randint(1, 20)
                    logger.info('Sleeping %s, tries left: %s' % (sleep_time, tries_left))
                    time.sleep(sleep_time)
                    response = requests.get(url, timeout=5, headers=mdb.helpers.headers)
                    break
                except (ConnectionError, OSError):
                    tries_left = tries_left - 1

            if response.status_code == 200 and response is not None:
                Downloader.write_to_cache(url, response.text)
                return response.text
            else:
                return None

    @staticmethod
    def get_from_cache(url):
        logger.info(Downloader.get_cached_filename(url))
        if sys.version_info[0] >= 3:
            f = open(Downloader.get_cached_filename(url), 'rt')
            data = f.read()
            f.close()
            return data
        else:
            with codecs.open(Downloader.get_cached_filename(url), 'r', encoding='utf-8') as f:
                data = f.read()
            return data

    @staticmethod
    def write_to_cache(url, data):
        if sys.version_info[0] >= 3:
            f = open(Downloader.get_cached_filename(url), 'wt')
            f.write(data)
            f.close()
        else:
            with codecs.open(Downloader.get_cached_filename(url), 'w', encoding='utf-8') as f:
                f.write(data)

    @staticmethod
    def get_cache_path():
        return os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'cache')

    @staticmethod
    def get_cached_filename(url):
        return os.path.join(Downloader.get_cache_path(),
                            hashlib.md5(url.encode('utf8')).hexdigest())

    @staticmethod
    def is_url_in_cache(url):
        return os.path.exists(Downloader.get_cached_filename(url))
