COPY(
select distinct d1.driver as "driver 1", d2.driver as "driver 2", d2.team_name as "team_name", d1.year as "year"
from drivers d1
join drivers d2
on d1.team_name = d2.team_name and d1.driver < d2.driver and d1.year = d2.year
order by year
) TO 'data/exports/teammate_h2h/teammates_per_season.csv'