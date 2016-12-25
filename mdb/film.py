#! -*- encoding: utf-8 -*-

import re
import logging

from lxml.html import fromstring
from mdb.helpers import unhtml
from mdb.db import Database
from mdb.http import Downloader

db = Database.Instance()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Film(object):

    def __init__(self, id, buffer):
        self.html = fromstring(buffer)
        self.id = id
        self.countries = list()
        self.slogan = None
        self.persons = list()
        self.length = None
        self.year = None
        self.cast = list()
        self.ratings = list()
        self.genres = list()
        self.rating_kinopoisk = None
        self.rating_imdb = None
        self.parse()

    def parse_title(self):
        h1 = self.html.xpath('//h1[@class="moviename-big"]')
        self.title = unhtml(h1[0].text_content())
        alternative = self.html.xpath('//span[@itemprop="alternativeHeadline"]')
        if alternative is not None:
            self.alternative_title = alternative[0].text_content()

    def extract_country_id_from_url(self, url):
        m = re.search('/(\d+)/$', url)
        return int(m.group(1))

    def extract_person_id_from_url(self, url):
        m = re.search('/name/(\d+)/$', url)
        return int(m.group(1))

    def save_country(self, id, name):
        exists = db.query_value('select id from mdb.country where id = %s', [id])
        if exists is None:
            db.execute('insert into mdb.country(id, name) values (%s, %s)', [id, name])

    def parse_countries(self, elem):
        for a in elem.xpath('.//a'):
            href = a.get('href')
            name = a.text_content()
            id = self.extract_country_id_from_url(href)
            yield {'id': id, 'name': name}

    def parse_slogan(self, elem):
        return unhtml(elem.text_content())

    def update_person_array(self, role, elem):
        for item in elem.xpath('.//a'):
            href = item.get('href')
            m = re.search('/name/(\d+)/$', href)
            if m is None:
                continue
            id = int(m.group(1))
            name = item.text_content()
            self.persons.append({'id': id, 'name': name, 'role': role})

    def parse_length(self, elem):
        m = re.search(u'(\d+) мин', elem.text_content(), re.UNICODE)
        if m is not None:
            return int(m.group(1))
        else:
            return None

    def parse_year(self, elem):
        m = re.search('(\d{4})', elem.text_content().strip())
        if m is not None:
            self.year = int(m.group(1))
        else:
            return None

    def save_persons_in_movie(self):
        # Depricated
        db.execute('delete from mdb.person_in_movie where movie_id = %s', [self.id])
        for person in self.persons:
            db.execute('insert into mdb.person_in_movie(movie_id, person_id, role) '
                       'values (%s, %s, %s)', [self.id, person['id'], person['role']])

    def save_persons(self):
        for person in self.cast:
            id = db.query_value('select id from mdb.person where id = %s', [person['id']])
            if id is None:
                db.execute('insert into mdb.person (id, name, alternative_name) '
                           'values (%s, %s, %s)', [person['id'], person['name'],
                                                   person['alternative_name']])

    def save_cast(self):
        db.execute('delete from mdb.person_in_movie where movie_id = %s', [self.id])
        for person in self.cast:
            db.execute('insert into mdb.person_in_movie(movie_id, person_id, role, commentary) '
                       'values (%s, %s, %s, %s)', [self.id, person['id'], person['role'],
                                                   person['commentary']])

    def save_countries(self):
        for country in self.countries:
            self.save_country(country['id'], country['name'])

    def get_array_of_id(self, for_list):
        return [int(i['id']) for i in for_list]

    def save_movie(self):
        id = db.query_value('select id from mdb.movie where id = %s', [self.id])
        if id is None:
            db.execute('insert into mdb.movie(id, title, alternative_title, year, slogan, '
                       'length, genres, rating_kinopoisk, rating_imdb, '
                       'directors, scenario, operators, composers, producers, arts, editors) '
                       'values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       [self.id, self.title, self.alternative_title, self.year,
                        self.slogan, self.length, self.get_array_of_id(self.genres),
                        self.rating_kinopoisk, self.rating_imdb,
                        self.get_persons_by_role('director'), self.get_persons_by_role('writer'),
                        self.get_persons_by_role('operator'), self.get_persons_by_role('composer'),
                        self.get_persons_by_role('producer'), self.get_persons_by_role('design'),
                        self.get_persons_by_role('editor')])
        else:
            db.execute('update mdb.movie set title = %s, alternative_title = %s, year = %s, '
                       'slogan = %s, length = %s, genres = %s, rating_kinopoisk = %s, '
                       'rating_imdb = %s, directors = %s, scenario = %s, '
                       'operators = %s, composers = %s, producers = %s, arts = %s, '
                       'editors = %s '
                       'where id = %s',
                       [self.title, self.alternative_title, self.year, self.slogan,
                        self.length, self.get_array_of_id(self.genres),
                        self.rating_kinopoisk, self.rating_imdb,
                        self.get_persons_by_role('director'), self.get_persons_by_role('writer'),
                        self.get_persons_by_role('operator'), self.get_persons_by_role('composer'),
                        self.get_persons_by_role('producer'), self.get_persons_by_role('design'),
                        self.get_persons_by_role('editor'),
                        self.id])

    def get_cast(self):
        page = Downloader.get('http://www.kinopoisk.ru/film/%s/cast/' % self.id)
        html = fromstring(page)

        self.cast = list()

        for anchor in html.xpath('//a'):
            role = anchor.get('name')
            if role is None:
                continue
            div = anchor.getnext()

            while div is not None:
                div = div.getnext()
                if div is None or div.tag != 'div':
                    break
                if 'dub' not in div.get('class').split():
                    continue

                person = dict()

                name = div.xpath('.//div[@class="info"]//div[@class="name"]//a')[0]
                alternative_name = div.xpath('.//div[@class="info"]//div[@class="name"]//span[@class="gray"]')
                commentary = div.xpath('.//div[@class="info"]//div[@class="role"]')

                person['id'] = self.extract_person_id_from_url(name.get('href'))
                person['name'] = name.text_content()

                if alternative_name is not None:
                    person['alternative_name'] = alternative_name[0].text_content()

                if commentary is not None:
                    commentary_str = commentary[0].text_content().replace('... ', '').strip()
                    person['commentary'] = commentary_str if commentary_str != '' else None

                person['role'] = role

                self.cast.append(person)

    def get_ratings(self):
        kinopoisk = dict()

        kinopoisk_rating = self.html.xpath('//span[@class="rating_ball"]')
        kinopoisk_count = self.html.xpath('//span[@class="ratingCount"]')

        if kinopoisk_rating is not None and len(kinopoisk_rating) > 0:
            kinopoisk['rating_system'] = 'kinopoisk'
            kinopoisk['rating'] = float(kinopoisk_rating[0].text_content())
            kinopoisk['vote_count'] = int(re.sub('[^\d]', '', kinopoisk_count[0].text_content().replace('&nbsp;', ''), re.UNICODE))
            self.ratings.append(kinopoisk)
            self.rating_kinopoisk = kinopoisk['rating']

        imdb = dict()

        for div in self.html.xpath('//div[@id="block_rating"]//div'):
            if div.text_content().startswith('IMDb:'):
                imdb['rating_system'] = 'imdb'
                m = re.search('^IMDb: ([\d\.]+) \(([^)]+)\)', div.text_content())
                imdb['rating'] = float(m.group(1))
                imdb['vote_count'] = int(m.group(2).replace(' ', ''))

                self.ratings.append(imdb)
                self.rating_imdb = imdb['rating']
                break

    def save_ratings(self):
        for rating in self.ratings:
            id = db.query_value('select id from mdb.movie_rating where movie_id = %s and '
                                'rating_system = %s', [self.id, rating['rating_system']])
            if id is None:
                db.execute('insert into mdb.movie_rating (movie_id, rating_system, rating, '
                           'vote_count) values (%s, %s, %s, %s)',
                           [self.id, rating['rating_system'], rating['rating'],
                            rating['vote_count']])
            else:
                db.execute('update mdb.movie_rating set rating = %s, vote_count = %s '
                           'where movie_id = %s and rating_system = %s',
                           [rating['rating'], rating['vote_count'], self.id,
                            rating['rating_system']])

    def extract_genre_id_from_url(self, url):
        m = re.search('/(\d+)/$', url)
        return int(m.group(1))

    def get_genres(self, second_column):
        for a in second_column.xpath('.//a'):
            if a.get('href').startswith(u'/lists/m_act'):
                id = self.extract_genre_id_from_url(a.get('href'))
                name = a.text_content()
                self.genres.append({'id': id, 'name': name})
        logger.info(self.genres)

    def save_genres(self):
        for genre in self.genres:
            id = db.query_value('select id from mdb.genre where id = %s', [genre['id']])
            if id is None:
                db.execute('insert into mdb.genre(id, name) values (%s, %s)',
                           [genre['id'], genre['name']])

    def get_persons_by_role(self, role):
        return [int(i['id']) for i in self.cast if i['role'] == role]

    def save(self):
        self.save_persons()
        self.save_countries()
        self.save_genres()
        self.save_movie()
        self.save_cast()
        self.save_ratings()

    def parse_info(self):
        for line in self.html.xpath('//table[contains(@class, "info")]//tr'):
            info_type = line.xpath('.//td[@class="type"]')[0]
            info_type_str = info_type.text_content()

            second_column = line.xpath('.//td[2]')[0]

            if info_type_str == u'страна':
                for country in self.parse_countries(second_column):
                    self.countries.append(country)
            elif info_type_str == u'слоган':
                self.slogan = self.parse_slogan(second_column)

            elif info_type_str in [u'режиссер', u'сценарий', u'продюсер', u'художник', u'монтаж',
                                   u'композитор', u'оператор']:
                self.update_person_array(info_type_str, second_column)
            elif info_type_str == u'время':
                self.length = self.parse_length(second_column)
            elif info_type_str == u'год':
                self.parse_year(second_column)
            elif info_type_str == u'жанр':
                self.get_genres(second_column)

    def parse(self):
        self.parse_title()
        self.parse_info()
        self.get_cast()
        self.get_ratings()

