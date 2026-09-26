COPY(
--front_row_conversion
select driver,  
count(case when grid_position in (1,2) then 1 end) as wins_from_front_row,
count(*) as total_wins,
round(wins_from_front_row*100/total_wins, 2) as front_row_conversion
from race_results rr
where position = 1
group by all
order by wins_from_front_row desc
) TO 'data/exports/most_P1/front_row_conversion.csv'