COPY(
--Circuit chaos
select r.location as track, count(case when rr.classified_position = 'R' then 1 end) as retirements,
count(distinct r.year) as races_held,
round(retirements/races_held, 2) as avg_dnfs
from race_results rr
join races r
on rr.year = r.year and rr.round = r.round
group by all
order by avg_dnfs desc, races_held desc
) TO 'data/exports/race_statistics/track_avg_dnfs.csv'