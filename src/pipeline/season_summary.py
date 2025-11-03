"""
Utilities for assembling game-level feature sets and aggregating to team-season summaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.aggregation import aggregate_team_season
from src.data_ingest import NBADataIngestor
from src.features import compute_ball_security, compute_efficiency, compute_pace, compute_shot_profile
from src.preprocess import Preprocessor
from src.era import annotate_era, summarize_by_era

DEFAULT_OUTPUT_DIR = Path("data/processed")


def build_team_game_features(
    ingestor: NBADataIngestor,
    preprocessor: Optional[Preprocessor] = None,
    *,
    playoffs_only: bool = False,
    regular_season_only: bool = False,
) -> pd.DataFrame:
    """
    Construct team-level game dataframe enriched with pace/efficiency features.

    Parameters
    ----------
    ingestor:
        Data ingestor instance for accessing raw tables.
    preprocessor:
        Optional preprocessor; defaults to base configuration when omitted.
    playoffs_only / regular_season_only:
        Filter game scope. Only one of these may be True at a time.
    """
    if playoffs_only and regular_season_only:
        raise ValueError("Only one of playoffs_only or regular_season_only can be True.")

    preprocessor = preprocessor or Preprocessor()
    games_raw = ingestor.games(playoffs_only=playoffs_only, regular_season_only=regular_season_only)
    games_long = _reshape_games_to_long(games_raw)
    games_long = preprocessor.normalize_team_ids(games_long, ["TEAM_ABBREVIATION", "OPP_TEAM_ABBREVIATION"])
    games_long = preprocessor.attach_season(games_long, "GAME_DATE")
    games_long["GAME_DATE"] = pd.to_datetime(games_long["GAME_DATE"])

    # Estimate possessions and derive pace/efficiency metrics.
    enriched = preprocessor.estimate_possessions(games_long)
    enriched["MINUTES_PLAYED"] = 48 + 5 * enriched["OVERTIME_PERIODS"]

    enriched = compute_pace(enriched, possessions_col="EST_POSSESSIONS", minutes_col="MINUTES_PLAYED")
    enriched = compute_efficiency(enriched, points_col="PTS", possessions_col="EST_POSSESSIONS", prefix="OFF")
    enriched = compute_efficiency(enriched, points_col="OPP_PTS", possessions_col="EST_POSSESSIONS", prefix="DEF")
    enriched = compute_shot_profile(
        enriched,
        fgm_col="FGM",
        fga_col="FGA",
        fg3m_col="FG3M",
        fg3a_col="FG3A",
    )
    enriched = compute_ball_security(enriched, assists_col="AST", turnovers_col="TOV")
    return enriched


def generate_team_season_summary(
    ingestor: NBADataIngestor,
    *,
    preprocessor: Optional[Preprocessor] = None,
    playoffs_only: bool = False,
    regular_season_only: bool = False,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    save: bool = True,
    return_era_summary: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build team-season aggregates and optionally persist to disk.

    When return_era_summary is True, a tuple of (team_summary, era_summary) is returned.
    """
    features = build_team_game_features(
        ingestor,
        preprocessor=preprocessor,
        playoffs_only=playoffs_only,
        regular_season_only=regular_season_only,
    )
    summary = aggregate_team_season(features)
    summary = annotate_era(summary)
    era_summary = summarize_by_era(summary)

    if save:
        output_dir.mkdir(parents=True, exist_ok=True)
        tag = "playoffs" if playoffs_only else "regular" if regular_season_only else "all"
        summary.to_csv(output_dir / f"team_season_{tag}.csv", index=False)
        era_summary.to_csv(output_dir / f"team_era_{tag}.csv", index=False)

    if return_era_summary:
        return summary, era_summary
    return summary


# --------------------------------------------------------------------------- #
# Internal helpers


