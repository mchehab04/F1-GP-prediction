COPY (
select r.year as year,
round(count(case when r.grid_position > q.position or r.grid_position = 0 then 1 end)*100/count(*), 2) as penalty_pct
from race_results r
join quali_results q
on r.year = q.year and r.round = q.round and r.driver = q.driver
group by all
order by year, penalty_pct desc
) TO 'data/exports/race_statistics/season_avg_penalties.csv'