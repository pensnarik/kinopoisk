#! -*- encoding: utf-8 -*-

import re

from lxml.html import fromstring
from mdb.helpers import unhtml
from mdb.db import Database

db = Database.Instance()


class Film(object):

    def __init__(self, id, buffer):
        self.html = fromstring(buffer)
        self.id = id
        self.countries = list()
        self.slogan = None
        self.persons = list()
        self.length = None
        self.year = None
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

    def save_persons(self):
        for person in self.persons:
            id = db.query_value('select id from mdb.person where id = %s', [person['id']])
            if id is None:
                db.execute('insert into mdb.person (id, name) values (%s, %s)', [person['id'],
                                                                                 person['name']])

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

    def save(self):
        self.save_persons()
        self.save_countries()
        self.save_movie()

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
