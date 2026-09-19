COPY(
SELECT DISTINCT status, count(*) count 
FROM race_results 
group by status
order by status 
) TO 'data/exports/data_cleaning/distinct_status.csv'