def _reshape_games_to_long(games: pd.DataFrame) -> pd.DataFrame:
    """
    Convert wide game table (home/away columns) into a team-level long format.
    """
    base_cols = ["GAME_ID", "SEASON_ID", "SEASON_TYPE", "IS_REGULAR_SEASON", "IS_PLAYOFFS", "GAME_DATE"]

    def _select_side(side: str) -> pd.DataFrame:
        suffix = f"_{side}"
        opp_suffix = "_AWAY" if side == "HOME" else "_HOME"

        data = games[base_cols].copy()
        data["TEAM_ID"] = games[f"TEAM_ID{suffix}"]
        data["TEAM_ABBREVIATION"] = games[f"TEAM_ABBREVIATION{suffix}"]
        data["TEAM_NAME"] = games[f"TEAM_NAME{suffix}"]
        matchup_series = games[f"MATCHUP{suffix}"].astype(str)
        data["MATCHUP"] = matchup_series
        data["WL"] = games[f"WL{suffix}"]
        data["FGM"] = games[f"FGM{suffix}"]
        data["FGA"] = games[f"FGA{suffix}"]
        data["FG3M"] = games[f"FG3M{suffix}"]
        data["FG3A"] = games[f"FG3A{suffix}"]
        data["FTM"] = games[f"FTM{suffix}"]
        data["FTA"] = games[f"FTA{suffix}"]
        data["OREB"] = games[f"OREB{suffix}"]
        data["DREB"] = games[f"DREB{suffix}"]
        data["REB"] = games[f"REB{suffix}"]
        data["AST"] = games[f"AST{suffix}"]
        data["STL"] = games[f"STL{suffix}"]
        data["BLK"] = games[f"BLK{suffix}"]
        data["TOV"] = games[f"TOV{suffix}"]
        data["PF"] = games[f"PF{suffix}"]
        data["PTS"] = games[f"PTS{suffix}"]

        data["OPP_TEAM_ID"] = games[f"TEAM_ID{opp_suffix}"]
        data["OPP_TEAM_ABBREVIATION"] = games[f"TEAM_ABBREVIATION{opp_suffix}"]
        data["OPP_PTS"] = games[f"PTS{opp_suffix}"]
        data["OPP_FGM"] = games[f"FGM{opp_suffix}"]
        data["OPP_FGA"] = games[f"FGA{opp_suffix}"]
        data["OPP_FG3M"] = games[f"FG3M{opp_suffix}"]
        data["OPP_FG3A"] = games[f"FG3A{opp_suffix}"]
        data["OPP_FTM"] = games[f"FTM{opp_suffix}"]
        data["OPP_FTA"] = games[f"FTA{opp_suffix}"]
        data["OPP_OREB"] = games[f"OREB{opp_suffix}"]
        data["OPP_DREB"] = games[f"DREB{opp_suffix}"]
        data["OPP_REB"] = games[f"REB{opp_suffix}"]
        data["OPP_AST"] = games[f"AST{opp_suffix}"]
        data["OPP_TOV"] = games[f"TOV{opp_suffix}"]

        data["IS_HOME"] = side == "HOME"
        data["WIN"] = (data["WL"].str.upper() == "W").astype(int)
        data["OVERTIME_PERIODS"] = matchup_series.map(_parse_overtime_from_matchup)
        return data

    home_df = _select_side("HOME")
    away_df = _select_side("AWAY")

    combined = pd.concat([home_df, away_df], ignore_index=True)
    numeric_cols = [
        "FGM",
        "FGA",
        "FG3M",
        "FG3A",
        "FTM",
        "FTA",
        "OREB",
        "DREB",
        "REB",
        "AST",
        "STL",
        "BLK",
        "TOV",
        "PF",
        "PTS",
        "OPP_PTS",
        "OPP_FGM",
        "OPP_FGA",
        "OPP_FG3M",
        "OPP_FG3A",
        "OPP_FTM",
        "OPP_FTA",
        "OPP_OREB",
        "OPP_DREB",
        "OPP_REB",
        "OPP_AST",
        "OPP_TOV",
        "OVERTIME_PERIODS",
    ]
    for col in numeric_cols:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")

    return combined


def _parse_overtime_from_matchup(matchup: str) -> int:
    """
    Rough overtime estimate based on matchup string suffix.
    """
    matchup = str(matchup)
    if "OT" not in matchup:
        return 0
    try:
        suffix = matchup.split("OT")[-1].strip()
        return int(suffix) if suffix else 1
    except ValueError:
        return 1
