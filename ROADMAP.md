# F1 Race Prediction — Project Roadmap

A data science + data analytics project, run end to end the way a real one would be. Tick boxes as you go. Each phase ends with a **Done when** line that describes the deliverable, so you know when to move on.

The phases are roughly sequential, but real projects loop: EDA will send you back to cleaning, and modeling will send you back to feature engineering. That's expected, not a sign something went wrong.

---

## Existing data audit (2026-09-13)

**What's on disk**

| Source | Seasons | What was captured | Where |
|---|---|---|---|
| FastF1 cache | 2021–2022 (44 events, every session) | Live-timing laps, timing, weather, race control, driver info, plus Jolpica/Ergast results. **No car telemetry** (`telemetry=False`). ~570 MB | `fastf1_cache/` |
| OpenF1 raw JSONL | 2023–2024 (48 meetings, 236 sessions) | sessions, drivers, session_result, starting_grid. **No laps, stints, or weather** | `ingest/data/raw/openf1/` |

Both fetch scripts also wrote to a Postgres DB via `DATABASE_URL`. There is no `.env` in the project, so whether that DB still exists is unknown.

**Can they be used together?** Yes, but only after harmonizing, and not in the way you might first expect:

1. **The seasons don't overlap.** FastF1 covers 2021–22 and OpenF1 covers 2023–24. Combining them means stacking seasons, not joining rows.
2. **The content doesn't overlap either.** The FastF1 run kept laps + weather; the OpenF1 run kept results + grid. As-is, you can't build the same feature for all four seasons.
3. **The keys differ.** FastF1 rows use a made-up key (`year*10000 + round*10 + code`), while OpenF1 uses its own `session_key` (e.g. `7953`). You'll need a canonical key: `(season, round, session_type, driver)`.
4. **`driver_number` is not a stable driver ID.** Verstappen is #33 in 2021 and #1 from 2022. Use the 3-letter code (`VER`) or Jolpica's `driverId`.
5. **Team names drift.** AlphaTauri → RB, Alfa Romeo → Sauber → Audi (2026). You'll need a constructor lineage table.

**Recommendation:** use **FastF1 as the backbone for every season** (2018 → present; one API, one schema, laps and results included). Use **Jolpica** for long history (1950+) and canonical IDs, and **OpenF1** for 2023+ extras and as an independent source to cross-check against. Keep the existing OpenF1 JSONL: it's a ready-made, realistically messy dataset for Phase 2.

**Data-quality issues already found in the OpenF1 files** (good cleaning practice for Phase 2):

- [ ] 2023 `sessions` has every session **5×** (565 rows, 113 unique). Cause: `dump_jsonl` opens files in append mode (`"a"`), so each rerun appended again. 2023 drivers (57) and results (19) also have duplicate rows.
- [ ] **Pre-season testing is mixed in** under the name "Practice 1/2/3" (e.g. meeting 1140, Sakhir, 2023-02-23). It needs filtering by meeting.
- [ ] In Qualifying and Sprint Shootout/Qualifying results, `duration` and `gap_to_leader` are **lists** `[Q1, Q2, Q3]`. `pd.to_numeric` in `openf1_load_from_jsonl.py` turns these into NaN, which silently drops all qualifying times.
- [ ] `openf1_fetch.py` reads `status`, `time`, and `penalty_text`, but none of these fields exist in the responses. Those columns will be entirely null. The real fields are `dnf`, `dns`, `dsq`, `duration`, `gap_to_leader` (and grid `position`, `lap_duration`).
- [ ] 126 result rows have a null `position` (DNF/DNS/DSQ). You need an explicit rule for how these are encoded.
- [ ] The sprint qualifying session was renamed between seasons: "Sprint Shootout" (2023) became "Sprint Qualifying" (2024).
- [ ] The three OpenF1 scripts define **conflicting schemas** for the same tables. For example, `session_result` has `status`/`time_ms` in one script and `dnf`/`dns`/`dsq`/`duration` in another.

---

## Phase 0 — Framing & setup

The goal is to decide what you're predicting and for whom, before touching data.

