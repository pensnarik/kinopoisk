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
        self.buffer = buffer
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
        self.rating_critics = None
        self.age_restriction = None
        self.premieres = list()
        self.world_premiere = None
        self.dates = list()
        self.boxes = list()
        self.parse()
        logger.info(self.premieres)

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
            self.countries.append({'id': id, 'name': name})

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
                       'directors, scenario, operators, composers, producers, arts, editors, '
                       'age_restriction, countries, rating_critics, world_premiere) '
                       'values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
                       '%s, %s, %s, %s)',
                       [self.id, self.title, self.alternative_title, self.year,
                        self.slogan, self.length, self.get_array_of_id(self.genres),
                        self.rating_kinopoisk, self.rating_imdb,
                        self.get_persons_by_role('director'), self.get_persons_by_role('writer'),
                        self.get_persons_by_role('operator'), self.get_persons_by_role('composer'),
                        self.get_persons_by_role('producer'), self.get_persons_by_role('design'),
                        self.get_persons_by_role('editor'), self.age_restriction,
                        self.get_array_of_id(self.countries), self.rating_critics,
                        self.world_premiere])
        else:
            db.execute('update mdb.movie set title = %s, alternative_title = %s, year = %s, '
                       'slogan = %s, length = %s, genres = %s, rating_kinopoisk = %s, '
                       'rating_imdb = %s, directors = %s, scenario = %s, '
                       'operators = %s, composers = %s, producers = %s, arts = %s, '
                       'editors = %s, age_restriction = %s, countries = %s, rating_critics = %s, '
                       'world_premiere = %s '
                       'where id = %s',
                       [self.title, self.alternative_title, self.year, self.slogan,
                        self.length, self.get_array_of_id(self.genres),
                        self.rating_kinopoisk, self.rating_imdb,
                        self.get_persons_by_role('director'), self.get_persons_by_role('writer'),
                        self.get_persons_by_role('operator'), self.get_persons_by_role('composer'),
                        self.get_persons_by_role('producer'), self.get_persons_by_role('design'),
                        self.get_persons_by_role('editor'), self.age_restriction,
                        self.get_array_of_id(self.countries), self.rating_critics,
                        self.world_premiere,
                        self.id])

    def get_cast(self):
        page = Downloader.get('https://www.kinopoisk.ru/film/%s/cast/' % self.id)
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

        critics_rating = dict()
        critics = self.html.xpath('//div[contains(@class, "criticsRating")]//div[@class="star"]')

        if critics is not None and len(critics) > 0:
            critics_rating['rating_system'] = 'critics'
            critics_rating['rating'] = float(critics[0].text_content())
            critics_rating['vote_count'] = None

            self.ratings.append(critics_rating)
            self.rating_critics = critics_rating['rating']

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

    def get_age_restriction(self, elem):
        self.age_restriction = elem.text_content().strip()

    def get_premiere_date(self, date_as_russian_text):
        month_mapping_d = {u'января': 1, u'февраля': 2, u'марта': 3, u'апреля': 4, u'мая': 5,
                           u'июня': 6, u'июля': 7, u'августа': 8, u'сентября': 9, u'октября': 10,
                           u'ноября': 11, u'декабря': 12}
        month_mapping_m = {u'январь': 1, u'февраль': 2, u'март': 3, u'апрель': 4, u'май': 5, u'июнь': 6,
                           u'июль': 7, u'август': 8, u'сентябрь': 9, u'октябрь': 10, u'ноябрь': 11,
                           u'декабрь': 12}
        data = date_as_russian_text.split(' ')
        if len(data) == 3:
            # Bug with https://www.kinopoisk.ru/film/224679/dates/
            if data[0] == '0':
                data[0] = '1'
            return {'precision': 'd',
                    'date': '%s-%.02d-%.02d' % (data[2], month_mapping_d[data[1].lower()], int(data[0]))}
        elif len(data) == 2:
            return {'precision': 'm',
                    'date': '%s-%.02d-01' % (data[1], month_mapping_m[data[0].lower()])}
        elif len(data) == 1:
            return {'precision': 'y',
                    'date': '%s-01-01' % (data[0])}

    def get_premieres(self, elem):
        div = elem.xpath('.//div[@class="prem_ical"]')
        if div is not None and len(div) > 0:
            date = self.get_premiere_date(div[0].get('data-ical-date').strip())
            premiere = {'region': div[0].get('data-ical-type')}
            premiere.update(date)
            self.premieres.append(premiere)
            if premiere['region'] == 'world':
                self.world_premiere = date['date']

    def save_premieres(self):
        for premiere in self.premieres:
            id = db.query_value('select id from mdb.premiere_date where movie_id = %s and '
                                'region = %s', [self.id, premiere['region']])
            if id is None:
                db.execute('insert into mdb.premiere_date (movie_id, region, premiere_date, '
                           'precision) values (%s, %s, %s, %s)',
                           [self.id, premiere['region'], premiere['date'], premiere['precision']])

    def get_dates(self):
        page = Downloader.get('https://www.kinopoisk.ru/film/%s/dates/' % self.id)
        html = fromstring(page)
        for div in html.xpath('//table//tr//div[contains(@class, "flag")]'):
            td_date = div.getparent().getnext()
            td_country = td_date.getnext().xpath('.//a[contains(@class, "all")]')
            td_small = td_date.getnext().xpath('.//small')
            td_count = td_date.getnext().getnext().xpath('.//small')

            date = self.get_premiere_date(td_date[0].text_content().strip())
            country = td_country[0].text_content()
            country_id = self.extract_country_id_from_url(td_country[0].get('href'))
            small = td_small[0].text_content().strip()
            m = re.search(u'(.+)чел.', td_count[0].text_content(), re.UNICODE)

            try:
                count = re.sub('[^\d]', '', m.group(1))
                count = int(count)
            except (AttributeError, ValueError):
                count = None

            if country_id not in [i['id'] for i in self.countries]:
                self.countries.append({'id': country_id, 'name': country})
            self.dates.append({'date': date, 'country_id': country_id,
                               'commentary': small, 'viewers': count})

    def save_dates(self):
        db.execute('delete from mdb.dates where movie_id = %s', [self.id])
        for date in self.dates:
            db.execute('insert into mdb.dates (movie_id, country_id, premiere_date, '
                       'premiere_precision, viewers, commentary) '
                       'values (%s, %s, %s, %s, %s, %s)',
                       [self.id, date['country_id'], date['date']['date'],
                        date['date']['precision'], date['viewers'], date['commentary']])

    def get_boxes(self):
        """
        Информация о кассовых сборах и бюджете
        """
        logger.warning('Parsing boxes')
        page = Downloader.get('https://www.kinopoisk.ru/film/%s/box/' % self.id)
        html = fromstring(page)
        for div in html.xpath('//div[@style="width: 274px"]//table'):
            group = div.xpath('.//tr//td')[0].text_content()
            logger.warning(group)
            for b in div.xpath('.//td[@colspan="2"]//b'):
                title = b.text_content().replace(':', '')
                if title == group:
                    continue
                next_tr = b.getparent().getparent().getnext().xpath('.//td')[0]
                value = re.sub('[^\d]', '', next_tr.text_content().strip(), re.UNICODE)
                logger.warning('"%s" : "%s"' % (title, value,))
                if value != '':
                    self.boxes.append({'category': group, 'item': title, 'value': value})

    def save_boxes(self):
        db.execute('delete from mdb.movie_boxes where movie_id = %s', [self.id])
        for box in self.boxes:
            db.execute('insert into mdb.movie_boxes(movie_id, category, item, value) '
                       'values (%s, %s, %s, %s)',
                       [self.id, box['category'], box['item'], box['value']])

    def save(self):
        self.save_persons()
        self.save_countries()
        self.save_genres()
        self.save_movie()
        self.save_premieres()
        self.save_cast()
        self.save_ratings()
        self.save_dates()
        self.save_boxes()

    def parse_info(self):
        for line in self.html.xpath('//table[contains(@class, "info")]//tr'):
            info_type = line.xpath('.//td[@class="type"]')[0]
            info_type_str = info_type.text_content()

            second_column = line.xpath('.//td[2]')[0]

            if info_type_str == u'страна':
                self.parse_countries(second_column)
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
            elif info_type_str == u'возраст':
                self.get_age_restriction(second_column)
            elif info_type_str.startswith(u'премьера'):
                self.get_premieres(second_column)

    def parse(self):
        self.parse_title()
        self.parse_info()
        self.get_cast()
        self.get_ratings()
        self.get_dates()
        if '/film/%s/box/' % self.id in self.buffer:
            self.get_boxes()
        else:
            logger.warning('There is not boxes information for this movie')
