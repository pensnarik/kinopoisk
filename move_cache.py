#!/usr/bin/env python

import os
import hashlib
import shutil

import config
from mdb.db import Database

db = Database.Instance()


class App():
    cache_path = '/home/mutex/data/cache/kinopoisk/cache'

    def __init__(self):
        db.connect(config.dsn)

    def get_year_mapping(self):
        self.mapping = dict()
        for movie in db.query_dict('select id, year from mdb.movie'):
            self.mapping[movie['id']] = movie['year']

    def hashes(self, id):
        masks = ['https://www.kinopoisk.ru/film/%s/cast/',
                 'http://www.kinopoisk.ru/film/%s/cast/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/actor/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/design/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/writer/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/director/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/editor/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/voice/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/actor/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/producer/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/operator/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/producer_ussr/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/voice_director/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/translator/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/composer/',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/actor/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/design/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/writer/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/director/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/editor/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/voice/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/actor/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/producer/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/operator/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/producer_ussr/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/voice_director/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/translator/:10000',
                 'https://www.kinopoisk.ru/film/%s/cast/who_is/composer/:10000',
                 'https://www.kinopoisk.ru/film/%s/dates/',
                 'https://www.kinopoisk.ru/film/%s/box/',
                 'https://www.kinopoisk.ru/film/%s/']
        for mask in masks:
            yield hashlib.md5((mask % id).encode('utf-8')).hexdigest()

    def run(self):
        self.get_year_mapping()
        for id in range(0, 1100000):
            for hash in self.hashes(id):
                filename = os.path.join(self.cache_path, hash)
                if os.path.exists(filename):
                    if id in self.mapping:
                        new_path = os.path.join(self.cache_path, str(self.mapping[id]), hash)
                        if not os.path.isdir(os.path.join(self.cache_path, str(self.mapping[id]))):
                            os.mkdir(os.path.join(self.cache_path, str(self.mapping[id])))
                        print('%s -> %s' % (filename, new_path))
                        shutil.move(filename, new_path)
        for year in range(1890, 2018):
            print(year)
            for page in range(1, 1000):
                hash = hashlib.md5(('https://www.kinopoisk.ru/lists/ord/name/m_act[year]/%s/m_act[all]/ok/page/%s/' %
                                    (year, page)).encode('utf-8')).hexdigest()
                filename = os.path.join(self.cache_path, hash)
                if os.path.exists(filename):
                    new_path = os.path.join(self.cache_path, str(year), hash)
                    print('%s -> %s' % (filename, new_path))
                    shutil.move(filename, new_path)


if __name__ == '__main__':
    app = App()
    app.run()
