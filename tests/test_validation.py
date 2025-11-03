import pandas as pd
import pytest

from src.pipeline.season_summary import generate_team_season_summary
from src.validation import assert_team_summary_valid, validate_team_summary
from src.data_ingest import NBADataIngestor


def test_validate_team_summary_reports_no_issues_for_expected_ranges():
    df = pd.DataFrame(
        {
            "TEAM_ID": ["TEST"],
            "SEASON_YEAR": [2020],
            "IS_PLAYOFFS": [False],
            "PACE": [100.0],
            "OFF_EFF_PER_100": [112.5],
            "DEF_EFF_PER_100": [107.3],
            "THREE_POINT_RATE": [0.35],
            "AST_TOV_RATIO": [1.5],
            "TOTAL_EST_POSSESSIONS": [8200.0],
            "WIN_PCT": [0.6],
            "GAMES_PLAYED": [82],
        }
    )

    issues = validate_team_summary(df)
    assert issues == []


def test_validate_team_summary_flags_out_of_bounds_values():
    df = pd.DataFrame(
        {
            "TEAM_ID": ["TEST"],
            "SEASON_YEAR": [2020],
            "IS_PLAYOFFS": [False],
            "PACE": [30.0],
            "OFF_EFF_PER_100": [170.0],
            "DEF_EFF_PER_100": [10.0],
            "THREE_POINT_RATE": [0.35],
            "AST_TOV_RATIO": [1.5],
            "TOTAL_EST_POSSESSIONS": [100.0],
            "WIN_PCT": [1.2],
            "GAMES_PLAYED": [1],
        }
    )

    issues = validate_team_summary(df)
    assert len(issues) >= 3


def test_assert_team_summary_valid_runs_pipeline_when_data_available():
    try:
        ingestor = NBADataIngestor()
    except FileNotFoundError:
        pytest.skip("NBA dataset not available locally.")

    summary = generate_team_season_summary(ingestor, regular_season_only=True, save=False)
    assert_team_summary_valid(summary)