- [x] Write the **primary question** in one sentence. **Decided (2026-09-13):** *"After qualifying, predict each driver's finishing position for the Grand Prix."* Podium / points probabilities can be derived from the position model later.
- [ ] Fix the **decision point** (e.g. "after qualifying, before lights out"). Every feature must be knowable at that moment. This single rule prevents most leakage.
- [ ] List 5–8 **analytics questions**, the kind a stakeholder would ask. Examples: How often does pole convert to a win, by circuit? Which teams lose the most time in the pits? How much does rain reshuffle results? How did the 2022 and 2026 regulation changes affect overtaking?
- [ ] Define **success**: a baseline to beat ("finish = grid position") and metrics (MAE on position, Spearman rank correlation, Brier score for podium probability).
- [ ] Note who the audience is: a technical reviewer (DS) vs a fan or team strategist (DA). This shapes Phase 11.
- [ ] Set up: `git init`, `.gitignore` (cache, `.env`, `data/`), virtualenv, pinned `requirements.txt`, and a folder layout: `data/{raw,interim,processed}`, `src/`, `notebooks/`, `reports/`, `tests/`.
- [x] Choose storage. **Decided (2026-09-13): DuckDB + Parquet** — real SQL without running a server. The old ingest scripts' Postgres writes get replaced in Phase 1.
- [ ] Start `docs/decisions.md`, a short log of each choice and the reason for it. Real teams keep one of these.

**Done when:** a README states the question, decision point, baseline, and metrics; the repo is under git.

---

## Phase 1 — Data acquisition (fetching)

The goal is reproducible, polite, idempotent ingestion from several kinds of source.

**Fix and reuse what exists**
- [ ] Fix the append-mode bug. Raw files should be written once per `(source, endpoint, key)` and overwritten on rerun, never appended.
- [ ] Add a **fetch manifest** row per request: source, URL/params, fetched_at, row count, status. This is how you'll prove the pipeline is reproducible.

**FastF1 (Python library over F1 live timing)**
- [ ] Extend to **2018 → 2026-to-date**, all sessions, reusing the existing cache.
- [ ] Extract `session.results`, `laps`, `weather_data`, `race_control_messages`, and `track_status`. The current script skips results.
- [ ] Pull car telemetry (`car_data`) for a **small subset** only, such as a few races, for Phase 4 deep-dives. It's large.
- [ ] Respect rate limits: cache on, cap sessions per run, back off on errors (the current script already does this).

**OpenF1 (REST, JSON, 2023+)**
- [ ] Fetch the endpoints you skipped: `meetings`, `laps`, `stints`, `pit`, `weather`, `race_control`, `intervals`, `position`.
- [ ] Practice filter syntax (e.g. `date>=...`, `lap_number<=...`) and handle `429` responses with backoff.
- [ ] Check current access terms. Historical data has been free, but real-time access may require a paid tier.

**Jolpica (Ergast successor, REST, 1950 → present)**
- [ ] Fetch results, qualifying, sprint, pit stops, driver/constructor standings, and circuits.
- [ ] Handle **pagination** (`limit` / `offset`) and throttle requests to stay within its rate limit.
- [ ] Use its `driverId` / `constructorId` / `circuitId` as your canonical IDs.

**Weather (Open-Meteo, free, no key)**
- [ ] Fetch hourly historical weather at each circuit's lat/long for race day.
- [ ] Stretch goal: fetch archived **forecasts**, meaning what was predicted before the race. Using actual race weather as a feature is leakage; using the forecast isn't.

**Web scraping (HTML)**
- [ ] Scrape circuit attributes from Wikipedia (length, corners, street vs permanent, first GP) using `pandas.read_html` or BeautifulSoup.
- [ ] Check `robots.txt`, cache pages locally, and rate-limit requests.

**Done when:** one command per source rebuilds `data/raw/` from scratch, reruns cause no duplicates, and the manifest shows what came from where.

---

## Phase 2 — Cleaning, integration & validation

The goal is one set of trustworthy, documented tables.

- [ ] Build **canonical dimension tables**: `season`, `circuit`, `driver` (stable ID + code + DOB), `constructor` + lineage (AlphaTauri → RB, Sauber → Audi), and `session` (normalized `session_type` enum).
- [ ] Map all source keys to canonical keys (FastF1 surrogate keys, OpenF1 `session_key`, Jolpica IDs).
- [ ] Normalize session names (Sprint Shootout / Sprint Qualifying) and **drop testing**.
- [ ] Deduplicate and enforce dtypes. Pick one unit for time (ms or s) and store everything in UTC.
- [ ] Fix the qualifying-list issue: explode `[Q1, Q2, Q3]` into columns.
- [ ] Classify **missingness** as structural (no Q3 time because the driver was knocked out in Q2), mechanical (DNF), or genuinely missing. Handle each type differently.
- [ ] Define result encoding: classified finish, DNF, DNS, DSQ, and "not classified but ran 90%".
- [ ] **Cross-source reconciliation** for overlapping seasons (FastF1 vs OpenF1 vs Jolpica): measure the agreement rate and investigate mismatches. Post-race penalties and disqualifications are the usual cause; the 2023 US GP had two post-race DSQs.
- [ ] Write **validation checks as code** (pandera, or plain `assert`s). Examples:
  - one winner per race; grid positions unique
  - race points total matches that season's points system
  - lap numbers increase monotonically per driver; lap times fall within a plausible range
  - driver count per race matches the grid size for that season (20 through 2025, 22 in 2026 with Cadillac). Derive this from data rather than hardcoding it.
