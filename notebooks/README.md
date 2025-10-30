# Notebooks

- Use this directory for exploratory analysis and visualization prototypes.
- Keep notebooks lightweight; move reusable logic into `src/` modules.
- Naming convention: `<sequence>_<focus>.ipynb` (e.g., `01_data_overview.ipynb`).
- Choose the `nba-stats (venv)` kernel to run notebooks with the project environment.
- If a notebook cannot import `src`, prepend a cell that appends the project root to `sys.path` (see `01_data_overview.ipynb` for example).

## Current Notebooks
- `01_data_overview.ipynb`: quick table listings and regular vs playoff sampling.
- `02_era_analysis.ipynb`: pace, three-point, and efficiency era trends using regular-season aggregates.
