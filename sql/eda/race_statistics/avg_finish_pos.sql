COPY (
--average finishing position per season
select r.year, r.driver, round(avg(r.position), 1) avg_finish_pos, sum(r.points) total_points
from race_results r
group by year, driver
order by year, avg_finish_pos
) TO 'data/exports/race_statistics/avg_finish_pos.csv'