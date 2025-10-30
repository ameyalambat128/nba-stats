# Project Context
- Title: Pace and Efficiency – The Modern NBA Revolution.
- Team: Karanbir Singh Grewal, Ameya Lambat, Aidan Dubel (from project brief).
- Objective: Quantify evolution of NBA playing styles, identify era clusters, predict team success from pace/efficiency, and measure three-point revolution across 1946–present dataset.

# Data Sources
- Kaggle NBA historical dataset (`nba-dataset/csv/*.csv`, `nba-dataset/nba.sqlite`) covering ~64K games, 5K players.
- Supplementary references: NBA.com, Statmuse (per brief) for validation.

# Current Insights (from brief)
- Pace vs. time shows U-shaped trend with inflection in 2014–15.
- Three-point attempts grow exponentially post-2014; AST/TOV improving.
- Four playing-style clusters; pace-efficiency correlation shifts from negative to positive.
- Challenges include missing advanced stats pre-1980, rule-change non-stationarity, and possession estimation gaps.

# Working Guidelines
- Use Python + pandas for the pipeline; keep code clean with descriptive filenames and functions.
- Prefer straightforward data access path (CSV or SQLite) as needed.
- Maintain concise commits without labels or watermarks.
- Ask clarifying questions when assumptions arise.
- Document evolving context in this file for future agents.
- Development branches are person-specific (e.g., current work on `ameya` branch).
- Intermediate artifacts live under `data/processed/` (CSV format, directory git-ignored).
- Standardize shared visualizations on Matplotlib (Seaborn optional for styling).
- Dependencies managed via project virtual environment `.venv` with packages listed in `requirements.txt`.
- Jupyter notebooks should use the `nba-stats (venv)` kernel registered via `ipykernel`.
- Notebook templates include a helper to add the repo root to `sys.path`; reuse that snippet to avoid `ModuleNotFoundError` when importing from `src`.
- Data ingestion defaults to dataset paths relative to the repository root (`nba-dataset/`).

# Pipeline Vision (current draft)
1. Ingest data from CSV/SQLite into unified schema with season metadata.
2. Clean and harmonize team/player identifiers; handle missing advanced stats.
3. Engineer pace, efficiency, shooting distribution, AST/TOV, and era indicators.
4. Perform exploratory analysis to validate trends and detect change points.
5. Train predictive/clustering models (logistic, linear, ensembles, K-means).
6. Summarize findings via visualizations and dashboards; iterate on insights.

# Recent Updates
- Added `src/pipeline/season_summary.py` to reshape game stats into team-level features and write season aggregates to `data/processed/`.
- Created `src/config/team_aliases.json` with canonical franchise mappings consumed by `Preprocessor`.
- Notebook scaffold: `notebooks/01_data_overview.ipynb` demonstrates basic ingestion checks.
- Virtual environment now bundles scikit-learn, statsmodels, pyarrow, and Jupyter tooling for modeling/EDA workflows.
