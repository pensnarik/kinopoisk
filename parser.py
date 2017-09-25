#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import re
import sys
import logging
import argparse
from socket import gethostname
from datetime import date

from lxml.html import fromstring

import config
from mdb.film import Film
from mdb.person import Person
from mdb.db import Database
from mdb.http import Downloader

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

db = Database.Instance()


class App():

    base = 'https://www.kinopoisk.ru'
    total_count = None
    current_page = None
    total_pages = None

    def __init__(self):
        parser = argparse.ArgumentParser(description='kinopoisk.ru parser')
        parser.add_argument('--year', type=int, help='Year to process')
        parser.add_argument('--hostname', type=str, help='Hostname', required=False,
                            default=gethostname())
        parser.add_argument('--film-id', type=int, help='Film ID')
        parser.add_argument('--sleep-time', type=int, help='Max sleep time between requests',
                            default=20)
        parser.add_argument('--total', required=False, default=False, action='store_true')
        parser.add_argument('--read-only', required=False, default=False, action='store_true')
        parser.add_argument('--cache-path', required=False, default='.', type=str)
        parser.add_argument('--update', required=False, default=False, action='store_true')
        parser.add_argument('--start-page', required=False, default=1, type=int)
        parser.add_argument('--persons', required=False, default=False, action='store_true')
        parser.add_argument('--from-id', required=False, default=1, type=int)
        parser.add_argument('--to-id', required=False, default=None)
        self.args = parser.parse_args()
        config.cache_path = self.args.cache_path
        # Initialization of the cache
        Downloader.init_cache()
        # Initialization of database connection
        db.connect(config.dsn)
        config.sleep_time = self.args.sleep_time
        if self.args.year is not None:
            self.set_year(self.args.year)

    def set_year(self, year):
        config.year = year

    def get_rating_history(self, film_id):
        """
        /graph_data/variation_data_film/243/variation_data_film_810243.xml? + Math.random(0,10000)
        """
        return

    def get_pages_count(self, year, force_download=False):
        logger.info('Getting pages count for year %s' % year)
        page = Downloader.get(self.get_url_for_year(year), force_download=force_download)
        html = fromstring(page)
        a = html.xpath('//ul[@class="list"]//li[@class="arr"][last()]//a')
        if a is None or len(a) == 0:
            pages_count = 1
        else:
            m = re.search('/page/(\d+)/', a[0].get('href'))
            pages_count = int(m.group(1))

        h1 = html.xpath('//h1[@class="level2"]//span[@style="color: #777"]')
        if h1 is not None and len(h1) > 0:
            self.total_count = int(re.sub('[^\d]', '', h1[0].text_content()))
        else:
            raise Exception('Could not get total records count!')

        logger.info('Got total_count = %s' % self.total_count)
        self.total_pages = pages_count
        return pages_count

    def get_url_for_year(self, year, page=1):
        return '%s/lists/ord/name/m_act[year]/%s/m_act[all]/ok/page/%s/' % (self.base, year, page,)

    def extract_id_from_url(self, url):
        if re.match('^/film/(\d+)/$', url):
            # Old URL format
            # /film/1049041/
            m = re.search('^/film/(\d+)/$', url)
            return int(m.group(1))
        else:
            # New URL format
            # /film/pyewacket-2017-1004054/
            m = re.search('-(\d+)/$', url)
            return int(m.group(1))

    def get_films_from_page(self, url, force_download=False):
        page = Downloader.get(url, force_download=force_download)
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

        logger.info('%s (%s) | %s' % (film.title, film.alternative_title, film.year,))
        return film

    def get_current_count(self):
        return db.query_value('select count(*) from mdb.movie where year = %s' % config.year)

    def update_stat(self, last_movie_id):
        id = db.query_value('select id from mdb.stat where year = %s', [config.year])
        if id is None:
            db.execute('insert into mdb.stat (year, done_count, total_count, hostname, '
                       'last_movie_id, current_page, total_pages) '
                       'values (%s, %s, %s, %s, %s, %s, %s)',
                       [config.year, self.get_current_count(), self.total_count,
                        self.args.hostname, last_movie_id, self.current_page,
                        self.total_pages])
        else:
            db.execute('update mdb.stat set done_count = %s, total_count = %s, hostname = %s, '
                       'last_update_time = current_timestamp, last_movie_id = %s, '
                       'current_page = %s, total_pages = %s '
                       'where year = %s',
                       [self.get_current_count(), self.total_count, self.args.hostname,
                        last_movie_id, self.current_page, self.total_pages,
                        config.year])

    def update_total(self):
        id = db.query_value('select id from mdb.stat where year = %s', [config.year])
        if id is None:
            db.execute('insert into mdb.stat (year, done_count, total_count, hostname, '
                       'last_movie_id, total_pages) '
                       'values (%s, %s, %s, %s, %s, %s)',
                       [config.year, 0, self.total_count, None, None, self.total_pages])

    def log_error(self, movie_id, message):
        """
        TODO: movie_id -> object_id
        """
        logger.error('Could not parse movie %s: "%s"' % (movie_id, message,))
        db.execute('insert into mdb.error(hostname, movie_id, message) '
                   'values (%s, %s, %s)', [self.args.hostname, movie_id, message])

    def is_film_exists(self, movie_id):
        return db.query_value('select count(*) from mdb.movie where id = %s', [movie_id]) > 0

    def get_year(self, year, update_mode=False):
        logger.info('======= Processing year %s =======' % year)
        for page_number in range(self.args.start_page,
                                 self.get_pages_count(year, force_download=update_mode) + 1):
            self.current_page = page_number
            logger.info("Processing page %s" % page_number)
            for id, title, href in self.get_films_from_page(self.get_url_for_year(year,
                                                                                  page_number),
                                                            force_download=update_mode):
                if update_mode and self.is_film_exists(id) is True:
                    continue
                if update_mode and self.is_film_exists(id) is False:
                    logger.warning('New film found')

                logger.info('%s | %s | %s' % (id, title, href,))

                try:
                    f = self.get_film(id)
                    if self.args.read_only is False:
                        f.save()
                except Exception as e:
                    self.log_error(id, str(e))
                logger.warning('%s from %s' % (self.get_current_count(), self.total_count,))
                if self.args.read_only is False:
                    self.update_stat(id)
        # После получения всех страниц года нужно сбросить счётчик страниц,
        # чтобы новый год начинать извлекать всегда с первой страницы
        self.args.start_page = 1

    def update_persons(self):
        query = "select id from mdb.person " \
                " where id between %s and coalesce(%s, 999999999) " \
                "   and parsed_extra = false " \
                " order by id"
        for person in db.query_dict(query, [self.args.from_id, self.args.to_id]):
            logger.info('Parsing person with ID = %s', person['id'])
            try:
                person = Person(person['id'])
                person.save()
            except Exception as e:
                logger.error('Could not process person %s' % person['id'])
                self.log_error(person['id'], 'Could not process person: %s' % str(e))

    def run(self):
        if self.args.persons is True:
            self.update_persons()
            return
        if self.args.total is True:
            logger.warning('======= Updating total stat =======')
            for year in range(1890, date.today().year + 1):
                logger.warning('Year %s' % year)
                config.year = year
                self.get_pages_count(year)
                self.update_total()
            return
        elif self.args.update is True:
            logger.warning('Running in UPDATE mode')
        elif self.args.film_id is not None:
            logger.warning('======= Processing film %s =======' % self.args.film_id)
            f = self.get_film(self.args.film_id)
            f.save()
            sys.exit(0)

        while config.year <= date.today().year + 1:
            self.get_year(config.year, update_mode=self.args.update)
            self.set_year(config.year + 1)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO, stream=sys.stdout)
    app = App()
    app.run()