- [ ] Write a **data dictionary** (table, column, type, unit, source, meaning) and a lineage note (raw → interim → processed).

**Done when:** `data/processed/` builds from raw with one command, all validation checks pass, and the dictionary is written.

---

## Phase 3 — SQL & data modeling (analytics track)

- [ ] Model a **star schema**: `fact_result`, `fact_lap`, `fact_pitstop`, `dim_driver`, `dim_constructor`, `dim_circuit`, `dim_session`.
- [ ] Answer the Phase 0 analytics questions **in SQL**: CTEs, window functions (rolling form, `RANK()`, `LAG()`), and conditional aggregation.
- [ ] Define 5–10 **KPIs** with exact formulas (e.g. pole-to-win conversion, average positions gained, DNF rate, median pit-stop loss).
- [ ] Save them as reusable SQL views that later feed the dashboard.

**Done when:** a `sql/` folder of views answers every analytics question.

---

## Phase 4 — Exploratory data analysis

- [ ] Look at distributions: finishing position, positions gained, lap times by compound, pit-stop durations.
- [ ] Look at relationships: grid vs finish (overall and **per circuit**), qualifying gap vs result, teammate deltas.
- [ ] Look at time structure: team dominance by season, and visible shifts at the **2022 and 2026 regulation changes**.
- [ ] Look for outliers and anomalies: safety cars, red flags, wet races. Decide whether each is noise or signal.
- [ ] Do one telemetry deep-dive: compare two drivers' speed traces on a fastest lap.
- [ ] Keep a **hypothesis log**. Every "huh, interesting" becomes a candidate for Phase 5 or 6.

**Done when:** an EDA notebook ends with the 10 most important findings, each backed by a chart.

---

## Phase 5 — Statistical inference & hypothesis testing

- [ ] Compute **bootstrap confidence intervals** for KPIs (e.g. mean pit-stop time per team).
- [ ] Test whether the pole-to-win rate differs from P2's, using a proportion test or chi-square.
- [ ] Test teammate qualifying gaps with **paired tests** (paired t-test vs Wilcoxon signed-rank) and check the assumptions for each.
- [ ] Test whether wet races produce more position change, using a Levene test on variance or a permutation test.
- [ ] Estimate tyre degradation with regression slopes of lap time vs tyre age by compound, including CIs.
- [ ] Run a **home-race effect** permutation test.
- [ ] Control for **multiple comparisons** (Bonferroni vs Benjamini–Hochberg), report **effect sizes**, and do one **power analysis**. Ask: is there enough data to detect this effect at all?
- [ ] Bayesian angle: a Beta-Binomial model of each team's reliability (DNF rate) that shrinks small samples toward the mean.
- [ ] Mixed-effects model: how much of the result is the **driver** vs the **car**? Use random effects for driver and constructor-season.

**Done when:** each test is written up as hypothesis → method → assumptions → result → effect size → plain-English conclusion.

---

## Phase 6 — Causal analysis

Correlation vs causation, with explicit assumptions.

- [ ] Draw a **DAG** for "does starting on pole cause winning?" Car pace confounds both grid and finish, so decide what you must adjust for.
- [ ] **Natural experiment:** does pitting under a Safety Car gain positions? SC timing is close to random with respect to strategy.
- [ ] **Regression discontinuity** (2018–2021): under the rules then, P10 had to start on its Q2 tyres while P11 had free choice. Do drivers just outside the top 10 outperform those just inside?
- [ ] **Interrupted time series / pre-post** on the 2022 regulation change: did overtaking or grid-to-finish correlation shift?
- [ ] **Propensity score matching or weighting:** the effect of a one-stop vs two-stop strategy on finishing position.
- [ ] Run refutation and sensitivity checks (e.g. DoWhy placebo tests), and state what could break each conclusion.

**Done when:** each analysis states its causal question, assumptions, method, estimate with uncertainty, and limitations.

---

## Phase 7 — Feature engineering

One row per `(race, driver)`, using only information available at the decision point.

- [ ] Grid and qualifying: grid position, gap to pole (%), gap to teammate, grid penalties.
- [ ] Form: rolling / exponentially weighted driver and constructor results, points, and DNF rate over the last N races.
- [ ] Pace from practice: FP2 long-run pace and degradation from lap data, **normalized to the session** (relative to the fastest).
- [ ] Circuit: type, overtaking difficulty (historical grid-to-finish correlation), and the driver's history at the track.
- [ ] Context: championship position, sprint result on sprint weekends, weather forecast.
- [ ] Handle regime changes: use relative-to-field features instead of raw lap times, add an era indicator, and weight recent seasons more.
- [ ] Do **point-in-time joins** (`merge_asof` or SQL with `<` date filters). Write a test proving no feature uses data from on or after race day.
- [ ] Run a leakage review: for every feature, ask "could I have known this at the decision point?"

