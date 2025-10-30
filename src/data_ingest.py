"""
Data ingestion utilities for the NBA pace and efficiency project.

Responsibilities:
    * Load raw tables from CSV or SQLite sources.
    * Provide schema-aware accessors for common tables (games, teams, players).
    * Attach season metadata and identify regular-season vs playoff records.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
import sqlite3


DEFAULT_DATA_ROOT = Path("nba-dataset")


@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration describing where datasets are stored."""

    csv_dir: Path = DEFAULT_DATA_ROOT / "csv"
    sqlite_path: Path = DEFAULT_DATA_ROOT / "nba.sqlite"

    def validate(self) -> None:
        """Ensure the configured paths exist."""
        if not self.csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {self.csv_dir}")
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")


class NBADataIngestor:
    """
    Loader class that gives convenient access to raw NBA datasets.

    Parameters
    ----------
    source_config:
        Configuration object containing CSV directory and SQLite database path.
    prefer_sqlite:
        When True, attempts to pull tables from SQLite before falling back to CSV.
    """

    def __init__(self, source_config: Optional[DataSourceConfig] = None, *, prefer_sqlite: bool = True) -> None:
        self.source_config = source_config or DataSourceConfig()
        self.source_config.validate()
        self.prefer_sqlite = prefer_sqlite

    def list_csv_tables(self) -> Dict[str, Path]:
        """Return available CSV tables keyed by table name (stem)."""
        return {p.stem: p for p in self.source_config.csv_dir.glob("*.csv")}

    def read_table(self, table: str, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """
        Load a table from SQLite or CSV.

        Parameters
        ----------
        table:
            Logical table name (e.g., 'game', 'line_score').
        columns:
            Optional subset of columns to select when supported.
        """
        if self.prefer_sqlite:
            try:
                return self._read_sqlite_table(table, columns=columns)
            except (sqlite3.DatabaseError, FileNotFoundError, ValueError):
                pass

        return self._read_csv_table(table, columns=columns)

    def _read_sqlite_table(self, table: str, *, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """Internal helper to read a table from the SQLite database."""
        with sqlite3.connect(self.source_config.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                if columns:
                    col_clause = ", ".join(columns)
                else:
                    col_clause = "*"
                query = f"SELECT {col_clause} FROM {table}"
                df = pd.read_sql_query(query, conn)
            except sqlite3.OperationalError as exc:
                raise ValueError(f"Table '{table}' not found in SQLite database") from exc
        return df

    def _read_csv_table(self, table: str, *, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """Internal helper to read a table from CSV exports."""
        csv_files = self.list_csv_tables()
        if table not in csv_files:
            raise ValueError(f"Table '{table}' not found in CSV directory {self.source_config.csv_dir}")
        df = pd.read_csv(csv_files[table])
        if columns:
            missing = set(columns) - set(df.columns)
            if missing:
                raise ValueError(f"Columns {missing} not found in table '{table}'")
            df = df.loc[:, list(columns)]
        return df

    # -- Domain Specific Accessors -------------------------------------------------

    def games(self, *, playoffs_only: bool = False, regular_season_only: bool = False) -> pd.DataFrame:
        """
        Retrieve game-level records with season stage flags.

        The 'game' table uses a GAME_ID suffix convention (e.g., '001' regular season, '002' preseason,
        '004' playoffs). This helper filters based on suffixes for reproducibility.
        """
        game_df = self.read_table("game")
        if playoffs_only and regular_season_only:
            raise ValueError("Cannot request both playoffs_only and regular_season_only")

        suffix = game_df["GAME_ID"].astype(str).str[-3:]
        is_regular = suffix == "001"
        is_playoffs = suffix == "004"

        if playoffs_only:
            game_df = game_df.loc[is_playoffs].copy()
        elif regular_season_only:
            game_df = game_df.loc[is_regular].copy()

        game_df["IS_REGULAR_SEASON"] = is_regular
        game_df["IS_PLAYOFFS"] = is_playoffs
        return game_df

    def line_scores(self) -> pd.DataFrame:
        """Return per-team-per-game line score data."""
        return self.read_table("line_score")

    def other_stats(self) -> pd.DataFrame:
        """Return additional box score statistics for games."""
        return self.read_table("other_stats")

    def team_info(self) -> pd.DataFrame:
        """Return team metadata."""
        return self.read_table("team_info_common")

    def player_info(self) -> pd.DataFrame:
        """Return player metadata."""
        return self.read_table("common_player_info")

