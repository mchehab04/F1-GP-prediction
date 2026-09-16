COPY (
--reliability issues
select distinct r.year, r.driver, count(case when r.classified_position = 'R' then 1 end) as retirements, 
    count(case when (r.classified_position != 'R' and r.classified_position != 'D' and r.classified_position != 'W') then 1 end) as races_completed,
    round(races_completed*100/(races_completed+retirements), 1) as completion_pct
from race_results r
where r.classified_position is not null
group by year, driver
order by year, completion_pct desc
) TO 'data/exports/race_statistics/race_completion_pct.csv'