COPY (
select * from race_results r where r.position is null
) TO 'data/exports/data_cleaning/null_values.csv'