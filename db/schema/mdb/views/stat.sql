CREATE OR REPLACE VIEW public.stat AS
 SELECT stat.id,
    stat.year,
    stat.done_count,
    stat.total_count,
    stat.last_update_time,
    stat.hostname,
    stat.current_page,
    stat.total_pages,
    round(stat.done_count::numeric / stat.total_count::numeric * 100::numeric, 2) AS perc
   FROM mdb.stat
  ORDER BY stat.year;

GRANT SELECT ON public.stat TO mdb;