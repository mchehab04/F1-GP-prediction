COPY (
--drivers start on pole and win the race
select r.year, r.round, r.driver
from race_results r, quali_results q
where q.year = r.year and q.round = r.round and q.driver = r.driver
and r.position = 1 and q.position = 1
group by all
order by year, round
) TO 'data/exports/race_statistics/pole_to_win.csv'