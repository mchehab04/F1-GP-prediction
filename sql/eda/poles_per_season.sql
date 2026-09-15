COPY (
select driver, year, count(*) as poles
from quali_results
where position = 1
group by driver, year
order by year, poles
) TO 'data/exports/poles_per_season.csv';