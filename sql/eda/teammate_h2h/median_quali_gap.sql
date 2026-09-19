COPY (
--median quali time gap
select d1.year as year, r1.team_name as team, count(*) as races, d1.driver as d1, d2.driver as d2,
  round(median(
      case
        when d1.q3 is not null and d2.q3 is not null then d1.q3 - d2.q3
        when d1.q2 is not null and d2.q2 is not null then d1.q2 - d2.q2
        when d1.q1 is not null and d2.q1 is not null then d1.q1 - d2.q1
      end), 3) as median_gap_s
from quali_results d1, quali_results d2, race_results r1, race_results r2
where d1.year = d2.year and d1.round = d2.round
  and d1.driver = r1.driver and d2.driver = r2.driver
  and r1.year = d1.year and r2.round = d2.round
  and r1.year = r2.year and r1.round = r2.round
  and r1.team_name = r2.team_name
  and d1.driver < d2.driver
group by all
order by year, races desc, median_gap_s desc
) TO 'data/exports/teammate_h2h/median_quali_gap.csv'