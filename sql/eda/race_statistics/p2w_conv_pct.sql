COPY (
--pole to win conversion
select r.year, r.driver, count(*) as total_poles,
    count(case when r.position = 1 then 1 end) as pole_to_win,
    round(pole_to_win*100/total_poles, 1) as p2w_conversion
from race_results r, quali_results q
where q.year = r.year and q.round = r.round and q.driver = r.driver
and q.position = 1
group by all
order by year, total_poles desc
) TO 'data/exports/race_statistics/pole_to_win_conv_pct.csv'