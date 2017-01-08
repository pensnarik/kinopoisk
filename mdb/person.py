# -*- encoding: utf-8 -*-

import re
import logging

from lxml.html import fromstring

from mdb.db import Database
from mdb.http import Downloader
from mdb.helpers import get_date

db = Database.Instance()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Person(object):

    base = 'https://www.kinopoisk.ru'

    def __init__(self, id):
        self.id = id
        self.name = None
        self.alternative_name = None
        self.birth_date = None
        self.birth_place = None
        self.death_date = None
        self.death_place = None
        self.growth = None
        page = Downloader.get('%s/name/%s/' % (self.base, id))
        self.parse(page)

    def parse(self, page):
        self.html = fromstring(page)

        alternative_span = self.html.xpath('//span[@itemprop="alternateName"]')
        if len(alternative_span) > 0:
            self.alternative_name = alternative_span[0].text_content()

        for tr in self.html.xpath('//table[@class="info"]//tr'):
            td = tr.xpath('.//td[@class="type"]')[0]
            info_type = td.text_content()
            info = td.getnext().text_content()
            if info_type == u'дата рождения':
                self.birth_date = tr.xpath('.//td[@class="birth"]')[0].get("birthdate")
            elif info_type == u'место рождения':
                self.birth_place = info
            elif info_type == u'рост':
                m = re.search('(\d+)\.(\d+) м', info, re.UNICODE)
                if m is not None:
                    self.growth = int(m.group(1)) * 100 + int(m.group(2))
            elif info_type == u'дата смерти':
                logger.warning(info)
                m = re.search('^(.+)•', info)
                if m is None:
                    date = get_date(info.strip()).get('date')
                else:
                    date = get_date(m.group(1).strip()).get('date')
                logger.warning('date = %s' % date)
                self.death_date = date
            elif info_type == u'место смерти':
                self.death_place = info

    def is_exists(self):
        return db.query_value('select count(*) from mdb.person where id = %s', [self.id]) > 0

    def save(self):
        if self.is_exists() is True:
            db.execute('update mdb.person set alternative_name = %s, '
                       'birth_date = %s, birth_place = %s, growth = %s, '
                       'death_date = %s, death_place = %s '
                       'where id = %s', [self.alternative_name, self.birth_date,
                                         self.birth_place, self.growth,
                                         self.death_date, self.death_place, self.id])
        else:
            db.execute('insert into mdb.person(id, name, alternative_name, birth_date, birth_place, '
                       'growth, death_date, death_place) '
                       'values (%s, %s, %s, %s, %s, %s, %s, %s)',
                       [self.id, self.name, self.alternative_name, self.birth_date,
                        self.birth_place, self.growth, self.death_date, self.death_place])
