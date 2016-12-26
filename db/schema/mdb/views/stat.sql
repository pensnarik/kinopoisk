CREATE OR REPLACE VIEW public.stat AS
 SELECT stat.id,
    stat.year,
    stat.done_count,
    stat.total_count,
    stat.last_update_time,
    stat.hostname,
    round(stat.done_count::numeric / stat.total_count::numeric * 100::numeric, 2) AS perc
   FROM mdb.stat
  ORDER BY stat.year
