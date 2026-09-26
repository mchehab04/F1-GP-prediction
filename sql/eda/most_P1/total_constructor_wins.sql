COPY(
--total constructor wins from 2022-2026
select d1.team_name, count(*) as total_wins
from race_results d1
join race_results d2
on d1.year = d2.year and d1.round = d2.round and d1.driver = d2.driver
group by all
having d1.position = 1
order by total_wins desc
) TO 'data/exports/most_P1/total_constructor_wins.csv'