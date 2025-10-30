"""
Feature engineering utilities for deriving pace, efficiency, and shooting metrics.
"""

from __future__ import annotations

import pandas as pd


def compute_pace(df: pd.DataFrame, possessions_col: str, minutes_col: str = "MIN") -> pd.DataFrame:
    """
    Compute pace metric (possessions per 48 minutes).

    Parameters
    ----------
    df:
        DataFrame containing possession estimates and minutes played.
    possessions_col:
        Column representing team possessions.
    minutes_col:
        Column representing total minutes played for the team in the game.
    """
    result = df.copy()
    if possessions_col not in result.columns or minutes_col not in result.columns:
        raise ValueError(f"Columns {possessions_col!r} and {minutes_col!r} must exist to calculate pace.")

    result["PACE"] = (result[possessions_col] * 48) / result[minutes_col]
    return result


def compute_efficiency(df: pd.DataFrame, points_col: str, possessions_col: str, prefix: str = "OFF") -> pd.DataFrame:
    """
    Compute offensive or defensive efficiency (points per 100 possessions).

    Parameters
    ----------
    points_col:
        Column containing points scored (or allowed if calculating defensive efficiency).
    possessions_col:
        Column containing possessions.
    prefix:
        Prefix for naming the derived efficiency column, defaults to 'OFF'.
    """
    result = df.copy()
    if points_col not in result.columns or possessions_col not in result.columns:
        raise ValueError(f"Columns {points_col!r} and {possessions_col!r} must exist to calculate efficiency.")

    result[f"{prefix}_EFF_PER_100"] = (result[points_col] * 100) / result[possessions_col]
    return result


def compute_shot_profile(df: pd.DataFrame, *, fgm_col: str, fga_col: str, fg3m_col: str, fg3a_col: str) -> pd.DataFrame:
    """
    Derive shooting distribution metrics.

    Adds:
        * THREE_POINT_RATE: fraction of shot attempts that are threes.
        * THREE_POINT_SHARE_OF_PTS: fraction of points coming from threes.
        * EFFECTIVE_FG_PCT: efficiency adjusted for three-point value.
    """
    result = df.copy()
    missing = [col for col in (fgm_col, fga_col, fg3m_col, fg3a_col) if col not in result.columns]
    if missing:
        raise ValueError(f"Missing required columns for shot profile: {missing}")

    result["THREE_POINT_RATE"] = result[fg3a_col] / result[fga_col].replace(0, pd.NA)
    result["THREE_POINT_SHARE_OF_PTS"] = (3 * result[fg3m_col]) / (2 * result[fgm_col] + result[fg3m_col]).replace(0, pd.NA)
    result["EFFECTIVE_FG_PCT"] = (result[fgm_col] + 0.5 * result[fg3m_col]) / result[fga_col].replace(0, pd.NA)
    return result


def compute_ball_security(df: pd.DataFrame, *, assists_col: str, turnovers_col: str) -> pd.DataFrame:
    """
    Calculate assist-to-turnover ratio and turnover percentage.
    """
    result = df.copy()
    missing = [col for col in (assists_col, turnovers_col) if col not in result.columns]
    if missing:
        raise ValueError(f"Missing required columns for ball security: {missing}")

    result["AST_TOV_RATIO"] = result[assists_col] / result[turnovers_col].replace(0, pd.NA)
    result["TURNOVER_PCT"] = result[turnovers_col] / (result[assists_col] + result[turnovers_col]).replace(0, pd.NA)
    return result

