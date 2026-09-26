COPY(
select year, driver, count(case when position = 1 then 1 end) as sprint_wins, 
count(*) as sprint_races
from sprint_results
group by all
having sprint_wins > 0
order by year, sprint_wins desc
) TO 'data/exports/most_P1/sprint_race_winners.csv'