**Done when:** the feature table builds from processed data, the leakage test passes, and every feature is in the data dictionary.

---

## Phase 8 — Modeling

- [ ] Baselines first: "finish = grid", "finish = last race result". Record their scores.
- [ ] Try these model families:
  - Linear / ordinal regression on position
  - Logistic regression for podium and points-finish probabilities
  - Gradient boosting (LightGBM / XGBoost)
  - **Learning-to-rank** (LightGBM `lambdarank` with each race as a query group). This fits F1 naturally: you're ranking a field, not predicting independent numbers.
  - Stretch goal: a separate **DNF model** combined with a finishing-order model, since crashes and failures behave differently from pace.
- [ ] **Time-aware validation:** walk-forward / rolling-origin by race. **Never use random K-fold** on this data.
- [ ] Tune hyperparameters inside the temporal folds (e.g. Optuna).
- [ ] Track experiments with MLflow, or at minimum a CSV log of params, features, and scores.
- [ ] **Calibrate** probabilities (isotonic or Platt) and check reliability curves.

**Done when:** at least one model beats the grid baseline on walk-forward validation, and every experiment is logged.

---

## Phase 9 — Evaluation & interpretation

- [ ] Metrics: MAE on position, Spearman, NDCG@3 / @10, Brier / log loss, and calibration.
- [ ] Measure **uncertainty in the comparison**: bootstrap over races and run a paired test of model vs baseline. A small gain may be noise.
- [ ] **Error analysis:** break errors down by circuit type, weather, team, and season. Separate DNF-driven errors from pace errors.
- [ ] Explainability: SHAP, permutation importance, partial dependence. Check that the model's reasoning makes F1 sense.
- [ ] **Distribution shift:** evaluate separately on 2026 (new regulations, new team). How much does performance drop, and how fast does it recover as 2026 races accumulate?
- [ ] Write a **model card**: intended use, data, metrics, limitations, known failure modes.

**Done when:** the model card is written and you can say where the model can and cannot be trusted.

---

## Phase 10 — Application & deployment

- [ ] Move notebook logic into `src/` modules with a simple pipeline (a Makefile or `python -m src.pipeline <step>`).
- [ ] Write `pytest` tests for cleaning, feature, and validation functions, focusing on the tricky ones (point-in-time joins, result encoding).
- [ ] **Serve predictions:** a FastAPI endpoint (`/predict/{season}/{round}`) and/or a Streamlit app.
- [ ] Containerize with Docker and deploy to a free host (Streamlit Community Cloud, Hugging Face Spaces, Render).
- [ ] Set up a **live loop for the 2026 season:** fetch after qualifying → predict → publish, then score after the race and log the result. This is real out-of-sample evaluation, which most portfolio projects never get.
- [ ] Monitoring: rolling metrics over time, feature drift checks, and a written retraining rule (e.g. "retrain after every race" or "when MAE degrades by X").
- [ ] Run CI on GitHub Actions: lint + tests on each push.

**Done when:** a public URL shows the upcoming race's predictions, and the scoring log updates after each race.

---

## Phase 11 — Communication

- [ ] **Analytics dashboard** built on the Phase 3 KPIs (Streamlit, Power BI, or Tableau), for a non-technical fan or strategist.
- [ ] **Technical report:** data, methods, validation, results, limitations.
- [ ] **One-page executive summary:** the question, the answer, how confident you are, and what it would take to improve.
- [ ] A 5–10 minute **presentation**. Practise explaining one causal result and one model limitation to a non-technical listener.
- [ ] A **portfolio README / blog post** telling the project's story, including what went wrong and what you changed.
- [ ] Data ethics and licensing note: FastF1, OpenF1, and Jolpica are unofficial and not affiliated with F1. Check each source's terms before redistributing raw data.

**Done when:** someone outside the project can understand what you found in 5 minutes, and a technical reviewer can reproduce it from the README.

---

## Cross-cutting habits (every phase)

- [ ] Commit small and often, with messages that say *why*.
- [ ] Update `docs/decisions.md` whenever you make a non-obvious choice.
- [ ] Keep notebooks for exploration and `src/` for anything reused. Promote code once you copy it a second time.
- [ ] Set seeds, pin dependencies, and make sure raw → processed is one command.
- [ ] Keep a short **learning log**: what surprised you, what you'd do differently next time.
