COPY (
--percent of q3 appearances per season
select d1.year as year, r1.team_name as team, d1.driver d1, round(count(case when d1.q3 is not null then 1 end)*100/count(*), 2) as d1_q3_app_pct,
  d2.driver as d2, round(count(case when d2.q3 is not null then 1 end)*100/count(*), 2) as d2_q3_app_pct
from quali_results d1, quali_results d2, race_results r1, race_results r2
where d1.year = d2.year and d1.round = d2.round
  and d1.year = r1.year and d2.year = r2.year and d1.round = r1.round and d2.round = r2.round
  and r1.team_name = r2.team_name and d1.driver < d2.driver
  and d1.driver = r1.driver and d2.driver = r2.driver
group by all
order by year, d1_q3_app_pct desc
) TO 'data/exports/teammate_h2h/q3_app_pct.csv'