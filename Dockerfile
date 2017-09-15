FROM postgres:9.6

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python2.7 \
      "postgresql-contrib-$PG_MAJOR" \
      "postgresql-plpython-$PG_MAJOR"
RUN apt-get install -y --no-install-recommends wget
RUN apt-get clean \
 && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

COPY docker/docker-entrypoint-initdb.d /docker-entrypoint-initdb.d/
COPY db /db
WORKDIR /db/data
RUN wget --quiet http://parselab.ru/kinopoisk/data/mdb.person.sql.bz2 \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.person_in_movie.sql.bz2 \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.movie_boxes.sql \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.movie_dates.sql.bz2 \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.country.sql \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.genre.sql \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.person.sql.bz2 \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.movie_rating.sql \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.movie.sql.bz2 \
 && wget --quiet http://parselab.ru/kinopoisk/data/mdb.premiere_date.sql

WORKDIR /db
