"""
Preprocessing utilities for cleaning and standardizing NBA game data.

This module focuses on:
    * Harmonizing team and franchise identifiers across eras.
    * Aligning game, line score, and box score tables.
    * Filling or estimating missing advanced statistics (e.g., possessions).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

DEFAULT_ALIAS_PATH = Path(__file__).resolve().parent / "config" / "team_aliases.json"


@dataclass
class TeamAlias:
    """Mapping record for team alias harmonization."""

    canonical_id: str
    aliases: Iterable[str]


class Preprocessor:
    """Bundle of preprocessing routines applied to raw ingested data."""

    def __init__(self, *, team_aliases: Optional[Iterable[TeamAlias]] = None) -> None:
        if team_aliases is None:
            team_aliases = load_team_aliases()
        self.team_aliases = list(team_aliases)
        self._alias_map = self._build_alias_map()

    def _build_alias_map(self) -> dict[str, str]:
        mapping = {}
        for alias in self.team_aliases:
            for name in alias.aliases:
                mapping[name.upper()] = alias.canonical_id.upper()
        return mapping

    def normalize_team_ids(self, df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """
        Normalize team identifiers across provided columns.

        Parameters
        ----------
        df:
            Input dataframe to transform.
        columns:
            Columns containing team abbreviations or IDs to normalize.
        """
        result = df.copy()
        for col in columns:
            if col not in result.columns:
                continue
            result[col] = result[col].astype(str).str.upper().map(self._alias_map).fillna(result[col].astype(str).str.upper())
        return result

    def attach_season(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Add derived season metadata for a given game date column.

        Season convention used: if date month >= October (10), season year is that calendar year,
        else date belongs to previous year season (e.g., Jan 2015 => 2014 season).
        """
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column])
        season_year = result[date_column].dt.year.where(result[date_column].dt.month >= 10, result[date_column].dt.year - 1)
        result["SEASON_YEAR"] = season_year
        result["SEASON_LABEL"] = season_year.astype(str) + "-" + (season_year + 1).astype(str).str[-2:]
        return result

    def estimate_possessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Estimate possessions using standard formula when unavailable.

        Formula (team level): 0.5 * ((FGA + 0.4 * FTA - 1.07 * (ORB / (ORB + DRB)) * (FGA - FG) + TOV) +
                                     (OppFGA + 0.4 * OppFTA - 1.07 * (OppORB / (OppORB + OppDRB)) * (OppFGA - OppFG) + OppTOV))
        """
        result = df.copy()
        required_cols = [
            "FGA",
            "FGM",
            "FTA",
            "TOV",
            "OREB",
            "DREB",
            "OPP_FGA",
            "OPP_FGM",
            "OPP_FTA",
            "OPP_TOV",
            "OPP_OREB",
            "OPP_DREB",
        ]
        missing_cols = [col for col in required_cols if col not in result.columns]
        if missing_cols:
            raise ValueError(f"Cannot estimate possessions; missing columns: {missing_cols}")

        orb_factor = result["OREB"] / (result["OREB"] + result["DREB"]).replace(0, pd.NA)
        opp_orb_factor = result["OPP_OREB"] / (result["OPP_OREB"] + result["OPP_DREB"]).replace(0, pd.NA)

        team_possessions = result["FGA"] + 0.4 * result["FTA"] - 1.07 * orb_factor * (result["FGA"] - result["FGM"]) + result["TOV"]
        opp_possessions = (
            result["OPP_FGA"]
            + 0.4 * result["OPP_FTA"]
            - 1.07 * opp_orb_factor * (result["OPP_FGA"] - result["OPP_FGM"])
            + result["OPP_TOV"]
        )

        result["EST_POSSESSIONS"] = 0.5 * (team_possessions + opp_possessions)
        return result


def load_team_aliases(path: Optional[Path] = None) -> list[TeamAlias]:
    """
    Load team aliases from JSON configuration.

    Parameters
    ----------
    path:
        Optional custom path; defaults to config/team_aliases.json alongside this module.
    """
    alias_path = path or DEFAULT_ALIAS_PATH
    with alias_path.open("r", encoding="utf-8") as fh:
        raw_aliases = json.load(fh)
    return [TeamAlias(**entry) for entry in raw_aliases]
