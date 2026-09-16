COPY (
select q1.year as year, q1.round as round, q1.driver as faster_teammate, q2.driver as slower_teammate, round(q2.position - q1.position) as grid_gap
from quali_results q1, quali_results q2, race_results r1, race_results r2
where q1.round = q2.round and q1.year = q2.year
  and r1.year = q1.year and r1.round = q1.round and r1.driver = q1.driver
  and r2.year = q2.year and r2.round = q2.round and r2.driver = q2.driver
  and q1.driver = r1.driver and q2.driver = r2.driver
  and q1.position < q2.position
  and r1.team_name = r2.team_name
order by year, round
) TO 'data/exports/teammate_h2h/teammate_gaps_in_quali.csv'