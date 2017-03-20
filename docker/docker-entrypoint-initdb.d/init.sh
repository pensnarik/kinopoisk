#!/bin/sh

sed -ri "s/#(listen_addresses) = 'localhost'/\1 = '*'/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(wal_level) = .*/\1 = 'logical'/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(max_worker_processes) = .*/\1 = 10/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(max_replication_slots) = .*/\1 = 100/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(max_wal_senders) = .*/\1 = ${PG_MAX_WAL_SENDERS:-60}/" "${PGDATA}/postgresql.conf"
sed -ri "s/(max_connections) = .*/\1 = ${PG_MAX_CONNECTIONS:-150}/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(track_commit_timestamp) = .*/\1 = on/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(log_min_duration_statement) = .*/\1 = ${PG_LOG_MIN_DURATION_STATEMENT:-0}/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(log_line_prefix) = .*/\1 = '%t: db=%d,user=%u '/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(log_min_messages) = .*/\1 = ${PG_LOG_MIN_MESSAGES:-warning}/" "${PGDATA}/postgresql.conf"
sed -ri "s/#(synchronous_commit) = .*/\1 = ${PG_SYNCHRONOUS_COMMIT:-off}/" "${PGDATA}/postgresql.conf"
sed -rt "s/#(work_mem) = .*/\1 = ${PG_WORK_MEM:-4MB}/" "${PGDATA}/postgresql.conf"

pg_ctl -D "${PGDATA}" -w restart

/usr/bin/python /db/install.py "postgresql://postgres@localhost:5432"
