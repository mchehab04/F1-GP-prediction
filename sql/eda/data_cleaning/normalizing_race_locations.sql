UPDATE races
SET location = CASE
  WHEN lower(location) = 'monaco' THEN 'Monte Carlo'
  WHEN lower(location) = 'miami gardens' THEN 'Miami'
  WHEN lower(location) = 'yas island' THEN 'Yas Marina'
  WHEN lower(location) = 'kuala lumpur' THEN 'Sakhir'
  ELSE location
END
WHERE lower(location) IN ('monaco', 'miami gardens', 'yas island', 'kuala lumpur')