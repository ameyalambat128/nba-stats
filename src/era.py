"""
Utilities for working with predefined NBA era segments.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

DEFAULT_ERA_PATH = Path(__file__).resolve().parent / "config" / "era_segments.json"


@dataclass(frozen=True)
class EraDefinition:
    """Definition of an era bounded by (inclusive) start and end season years."""

    key: str
    label: str
    start_year: int
    end_year: Optional[int]
    description: str | None = None

    def contains(self, season_year: int) -> bool:
        upper_bound = self.end_year if self.end_year is not None else float("inf")
        return self.start_year <= season_year <= upper_bound


@lru_cache(maxsize=1)
def load_era_definitions(path: Optional[Path] = None) -> tuple[EraDefinition, ...]:
    """
    Load era definitions from JSON configuration.
    """
    era_path = path or DEFAULT_ERA_PATH
    with era_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    eras = tuple(EraDefinition(**entry) for entry in raw)
    if not eras:
        raise ValueError("Era definition file is empty.")
    return eras


def resolve_era_for_year(season_year: int, *, eras: Optional[Iterable[EraDefinition]] = None) -> EraDefinition:
    """
    Determine which era a given season year belongs to.
    """
    era_list = tuple(eras) if eras is not None else load_era_definitions()
    for era in era_list:
        if era.contains(season_year):
            return era
    raise ValueError(f"No era definition found for season year {season_year}")


def annotate_era(
    df: pd.DataFrame,
    *,
    season_col: str = "SEASON_YEAR",
    eras: Optional[Iterable[EraDefinition]] = None,
) -> pd.DataFrame:
    """
    Append era metadata columns to a dataframe containing season information.

    Adds ERA_KEY, ERA_LABEL, ERA_START_YEAR, ERA_END_YEAR columns.
    """
    if season_col not in df.columns:
        raise ValueError(f"Cannot annotate era without '{season_col}' column.")

    era_list = tuple(eras) if eras is not None else load_era_definitions()

    def _resolve(year: float) -> EraDefinition | None:
        if pd.isna(year):
            return None
        year_int = int(year)
        for era in era_list:
            if era.contains(year_int):
                return era
        return None

    result = df.copy()
    era_series = result[season_col].apply(_resolve)
    result["ERA_KEY"] = era_series.map(lambda era: era.key if era else pd.NA)
    result["ERA_LABEL"] = era_series.map(lambda era: era.label if era else pd.NA)
    result["ERA_START_YEAR"] = era_series.map(lambda era: era.start_year if era else pd.NA)
    result["ERA_END_YEAR"] = era_series.map(lambda era: era.end_year if (era and era.end_year is not None) else pd.NA)
    return result


def summarize_by_era(
    df: pd.DataFrame,
    *,
    weight_col: str = "GAMES_PLAYED",
    metrics: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Produce era-level aggregates from a team-season dataframe.

    Weighted averages use the supplied weight column (default: games played).
    Totals (e.g., possessions) are summed.
    """
    if metrics is None:
        metrics = ["PACE", "OFF_EFF_PER_100", "DEF_EFF_PER_100", "THREE_POINT_RATE", "AST_TOV_RATIO"]

    required_cols = {"ERA_KEY", "ERA_LABEL", weight_col}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Cannot summarize by era; missing columns: {missing}")

    grouped = df.groupby(["ERA_KEY", "ERA_LABEL", "IS_PLAYOFFS", "ERA_START_YEAR", "ERA_END_YEAR"], dropna=False)
    records: list[dict[str, object]] = []
    for (era_key, era_label, is_playoffs, era_start, era_end), group in grouped:
        record: dict[str, object] = {
            "ERA_KEY": era_key,
            "ERA_LABEL": era_label,
            "ERA_START_YEAR": era_start,
            "ERA_END_YEAR": era_end,
            "IS_PLAYOFFS": is_playoffs,
            "TOTAL_GAMES": group[weight_col].fillna(0).sum(),
            "TEAM_SEASONS": len(group),
        }

        weights = group[weight_col].fillna(0)
        total_weight = weights.sum()

        for metric in metrics:
            if metric not in group.columns:
                continue
            values = group[metric]
            valid_mask = values.notna() & weights.gt(0)
            if valid_mask.any() and total_weight > 0:
                metric_weight = weights[valid_mask]
                record[metric] = (values[valid_mask] * metric_weight).sum() / metric_weight.sum()
            else:
                record[metric] = pd.NA

        if "TOTAL_EST_POSSESSIONS" in group.columns:
            record["TOTAL_EST_POSSESSIONS"] = group["TOTAL_EST_POSSESSIONS"].fillna(0).sum()
        if "WIN_PCT" in group.columns:
            valid_mask = group["WIN_PCT"].notna() & weights.gt(0)
            if valid_mask.any() and total_weight > 0:
                win_weight = weights[valid_mask]
                record["WEIGHTED_WIN_PCT"] = (group.loc[valid_mask, "WIN_PCT"] * win_weight).sum() / win_weight.sum()
            else:
                record["WEIGHTED_WIN_PCT"] = pd.NA

        records.append(record)

    era_df = pd.DataFrame.from_records(records)
    if not era_df.empty:
        era_df = era_df.sort_values(["ERA_START_YEAR", "IS_PLAYOFFS"]).reset_index(drop=True)
    return era_df
