"""
Aggregation routines for team, season, and player level summaries.
"""

from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd


def aggregate_team_season(
    df: pd.DataFrame,
    *,
    group_cols: Optional[Iterable[str]] = None,
    metrics: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Aggregate game-level data to team-season summaries.

    Parameters
    ----------
    df:
        Game-level dataframe with at least team identifier and season columns.
    group_cols:
        Additional columns to group by (defaults to TEAM_ID, SEASON_YEAR, IS_PLAYOFFS flag).
    metrics:
        Optional mapping of column -> aggregation function (e.g., {'PACE': 'mean'}).
    """
    if group_cols is None:
        group_cols = ["TEAM_ID", "SEASON_YEAR", "IS_PLAYOFFS"]
    if metrics is None:
        metrics = {
            "PACE": "mean",
            "OFF_EFF_PER_100": "mean",
            "DEF_EFF_PER_100": "mean",
            "THREE_POINT_RATE": "mean",
            "AST_TOV_RATIO": "mean",
            "WIN": "mean",
        }

    available_cols = set(df.columns)
    missing_metrics = [col for col in metrics if col not in available_cols]
    if missing_metrics:
        raise ValueError(f"Cannot aggregate metrics; missing columns: {missing_metrics}")

    agg_df = df.groupby(list(group_cols), dropna=False).agg(metrics).reset_index()
    agg_df = agg_df.rename(columns={"WIN": "WIN_PCT"})
    return agg_df


def aggregate_player_season(
    df: pd.DataFrame,
    *,
    player_id_col: str = "PLAYER_ID",
    season_col: str = "SEASON_YEAR",
    playoff_col: str = "IS_PLAYOFFS",
    metrics: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Aggregate player game stats to season-level summaries.
    """
    if metrics is None:
        metrics = {
            "MIN": "sum",
            "PTS": "sum",
            "FGA": "sum",
            "FGM": "sum",
            "FG3A": "sum",
            "FG3M": "sum",
            "AST": "sum",
            "TOV": "sum",
            "REB": "sum",
        }

    required_cols = set([player_id_col, season_col, playoff_col])
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for player aggregation: {missing}")

    agg_df = (
        df.groupby([player_id_col, season_col, playoff_col], dropna=False)
        .agg(metrics)
        .reset_index()
    )
    return agg_df

