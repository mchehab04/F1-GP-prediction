# Streamlit Deep Dive: Architecture, Mental Model & F1 Project Implementation

**Status:** Reference Documentation & Architecture Guide  
**App Location:** `python/dashboard/`  
**Live URL (Local):** `http://localhost:8501`  
**Related Docs:** [web_visualization_plan.md](web_visualization_plan.md), [ROADMAP.md](../ROADMAP.md)

---

## 1. What is Streamlit?

**Streamlit** is an open-source Python framework designed specifically for data scientists and machine learning engineers to create interactive web applications without needing to write HTML, CSS, or JavaScript (though custom CSS can be injected for advanced styling).

### How It Differs from Traditional Web Frameworks

| Aspect | Traditional Web Dev (Flask / Django + React) | Streamlit |
|---|---|---|
| **Language Stack** | Python (backend) + JavaScript/TypeScript (frontend) + CSS | **100% Python** |
| **API Layer** | Must design REST/GraphQL endpoints (`/api/predict`) | **Direct Function Calls** (Python functions execute inside the app) |
| **State Syncing** | Redux, React state, WebSockets, client-server serialization | **Built-in Reactive Runtime** |
| **Development Speed** | Days to weeks per interactive dashboard | **Hours** |
| **Target Audience** | Full-stack software engineering teams | **Data Scientists, ML Engineers, Analysts** |

---

## 2. The Streamlit Mental Model: How It Works Under the Hood

Streamlit operates on a fundamentally simple and elegant execution paradigm:

### A. The Top-to-Bottom Execution Model
Unlike event-driven frontend frameworks (like React or Vue), **every time a user interacts with a widget (clicks a button, selects a dropdown, moves a slider), Streamlit re-executes the Python script from line 1 to the end.**

```
User Moves Grid Slider (e.g., P1 → P4)
                  │
                  ▼
Streamlit triggers rerun of `python/dashboard/app.py`
                  │
                  ▼
Reads new widget value → Re-computes prediction → Re-renders UI
```

### B. Why Doesn't This Make the App Slow?
Running from top-to-bottom on every click sounds inefficient, but Streamlit solves this with two core pillars:

1. **Intelligent Caching (`@st.cache_data`):**
   Functions that fetch data from DuckDB or compute heavy aggregations are decorated with `@st.cache_data`. When the script reruns, Streamlit checks the input arguments. If they haven't changed, **it returns the cached result from memory instantly in <1ms** rather than re-querying the database.
2. **Virtual DOM / Delta Updates:**
   Streamlit only transmits the specific UI elements that changed over a persistent WebSocket connection to the browser. Unchanged elements are not re-rendered.

---

## 3. How Streamlit is Used in This Project

Our F1 dashboard lives in `python/dashboard/` and is structured into a clean, modular architecture:

```
python/dashboard/
├── app.py                  # Main entry point, layout, and tab orchestration
├── data_layer.py           # Cached DuckDB queries and constructor color mappings
├── styles.css              # Bespoke 600+ line F1 dark theme styling & animations
├── .streamlit/config.toml  # Official theme and server configuration
└── components/
    ├── ui.py               # Reusable UI context managers, gantry intro, timing tower
    ├── charts.py           # Custom-themed Plotly figures (Tug-of-war, Dumbbell, DNA)
    └── predictor.py        # Grid simulator engine & interactive asphalt grid visualizer
```

### Component Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     data/f1_db.duckdb                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Read-only safe queries
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 python/dashboard/data_layer.py              │
│   • @st.cache_data(ttl=3600)                                │
│   • get_teammate_clean_h2h(), get_circuit_dna(), etc.       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Cached DataFrames
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  python/dashboard/app.py                    │
│   • Theme Injection via ui.inject_styles()                  │
│   • Season & Filter State                                   │
│   • Multi-Tab Routing                                       │
└──────────────┬───────────────┬───────────────┬──────────────┘
               │               │               │
               ▼               ▼               ▼
      ┌────────────────┐┌──────────────┐┌──────────────┐
      │  predictor.py  ││  charts.py   ││    ui.py     │
      │ • Grid Slider  ││ • Tug-of-War ││ • Timing     │
      │ • Probability  ││ • Dumbbell   ││   Tower      │
      │   Bars         ││ • 2D Chaos   ││ • Lights-Out │
      │ • Asphalt Grid ││ • Evolution  ││ • Card Wrap  │
      └────────────────┘└──────────────┘└──────────────┘
