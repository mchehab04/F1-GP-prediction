COPY (
--quali to race concordance
select d1.year as year, r1.team_name as team, count(*) as clean_races, d1.driver as d1,
  count(
    case
      when d1.position < d2.position and r1.position < r2.position then 1
    end
  ) as d1_concordance,
  d2.driver as d2,
  count(
    case
      when d1.position > d2.position and r1.position > r2.position then 1
    end
  ) as d2_concordance,
  round(((d1_concordance + d2_concordance) * 100/clean_races), 2) as team_con_pct
from quali_results d1, quali_results d2, race_results r1, race_results r2
where d1.year = d2.year and d1.round = d2.round
  and d1.driver = r1.driver and d2.driver = r2.driver
  and r1.year = d1.year and r2.round = d2.round
  and r1.year = r2.year and r1.round = r2.round
  and r1.team_name = r2.team_name
  and d1.driver < d2.driver
  and r1.classified_position not in ('R', 'D', 'W')
  and r2.classified_position not in ('R', 'D', 'W')
group by all
order by year, team_con_pct desc
) TO 'data/exports/teammate_h2h/concordance_pct.csv'