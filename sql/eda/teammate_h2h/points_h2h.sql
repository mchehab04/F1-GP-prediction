COPY (
select d1.driver as "driver 1", d2.driver as "driver 2", d1.year as "year", 
    sum(d1.points) as d1_points, sum(d2.points) as d2_points, round(d1_points - d2_points) as gap
from race_results d1
join race_results d2
on d1.team_name = d2.team_name and d1.driver < d2.driver and d1.year = d2.year and d1.round = d2.round
group by all
order by year, gap
desc
) TO 'data/exports/teammate_h2h/points_h2h.csv'