```

---

## 4. Key Project Files Explained

### 1. `data_layer.py` (Data Engine & Caching)
- **Role:** Direct bridge to DuckDB.
- **Key Pattern:** Uses `duckdb.connect(DB_PATH, read_only=True)` so queries never lock the database file or conflict with background tasks.
- **Caching:** Every query function is tagged with `@st.cache_data(ttl=3600)`. DuckDB only runs once per season/circuit; subsequent tab clicks hit RAM cache.

### 2. `ui.py` (Modular Design System)
- **Role:** Enforces visual consistency and eliminates boilerplate.
- **The `with ui.card(...)` Context Manager:**
  Instead of writing messy container divs repeatedly, sections are wrapped cleanly:
  ```python
  with ui.card("h2h", "Garage Wars", "Race head-to-head"):
      st.plotly_chart(...)
  ```
- **Custom HTML Components:** Injects the animated 5-light FIA gantry sequence (`lights_out_intro`) and the vertical timing tower leaderboard.

### 3. `predictor.py` (Interactive Simulator & Track Asphalt)
- **Role:** Simulates Sunday finishing positions and win/podium probabilities.
- **Starting Grid Visualizer (`_starting_grid`):** Generates an authentic staggered 2-wide F1 starting grid on asphalt using CSS grid layout, highlighting the user's selected driver in constructor colors and marking their expected finish position.

### 4. `charts.py` (Plotly Integration)
- **Role:** Renders all 5 EDA visualizations.
- **Theme Unification (`apply_f1_theme`):** Safely merges layout dictionaries via Python's `.update()` to eliminate Plotly keyword argument conflicts while enforcing dark transparent backgrounds and F1 typography (`Titillium Web`).

### 5. `styles.css` & `.streamlit/config.toml` (Aesthetics)
- **Role:** Overcomes the standard "bland" default Streamlit look.
- **Features:** 
  - Ambient radial gradients with Ferrari-red glow.
  - Custom font family (`Titillium Web` + `JetBrains Mono`).
  - Checkered flag dividers and custom pill tabs.
  - Hidden default Streamlit chrome (hides menu bar, deploy buttons, and footer).

---

## 5. Automated Testing: How We Verified the App

Streamlit includes a native headless testing framework: `streamlit.testing.v1.AppTest`.

In `tests/test_dashboard_e2e.py`, we simulate an entire browser session programmatically without opening a window:

```python
from streamlit.testing.v1 import AppTest

# 1. Load the app in memory
at = AppTest.from_file("python/dashboard/app.py", default_timeout=30)
at.run()
assert len(at.exception) == 0

# 2. Programmatically select seasons and assert zero exceptions
at.selectbox[0].select(2023).run()
assert len(at.exception) == 0
```

This tests every widget, query, and chart generation in seconds.

---

## 6. How Streamlit Fits into the Next Project Phases

### Phase 10: Model Serving
When we finish Phase 7 (Feature Engineering) and Phase 8 (LightGBM Modeling), we won't need to rewrite the web app. 

We will simply:
1. Load the trained model artifact (`model = joblib.load('models/lgbm_ranker.pkl')`) inside `predictor.py`.
2. Pass the selected driver's grid slot and track features to `model.predict()`.
3. Display the real ML prediction directly in the existing UI!

### Free Cloud Deployment (Streamlit Community Cloud)
When ready for portfolio sharing:
1. Push your code to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with GitHub.
3. Select this repo and branch `main`, pointing to `python/dashboard/app.py`.
4. Streamlit deploys a public HTTPS URL (e.g. `https://f1-race-prediction.streamlit.app`) for free.
