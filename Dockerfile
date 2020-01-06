FROM postgres:9.6

COPY docker/docker-entrypoint-initdb.d /docker-entrypoint-initdb.d/
