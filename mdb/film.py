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
        print(elem.text_content())
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

    def save_movie(self):
        id = db.query_value('select id from mdb.movie where id = %s', [self.id])
        if id is None:
            db.execute('insert into mdb.movie(id, title, alternative_title, year, slogan, length) '
                       'values (%s, %s, %s, %s, %s, %s)',
                       [self.id, self.title, self.alternative_title, self.year,
                        self.slogan, self.length])

    def get_cast(self):
        page = Downloader.get('http://www.kinopoisk.ru/film/%s/cast/' % self.id)
        html = fromstring(page)

        self.cast.clear()

        for anchor in html.xpath('//a'):
            role = anchor.get('name')
            if role is None:
                continue
            logger.warning(role)
            div = anchor.getnext()

            while div is not None:
                logger.warning('%s %s' % (div.tag, div.get('class')))
                div = div.getnext()
                if div is None or div.tag != 'div':
                    break
                if 'dub' not in div.get('class').split():
                    continue

                person = dict()

                name = div.xpath('.//div[@class="info"]//div[@class="name"]//a')[0]
                alternative_name = div.xpath('.//div[@class="info"]//div[@class="name"]//span[@class="gray"]')
                commentary = div.xpath('.//div[@class="info"]//div[@class="role"]')

                logger.warning(name.text_content())

                person['id'] = self.extract_person_id_from_url(name.get('href'))
                person['name'] = name.text_content()

                if alternative_name is not None:
                    logger.warning(alternative_name[0].text_content())
                    person['alternative_name'] = alternative_name[0].text_content()

                if commentary is not None:
                    commentary_str = commentary[0].text_content().replace('... ', '').strip()
                    logger.warning(commentary_str)
                    person['commentary'] = commentary_str if commentary_str != '' else None

                person['role'] = role

                self.cast.append(person)

    def save(self):
        self.save_persons()
        self.save_countries()
        self.save_movie()
        self.save_cast()

    def parse_info(self):
        for line in self.html.xpath('//table[contains(@class, "info")]//tr'):
            info_type = line.xpath('.//td[@class="type"]')[0]
            info_type_str = info_type.text_content()
            print('Type: %s' % info_type_str)

            second_column = line.xpath('.//td[2]')[0]

            if info_type_str == u'страна':
                for country in self.parse_countries(second_column):
                    print(country)
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

    def parse(self):
        self.parse_title()
        self.parse_info()
        self.get_cast()
        print(self.cast)
