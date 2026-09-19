COPY (
--teammates h2h for clean races
select d1.year as year, d1.team_name as team, d1.driver as driver1, round(avg(d1.position), 1) as d1_avg_pos,
  d2.driver as driver2, round(avg(d2.position), 1) as d2_avg_pos,
  count(*) clean_race_count,
  count(case when d1.position < d2.position  then 1 end) as d1_ahead,
  count(case when d2.position < d1.position  then 1 end) as d2_ahead
from race_results d1, race_results d2
where d1.year = d2.year and d1.round = d2.round 
  and d1.team_name = d2.team_name and d1.driver < d2.driver
  and d1.classified_position not in ('R', 'D', 'W')
  and d2.classified_position not in ('R', 'D', 'W')
group by all
order by year, clean_race_count desc
) TO 'data/exports/teammate_h2h/clean_h2h.csv'