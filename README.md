# Pace and Efficiency: The Modern NBA Revolution

Welcome! This repository hosts our CSE 572 project exploring how NBA playing styles evolved over the league's 75+ years, with a focus on pace, efficiency, and the rise of the three-point shot.

## Project Goals

- Quantify the evolution of playing style and identify distinct eras.
- Predict team success using pace and efficiency metrics.
- Measure the impact of the three-point revolution and modern offensive strategies.

For deeper context and historical notes, see `AGENTS.md`.

## Repository Layout

- `src/`: Python package housing reusable pipeline code.
  - `data_ingest.py`: Utilities for loading tables from the Kaggle dataset (CSV or SQLite) with regular-season/playoff filtering.
  - `preprocess.py`: Cleaning helpers for aligning team IDs, tagging seasons, and estimating possessions.
  - `features.py`: Feature engineering routines (pace, offensive/defensive efficiency, shot profile, AST/TOV).
  - `aggregation.py`: Season- and player-level aggregation helpers.
- `src/pipeline/`: Orchestrated workflows (e.g., team game features + season summaries).
- `notebooks/`: Jupyter notebooks for exploratory analysis (`README.md` inside lists naming conventions).
- `data/processed/`: Git-ignored directory for cached season/team/player aggregates and intermediate files (stored as CSV for simplicity).
- `nba-dataset/`: **Not tracked by git**. Place the Kaggle CSVs or `nba.sqlite` here.
- `AGENTS.md`: Working log for agents and context keepers.

## Getting Started

1. Ensure Python 3.10+ is available.
2. Create/activate the project virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Download the Kaggle NBA dataset and drop either the `csv/` directory or `nba.sqlite` database into `nba-dataset/`.

## Using the Pipeline Modules

```python
from src.data_ingest import NBADataIngestor
from src.preprocess import Preprocessor
from src.features import compute_pace, compute_efficiency
from src.aggregation import aggregate_team_season

ingestor = NBADataIngestor()
games = ingestor.games(regular_season_only=True)
line_scores = ingestor.line_scores()

# Merge, preprocess, and engineer features as needed...
```

For a quick aggregate export:

```python
from src.pipeline import generate_team_season_summary

summary = generate_team_season_summary(ingestor, regular_season_only=True)
```

More detailed usage patterns will be captured in forthcoming notebooks and module docstrings.

## Collaboration Notes
- Follow the clean-code conventions (descriptive filenames/functions, minimal duplication).
- Commit frequently with concise messages (e.g., `add team aggregation`).
- Keep notebooks tidy; move reusable logic into `src/`.
- Record major context decisions in `AGENTS.md`.
- Use Matplotlib (with Seaborn as needed) for shared visualizations unless otherwise noted.

## Next Steps
- Flesh out preprocessing pipelines (team alias mapping, possession estimation).
- Implement baseline models (logistic win classification, season-level regression, clustering).
- Expand visualizations for pace trends and era detection.

Feel free to reach out on any open questions or assumptions before diving in! Let's build something smart and shareable. 
