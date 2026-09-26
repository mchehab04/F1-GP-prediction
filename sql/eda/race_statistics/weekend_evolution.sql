COPY(
select 
  p.year, 
  p.round,
  r.location as track,
  round(avg(case when p.session = 'FP1' then p.best_lap end), 3) as fp1_avg_s,
  round(avg(case when p.session = 'FP2' then p.best_lap end), 3) as fp2_avg_s,
  round(avg(case when p.session = 'FP3' then p.best_lap end), 3) as fp3_avg_s,
  round(fp2_avg_s - fp1_avg_s, 3) as delta_fp12,
  round(fp3_avg_s - fp2_avg_s, 3) as delta_fp23,
  round(avg(coalesce(q.q3, q.q2, q.q1)), 3) as quali_avg_s,
  round(quali_avg_s - coalesce(fp3_avg_s, fp1_avg_s), 3) as delta_to_quali,
  round(quali_avg_s - fp1_avg_s, 3) as total_weekend_evolution_s
from practice_results p
join quali_results q 
  on p.year = q.year and p.round = q.round and p.driver = q.driver
join races r 
  on p.year = r.year and p.round = r.round
where p.best_lap is not null and p.best_lap > 0
group by all
order by p.year, p.round
) TO 'data/exports/race_statistics/weekend_evolution.csv'