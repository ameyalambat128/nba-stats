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

# Pipeline Vision (current draft)
1. Ingest data from CSV/SQLite into unified schema with season metadata.
2. Clean and harmonize team/player identifiers; handle missing advanced stats.
3. Engineer pace, efficiency, shooting distribution, AST/TOV, and era indicators.
4. Perform exploratory analysis to validate trends and detect change points.
5. Train predictive/clustering models (logistic, linear, ensembles, K-means).
6. Summarize findings via visualizations and dashboards; iterate on insights.

