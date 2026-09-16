COPY (
select r1.year as year, r1.round as round, r1.driver as faster_teammate, r2.driver as slower_teammate, round(r2.position - r1.position) as grid_gap, r1.classified_position as faster_position, r2.classified_position as slower_position
from race_results r1, race_results r2, race_results r3, race_results r4
where r1.round = r2.round and r1.year = r2.year
  and r1.year = r3.year and r1.round = r3.round and r1.driver = r3.driver
  and r2.year = r4.year and r2.round = r4.round and r2.driver = r4.driver
  and r1.driver = r3.driver and r2.driver = r4.driver
  and r1.position < r2.position
  and r1.team_name = r2.team_name
  and r1.status = r2.status
order by year, round
) TO 'data/exports/teammate_h2h/teammate_gaps_in_race.csv'