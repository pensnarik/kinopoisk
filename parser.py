#!/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
import sys
import logging
import argparse

from lxml.html import fromstring

import config
from mdb.film import Film
from mdb.db import Database
from mdb.http import Downloader

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

db = Database.Instance()


class App():

    base = 'https://www.kinopoisk.ru'

    def __init__(self):
        parser = argparse.ArgumentParser(description='Generate SQL statemets to create '
                                                     'attribute tables.')
        parser.add_argument('--year', type=str, help='Year to process', required=True)
        self.args = parser.parse_args()
        # Initialization of the cache
        if not os.path.exists(Downloader.get_cache_path()):
            os.mkdir(Downloader.get_cache_path())
        # Initialization of database connection
        db.connect(config.dsn)

    def get_rating_history(self, film_id):
        """
        /graph_data/variation_data_film/243/variation_data_film_810243.xml? + Math.random(0,10000)
        """
        return

    def get_pages_count(self, year):
        page = Downloader.get(self.get_url_for_year(year))
        html = fromstring(page)
        a = html.xpath('//ul[@class="list"]//li[@class="arr"][last()]//a')
        if a is None or len(a) == 0:
            return 1
        m = re.search('/page/(\d+)/', a.get('href'))
        return int(m.group(1))

    def get_url_for_year(self, year, page=1):
        return '%s/lists/ord/name/m_act[year]/%s/m_act[all]/ok/page/%s/' % (self.base, year, page,)

    def extract_id_from_url(self, url):
        m = re.search('/(\d+)/$', url)
        return int(m.group(1))

    def get_films_from_page(self, url):
        page = Downloader.get(url)
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
        page = Downloader.get(self.get_film_url(film_id))
        film = Film(film_id, page)
        logger.warning('%s (%s)' % (film.title, film.alternative_title,))
        return film

    def get_year(self, year):
        for page_number in range(1, self.get_pages_count(year) + 1):
            print("Processing page %s" % page_number)
            for id, title, href in self.get_films_from_page(self.get_url_for_year(year, page_number)):
                logger.info('%s | %s | %s' % (id, title, href,))
                f = self.get_film(id)
                f.save()

    def run(self):
        self.get_year(self.args.year)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO, stream=sys.stdout)
    app = App()
    app.run()
