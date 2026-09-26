COPY(
select driver,
  count(distinct grid_position) as different_grid_spots_won_from,
  count(*) as total_wins
from race_results
where position = 1
group by all
having count(distinct grid_position) > 1
order by different_grid_spots_won_from desc
) TO 'data/exports/most_P1/num_of_grid_spots_won_from.csv'