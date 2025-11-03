"""
Validation helpers for derived NBA metrics.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def _format_identifier(row: pd.Series) -> str:
    team = row.get("TEAM_ID", "UNKNOWN")
    season = row.get("SEASON_YEAR", "N/A")
    playoffs = row.get("IS_PLAYOFFS", False)
    scope = "Playoffs" if playoffs else "Regular"
    return f"{team} {season} ({scope})"


def validate_team_summary(
    summary: pd.DataFrame,
    *,
    pace_bounds: tuple[float, float] = (40.0, 150.0),
    efficiency_bounds: tuple[float, float] = (70.0, 150.0),
    possessions_bounds: tuple[float, float] = (40.0, 150.0),
) -> list[str]:
    """
    Inspect a team-season summary and report any out-of-range metrics.

    Returns a list of human-readable issue strings; an empty list means all checks passed.
    """
    issues: list[str] = []
    if summary.empty:
        return issues

    def _flag_out_of_bounds(column: str, bounds: tuple[float, float]) -> None:
        if column not in summary.columns:
            return
        series = summary[column]
        mask = series.notna() & ~series.between(bounds[0], bounds[1])
        if mask.any():
            offenders = summary.loc[mask, ["TEAM_ID", "SEASON_YEAR", "IS_PLAYOFFS", column]]
            for _, row in offenders.iterrows():
                ident = _format_identifier(row)
                issues.append(f"{column} out of bounds for {ident}: {row[column]:.2f}")

    _flag_out_of_bounds("PACE", pace_bounds)
    _flag_out_of_bounds("OFF_EFF_PER_100", efficiency_bounds)
    _flag_out_of_bounds("DEF_EFF_PER_100", efficiency_bounds)

    if "TOTAL_EST_POSSESSIONS" in summary.columns and "GAMES_PLAYED" in summary.columns:
        avg_possessions = summary["TOTAL_EST_POSSESSIONS"] / summary["GAMES_PLAYED"].replace(0, pd.NA)
        mask = avg_possessions.notna() & ~avg_possessions.between(possessions_bounds[0], possessions_bounds[1])
        if mask.any():
            offenders = summary.loc[mask, ["TEAM_ID", "SEASON_YEAR", "IS_PLAYOFFS"]].copy()
            offenders["AVG_POSSESSIONS"] = avg_possessions[mask]
            for _, row in offenders.iterrows():
                ident = _format_identifier(row)
                issues.append(f"Average possessions out of bounds for {ident}: {row['AVG_POSSESSIONS']:.2f}")
        negative_mask = summary["TOTAL_EST_POSSESSIONS"] < 0
        if negative_mask.any():
            offenders = summary.loc[negative_mask, ["TEAM_ID", "SEASON_YEAR", "IS_PLAYOFFS", "TOTAL_EST_POSSESSIONS"]]
            for _, row in offenders.iterrows():
                ident = _format_identifier(row)
                issues.append(f"Negative total possessions for {ident}: {row['TOTAL_EST_POSSESSIONS']:.2f}")

    if "WIN_PCT" in summary.columns:
        mask = summary["WIN_PCT"].notna() & ~summary["WIN_PCT"].between(0, 1)
        if mask.any():
            offenders = summary.loc[mask, ["TEAM_ID", "SEASON_YEAR", "IS_PLAYOFFS", "WIN_PCT"]]
            for _, row in offenders.iterrows():
                ident = _format_identifier(row)
                issues.append(f"Win pct out of bounds for {ident}: {row['WIN_PCT']:.3f}")

    return issues


def assert_team_summary_valid(summary: pd.DataFrame, **kwargs) -> None:
    """
    Raise ValueError when validation issues are detected.
    """
    issues = validate_team_summary(summary, **kwargs)
    if issues:
        formatted = "\n".join(f"- {issue}" for issue in issues)
        raise ValueError(f"Team summary validation failed with {len(issues)} issue(s):\n{formatted}")
