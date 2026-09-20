COPY (
select r.year, r.location, round(avg(abs(case when rr.grid_position = 0 then 20 else rr.grid_position end - rr.position)), 2) as avg_pos_gained
from race_results rr, races r
where rr.classified_position not in ('R', 'W', 'D')
and rr.year = r.year and rr.round = r.round
group by all
order by year, avg_pos_gained desc
) TO 'data/exports/race_statistics/track_overtaking.csv'