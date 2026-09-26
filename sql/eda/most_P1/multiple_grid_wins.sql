COPY(
--drivers who won a race starting from multiple grid places
select driver, 
grid_position as pos, 
count(*) as wins_from_pos
from race_results
where position = 1
group by all
order by driver, pos
) TO 'data/exports/most_P1/multiple_grid_wins.csv'