COPY(
--FP3 to quali
select q.driver as driver, count(*) as fp3_p1,
count(case when q.position = 1 then 1 end) as pole_position,
round((case when fp3_p1 != 0 then pole_position/fp3_p1 else 0 end) * 100, 2) as conv_rate
from quali_results q
join practice_results p
on q.year = p.year and q.round = p.round and q.driver = p.driver
and p.session = 'FP3' and p.position = 1 
group by all
order by pole_position desc
) TO 'data/exports/race_statistics/fp3_to_pole_conv.csv'