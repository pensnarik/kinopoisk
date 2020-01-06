\set ON_ERROR_STOP 1

drop user if exists mdb;

create database mdb;

create user mdb with password 'mdb';

\connect mdb

create schema mdb;

grant usage on schema mdb to mdb;

create type date_precision as enum ('d', 'm', 'y');

create table mdb.country
(
    id              serial primary key,
    name            text not null unique
);

grant select, insert on table mdb.country to mdb;

comment on table mdb.country is 'Страны';

create table mdb.movie
(
    id              serial,
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
    genres          text[],
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

comment on table mdb.movie is 'Фильмы';

create table mdb.movie_boxes
(
    id              serial primary key,
    movie_id        integer,
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
    movie_id        integer not null,
    day             date not null,
    rating          numeric not null
);

comment on table mdb.rating_history is 'Динамика изменения рейтинга фильма';


create table mdb.premiere_date
(
    id              serial primary key,
    movie_id        integer not null,
    region          varchar(100) not null,
    premiere_date   date,
    precision       date_precision not null default 'd',
    commentary      text
);

create unique index on mdb.premiere_date(movie_id, region);

grant select, usage on sequence mdb.premiere_date_id_seq to mdb;
grant select, insert, update on mdb.premiere_date to mdb;

comment on table mdb.premiere_date is 'Даты премьер';

create table mdb.genre
(
    id              text primary key,
    name            text not null unique
);

grant insert, update, select on mdb.genre to mdb;

comment on table mdb.genre is 'Жанры';

create table mdb.movie_keyword
(
    id              serial primary key,
    movie_id        integer not null,
    keyword         text not null
);

create unique index on mdb.movie_keyword (movie_id, keyword);

comment on table mdb.movie_keyword is 'Ключевые слова';

create table mdb.person
(
    id              serial,
    name            text not null,
    alternative_name text,
    birth_date      date,
    birth_place     varchar(200),
    growth          integer,
    death_date      date,
    death_place     varchar(200),
    inserted_at     timestamptz(0) not null default now(),
    updated_at      timestamptz(0),
    parsed_extra    boolean not null default false
);

create index on mdb.person (name varchar_pattern_ops);
create index on mdb.person(birth_date);
create index on mdb.person(growth);
create index on mdb.person(death_date);
create index on mdb.person(parsed_extra);

comment on table mdb.person is 'Персоны';
comment on column mdb.person.parsed_extra is 'true, если информация о персоне получена с индивидуальной страницы';

create table mdb.person_in_movie
(
    id              serial,
    movie_id        integer,
    person_id       integer,
    role            text not null,
    commentary      text
);

grant select, update, delete, insert on table mdb.person, mdb.person_in_movie to mdb;
grant select, usage on sequence mdb.person_in_movie_id_seq to mdb;

comment on table mdb.person_in_movie is 'Участие персон в фильмах';

create table mdb.movie_rating
(
    id              serial primary key,
    movie_id        integer not null,
    rating_system   varchar(100) not null,
    rating          numeric not null,
    vote_count      integer
);

grant insert, update, delete, select on mdb.movie_rating to mdb;
grant select, usage on sequence mdb.movie_rating_id_seq to mdb;

create unique index on mdb.movie_rating(movie_id, rating_system);

comment on table mdb.movie_rating is 'Рейтинги фильмов';

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

comment on table mdb.stat is 'Статистика парсера';

create table mdb.movie_dates
(
    id              serial primary key,
    movie_id        integer not null,
    country_id      integer not null references mdb.country(id),
    premiere_date   date,
    premiere_precision char(1),
    viewers         integer,
    commentary      text
);

create index on mdb.movie_dates (movie_id);

grant select, insert, update, delete on mdb.movie_dates to mdb;
grant select, usage on sequence mdb.movie_dates_id_seq to mdb;

comment on table mdb.movie_dates is 'Даты (премьер, показов и т.д.)';

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

comment on table mdb.error is 'Журнал ошибок';

/* Некоторые constraint'ы и индексы лучше создавать после загрузки данных */

alter table mdb.movie add constraint movie_pkey primary key (id);

alter table mdb.person add constraint person_pkey primary key (id);

alter table mdb.person_in_movie add constraint person_in_movie_pkey primary key (id);
alter table mdb.person_in_movie add constraint person_in_movie_movie_id_fkey foreign key (movie_id) references mdb.movie(id);
alter table mdb.person_in_movie add constraint person_in_movie_person_id_fkey foreign key (person_id) references mdb.person(id);
create index on mdb.person_in_movie(movie_id);
create index on mdb.person_in_movie(person_id);

alter table mdb.movie_boxes add constraint movie_boxes_movie_id_fkey foreign key (movie_id) references mdb.movie(id);

alter table mdb.rating_history add constraint rating_history_movie_id foreign key (movie_id) references mdb.movie(id);
alter table mdb.premiere_date add constraint premiere_date_movie_id foreign key (movie_id) references mdb.movie(id);

alter table mdb.movie_keyword add constraint movie_keyword_movie_id foreign key (movie_id) references mdb.movie(id);
alter table mdb.movie_rating add constraint movie_rating_movie_id foreign key (movie_id) references mdb.movie(id);
alter table mdb.movie_dates add constraint movie_dates_movie_id foreign key (movie_id) references mdb.movie(id);

create index on mdb.person_in_movie (commentary varchar_pattern_ops);

select setval('mdb.movie_rating_id_seq', (select max(id) from mdb.movie_rating));
select setval('mdb.premiere_date_id_seq', (select max(id) from mdb.premiere_date));
select setval('mdb.movie_dates_id_seq', (select max(id) from mdb.movie_dates));
