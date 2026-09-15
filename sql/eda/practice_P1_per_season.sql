COPY (
select driver, year, count(*) as practice_P1_positions
from practice_results
where position = 1
group by driver, year
order by year, practice_P1_positions
) TO 'data/exports/practice_P1_per_season.csv';