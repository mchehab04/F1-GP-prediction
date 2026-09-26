# F1 Race Prediction — Web Application & Visualization Plan

**Status:** Future Planning (To be implemented in Phases 10 & 11)  
**Related Docs:** [ROADMAP.md](../ROADMAP.md) (Phases 10 & 11), [docs/reports/](reports/)

---

## 1. Objective

To build an interactive, visually stunning web application that showcases the complete end-to-end data science lifecycle of this project:
1. **Interactive Predictive Tool:** Allow users to select an upcoming or historical Grand Prix weekend and see model predictions (finishing order, podium probability, and expected position gain/loss) right after qualifying.
2. **Exploratory Data Analysis (EDA) Showcase:** Visually present the key findings discovered through SQL exploration (teammate battles, circuit chaos, qualifying conversion, and car characteristics).
3. **Transparent Data Science & Engineering:** Provide model explainability (SHAP values, feature importance) and show technical reviewers the underlying SQL queries and pipeline architecture.

---

## 2. Website Information Architecture (The Story Flow)

The website will be organized into four cohesive sections that tell a story from raw data to machine learning predictions:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Hero Section: The "Sunday Race Predictor"                │
│    • Select Grand Prix & Season                             │
│    • Starting Grid vs. Predicted Finishing Position         │
│    • Win, Podium, and Points Probability Gauges             │
│    • "Why this prediction?" Driver Explainability Card      │
├─────────────────────────────────────────────────────────────┤
│ 2. The EDA Showcase: Insights from SQL                      │
│    • Tab 1: Garage Wars (Teammate H2H & Quali Gaps)         │
│    • Tab 2: Circuit DNA (Chaos, Volatility & Overtaking)    │
│    • Tab 3: Saturday Car vs. Sunday Car Matrix              │
│    • Tab 4: Starting Row Conversion Probabilities           │
├─────────────────────────────────────────────────────────────┤
│ 3. Model Performance & Evaluation                           │
│    • Benchmark Comparison (Model vs. "Finish = Grid")       │
│    • Walk-Forward Evaluation across 2022–2026               │
│    • Impact of 2026 Regulation Shift                        │
├─────────────────────────────────────────────────────────────┤
│ 4. Engineering & Architecture (For Technical Reviewers)     │
│    • Interactive Pipeline Diagram                           │
│    • "View SQL" modals for all EDA visuals                  │
│    • FastF1 & DuckDB data layer documentation               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Mapping SQL EDA Queries to Interactive Visuals

Every visual on the website will be powered directly by the SQL queries created during Phase 3 EDA:

| SQL Query in `sql/eda/` | Best Visual Representation | What the Visual Communicates |
|---|---|---|
| **`teammate_h2h/clean_h2h.sql`** | **Tug-of-War Split Bar Chart** | Compares head-to-head race finishes for teammates strictly in clean races (excluding DNF/DNS). |
| **`teammate_h2h/median_quali_gap.sql`** | **Dumbbell Delta Chart** (colored by team) | Shows the pure median one-lap pace gap (in seconds) between garage neighbors. |
| **`teammate_h2h/concordance_pct.sql`** | **Team Progress Bars / Gauges** | Displays how reliably winning Saturday qualifying translated into finishing ahead on Sunday. |
| **`teammate_h2h/q3_app_pct.sql`** | **Bullet Chart / Bar Chart** | Compares intra-team qualifying consistency and frequency of reaching Q3. |
| **`race_statistics/track_avg_dnfs.sql`** + **`track_overtaking.sql`** | **2D Quadrant Scatter Plot** | Maps **Track Chaos (Avg DNFs)** vs. **Overtaking (Avg Absolute Position Change)**. Identifies track archetypes (e.g. Monaco = low overtaking/high risk; Melbourne = high chaos). |
| **`race_statistics/driver_avg_penalties.sql`** | **Ranked Horizontal Bar Chart** | Highlights which drivers and power units suffered the most grid drop penalties. |
| **`race_statistics/p2w_conv_pct.sql`** | **Track-by-Track Conversion Chart** | Shows where pole position is almost guaranteed victory vs. tracks where pole is vulnerable. |
| **Rolling Average vs. Season Baseline** | **Dual-Line Progression Chart** | Shows actual finish against 3-race rolling momentum and season-to-date average across rounds. |

---

## 4. Technology Stack Options

When ready to implement in Phase 10, choose between two primary approaches based on time and portfolio goals:

### Option A: Streamlit (Fastest, 100% Python)
* **How it works:** Python-native framework that directly connects to DuckDB (`duckdb.connect('data/f1_db.duckdb', read_only=True)`).
* **Visualization Libraries:** Plotly (for interactive zoomable charts) and Altair.
* **Deployment:** 1-click free deployment via **Streamlit Community Cloud** directly connected to GitHub.
* **Pros:** Zero frontend (HTML/JS/CSS) overhead. Fastest path from Python/SQL to a live URL.
* **Cons:** Standard layout customization is somewhat constrained compared to bespoke web apps.

### Option B: React / Next.js + FastAPI (Maximum Visual Impact)
* **How it works:** A Python **FastAPI** backend serves model predictions and DuckDB query results as JSON. A **React/Next.js** frontend renders a custom F1 dark-mode UI.
* **Styling & Components:** F1-inspired dark aesthetic (carbon textures, neon team accents, driver helmet/portrait cards) using Tailwind CSS and Tremor/Recharts.
* **Deployment:** Frontend on Vercel, backend API containerized on Render or Hugging Face Spaces.
* **Pros:** Highest visual "WOW" factor for hiring managers; looks like an official Formula 1 digital product.
* **Cons:** Requires maintaining both frontend and backend codebases.

---

## 5. Next Steps & Checklist for Future Phases

When transitioning from EDA and modeling into web development, follow this checklist:

- [ ] **Phase 3 Completion:** Ensure all key exploratory findings have clean query files saved in `sql/eda/` and matching exports in `data/exports/`.
- [ ] **Phase 8 (Modeling):** Save trained model artifact (e.g. LightGBM `.booster` or `.pkl`) that takes a Grand Prix starting grid and outputs finish probabilities.
- [ ] **Data Layer Decision:** Choose whether the web app reads directly from `data/f1_db.duckdb` (via DuckDB-Wasm or Python backend) or reads pre-computed lightweight JSON/Parquet summaries.
- [ ] **Interactive Predictor Widget:** Implement the slider/dropdown allowing users to select a driver's grid slot and predict their finishing distribution.
- [ ] **SQL Query Inspector:** Add an expandable code drawer under each chart showing the exact SQL query used to calculate that metric.
