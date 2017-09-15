\set ON_ERROR_STOP 1

drop user if exists web;

create database :database;
create user web with password 'mdb';
create user mdb with password 'mdb';

\connect :database

create schema mdb;

grant usage on schema mdb to mdb;

create type date_precision as enum ('d', 'm', 'y');

create table mdb.country
(
    id              serial primary key,
    name            text not null unique
);

grant select, insert on table mdb.country to mdb;

create table mdb.movie
(
    id              serial primary key,
    title           text not null,
    alternative_title text,
    countries       integer[],
    year            integer,
    slogan          text,
    directors       integer[],
    scenario        integer[],
    operators       integer[],
    composers       integer[],
    producers       integer[],
    arts            integer[],
    editors         integer[],
    genres          integer[],
    length          integer,
    age_restriction text,
    rating_imdb     numeric,
    rating_kinopoisk numeric,
    rating_critics  numeric,
    world_premiere  date,
    parse_date      timestamptz(0) default now(),
    update_date     timestamptz(0),
    rating_mpaa     varchar(10),
    production_status varchar(100)
);

grant select, insert, update, delete on mdb.movie to mdb;

create table mdb.movie_boxes
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    category        text not null,
    item            text not null,
    value           bigint,
    currency        varchar(100)
);

comment on table mdb.movie_boxes is 'Сборы';

grant select, usage on sequence mdb.movie_boxes_id_seq to mdb;
grant select, insert, update, delete on mdb.movie_boxes to mdb;

create index on mdb.movie_boxes (movie_id);

create table mdb.rating_history
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    day             date not null,
    rating          numeric not null
);

comment on table mdb.rating_history is 'Динамика изменения рейтинга фильма';


create table mdb.premiere_date
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    region          varchar(100) not null,
    premiere_date   date,
    precision       date_precision not null default 'd',
    commentary      text
);

create unique index on mdb.premiere_date(movie_id, region);

grant select, usage on sequence mdb.premiere_date_id_seq to mdb;
grant select, insert, update on mdb.premiere_date to mdb;

create table mdb.genre
(
    id              serial primary key,
    name            text not null unique
);

grant insert, update, select on mdb.genre to mdb;

create table mdb.movie_keyword
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    keyword         text not null
);

create unique index on mdb.movie_keyword (movie_id, keyword);

create table mdb.person
(
    id              serial primary key,
    name            text not null,
    alternative_name text,
    birth_date      date,
    birth_place     varchar(200),
    growth          integer,
    death_date      date,
    death_place     varchar(200),
    inserted_at     timestamptz(0) not null default now(),
    updated_at      timestamptz(0)
);

create index on mdb.person (name varchar_pattern_ops);
create index on mdb.person(birth_date);
create index on mdb.person(growth);
create index on mdb.person(death_date);

create table mdb.person_in_movie
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    person_id       integer not null references mdb.person(id),
    role            text not null,
    commentary      text
);

create index on mdb.person_in_movie(movie_id);
create index on mdb.person_in_movie(person_id);

grant select, update, delete, insert on table mdb.person, mdb.person_in_movie to mdb;

grant select, usage on sequence mdb.person_in_movie_id_seq to mdb;

create table mdb.movie_rating
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    rating_system   varchar(100) not null,
    rating          numeric not null,
    vote_count      integer
);

grant insert, update, delete, select on mdb.movie_rating to mdb;
grant select, usage on sequence mdb.movie_rating_id_seq to mdb;

create unique index on mdb.movie_rating(movie_id, rating_system);

create table mdb.stat
(
    id              serial primary key,
    year            integer not null unique,
    done_count      integer not null default 0 check (done_count >= 0),
    total_count     integer not null check (total_count >= 0),
    last_update_time timestamptz(0) not null default now(),
    last_movie_id   integer,
    current_page    integer,
    total_pages     integer,
    hostname        text
);

grant select, update, insert on mdb.stat to mdb;
grant select, usage on sequence mdb.stat_id_seq to mdb;

create table mdb.movie_dates
(
    id              serial primary key,
    movie_id        integer not null references mdb.movie(id),
    country_id      integer not null references mdb.country(id),
    premiere_date   date,
    premiere_precision char(1),
    viewers         integer,
    commentary      text
);

create index on mdb.movie_dates (movie_id);

grant select, insert, update, delete on mdb.movie_dates to mdb;
grant select, usage on sequence mdb.movie_dates_id_seq to mdb;

create table mdb.error
(
    id              serial primary key,
    date_time       timestamptz(0) not null default now(),
    hostname        text,
    movie_id        integer,
    message         text
);

grant select, usage on sequence mdb.error_id_seq to mdb;
grant select, insert on mdb.error to mdb;

\copy mdb.country from data/mdb.country.sql
\copy mdb.genre from data/mdb.genre.sql
\copy mdb.movie from data/mdb.movie.sql
\copy mdb.person from data/mdb.person.sql
\copy mdb.person_in_movie from data/mdb.person_in_movie.sql
\copy mdb.movie_boxes from data/mdb.movie_boxes.sql
\copy mdb.movie_dates from data/mdb.movie_dates.sql
\copy mdb.movie_rating from data/mdb.movie_rating.sql
\copy mdb.premiere_date from data/mdb.premiere_date.sql
