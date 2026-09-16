COPY (
select p1.driver as "faster teammate", p2.driver as "slower teammate", r1.team_name as "team_name",
       p1.year as "year", p1.round as "round", p1.session as "session",
       p1.best_lap as "fastest_lap", round(p2.best_lap - p1.best_lap, 3) as "gap_s"
from practice_results p1, practice_results p2, race_results r1, race_results r2
where p1.year = p2.year and p1.round = p2.round and p1.session = p2.session   -- same session
  and r1.year = p1.year and r1.round = p1.round and r1.driver = p1.driver     -- driver 1's team that weekend
  and r2.year = p2.year and r2.round = p2.round and r2.driver = p2.driver     -- driver 2's team that weekend
  and r1.team_name = r2.team_name                                             -- same team = teammates
  and p1.best_lap < p2.best_lap                                               -- p1 is the faster one
order by year, round, session
) TO 'data/exports/teammate_h2h/teammate_gaps_in_practice.csv'