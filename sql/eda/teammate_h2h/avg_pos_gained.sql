COPY (
select d1.year as year, d1.team_name as team,
  d1.driver as d1,
  round(avg((case when d1.grid_position = 0 then 20 else d1.grid_position end) - d1.position), 2) as d1_avg_pos_gained,
  d2.driver as d2,
  round(avg((case when d2.grid_position = 0 then 20 else d2.grid_position end) - d2.position), 2) as d2_avg_pos_gained,
  count(*) as clean_races
from race_results d1, race_results d2
where d1.year = d2.year and d1.round = d2.round and d1.team_name = d2.team_name and d1.driver < d2.driver
and d1.classified_position not in ('R', 'D', 'W') and d2.classified_position not in ('R', 'D', 'W')
group by all
order by year, team
) TO 'data/exports/teammate_h2h/avg_pos_gained.csv'