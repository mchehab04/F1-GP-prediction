--if status is 'Finished' or includes to_lowercase('lap') (either +1 Lap or +2 Laps), then set the classified_position as the position. 
--if status is 'Withdrew' or 'Did not start', then set classidied_position to 'W'
--if status is 'Disqualified', then set classidied_position to 'D'
--Any other status should set classified_position to 'R' (they all are the reason for a DNF)
UPDATE race_results
SET classified_position = CASE
  WHEN lower(status) = 'finished' OR lower(status) LIKE '%lap%' THEN CAST(position AS VARCHAR)
  WHEN status IN ('Withdrew', 'Did not start') THEN 'W'
  WHEN status = 'Disqualified' THEN 'D'
  ELSE 'R'
END