COPY (
select r.driver as driver,
round(count(case when r.grid_position > q.position or r.grid_position = 0 then 1 end)*100/count(*), 2) as penalty_pct,
count(*) as races_driven
from race_results r
join quali_results q
on r.year = q.year and r.round = q.round and r.driver = q.driver
group by all
order by penalty_pct desc, races_driven desc
) TO 'data/exports/race_statistics/driver_avg_penalties.csv'