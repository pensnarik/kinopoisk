#!/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
import sys
import logging
import hashlib
import codecs

from lxml.html import fromstring
import requests

import config
from mdb.film import Film
from mdb.db import Database

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

db = Database.Instance()


class App():

    base = 'https://www.kinopoisk.ru'

    def __init__(self):
        # Initialization of the cache
        if not os.path.exists(self.get_cache_path()):
            os.mkdir(self.get_cache_path())
        # Initialization of database connection
        db.connect(config.dsn)

    def get(self, url):
        if self.is_url_in_cache(url):
            logger.info('Reading %s from cache...' % url)
            return self.get_from_cache(url)
        else:
            logger.info('Downloading %s' % url)
            tries_left = 10
            response = None

            while tries_left > 0:
                try:
                    logger.info('Tries left: %s' % tries_left)
                    response = requests.get(url, timeout=5)
                    break
                except (ConnectionError, OSError):
                    tries_left = tries_left - 1

            if response.status_code == 200 and response is not None:
                self.write_to_cache(url, response.text)
                return response.text
            else:
                return None

    def get_from_cache(self, url):
        logger.info(self.get_cached_filename(url))
        if sys.version_info[0] >= 3:
            f = open(self.get_cached_filename(url), 'rt')
            data = f.read()
            f.close()
            return data
        else:
            with codecs.open(self.get_cached_filename(url), 'r', encoding='utf-8') as f:
                data = f.read()
            return data

    def write_to_cache(self, url, data):
        if sys.version_info[0] >= 3:
            f = open(self.get_cached_filename(url), 'wt')
            f.write(data)
            f.close()
        else:
            with codecs.open(self.get_cached_filename(url), 'w', encoding='utf-8') as f:
                f.write(data)

    def get_rating_history(self, film_id):
        """
        /graph_data/variation_data_film/243/variation_data_film_810243.xml? + Math.random(0,10000)
        """
        return

    def get_cache_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')

    def get_cached_filename(self, url):
        return os.path.join(self.get_cache_path(), hashlib.md5(url.encode('utf8')).hexdigest())

    def is_url_in_cache(self, url):
        return os.path.exists(self.get_cached_filename(url))

    def get_pages_count(self, year):
        page = self.get(self.get_url_for_year(year))
        html = fromstring(page)
        a = html.xpath('//ul[@class="list"]//li[@class="arr"][last()]//a')[0]
        print(a.get('href'))
        m = re.search('/page/(\d+)/', a.get('href'))
        return int(m.group(1))

    def get_url_for_year(self, year, page=1):
        return '%s/lists/ord/name/m_act[year]/%s/m_act[all]/ok/page/%s/' % (self.base, year, page,)

    def extract_id_from_url(self, url):
        m = re.search('/(\d+)/$', url)
        return int(m.group(1))

    def get_films_from_page(self, url):
        page = self.get(url)
        html = fromstring(page)
        for item in html.xpath('//div[contains(@class, "item")]//div[@class="name"]//a'):
            title = item.text_content()
            href = item.get('href')
            id = self.extract_id_from_url(href)
            yield (id, title, href)

    def get_film_url(self, film_id):
        return '%s/film/%s/' % (self.base, film_id,)

    def get_film(self, film_id):
        """
        Extracts all informarion about film
        """
        page = self.get(self.get_film_url(film_id))
        film = Film(film_id, page)
        print(film.title, film.alternative_title)
        print('Slogan: %s' % film.slogan)
        print('Persons: %s' % film.persons)
        print('Length: %s min' % film.length)
        return film

    def get_year(self, year):
        for page_number in range(1, self.get_pages_count(year) + 1):
            print("Processing page %s" % page_number)
            for id, title, href in self.get_films_from_page(self.get_url_for_year(year, page_number)):
                logger.info('%s | %s | %s' % (id, title, href,))
                f = self.get_film(id)
                f.save()

    def run(self):
        self.get_year(1975)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO, stream=sys.stdout)
    app = App()
    app.run()
