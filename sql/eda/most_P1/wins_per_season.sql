COPY (
select driver, year, count(*) as wins
from race_results
where position = 1
group by driver, year
order by year, wins
) TO 'data/exports/most_P1/wins_per_season.csv';