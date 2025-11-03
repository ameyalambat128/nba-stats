import pandas as pd
import pytest

from src.era import annotate_era, load_era_definitions, summarize_by_era, resolve_era_for_year


def test_resolve_era_for_year_matches_config():
    eras = load_era_definitions()
    sample_year = 2015
    era = resolve_era_for_year(sample_year, eras=eras)
    assert era.label == "Modern Pace & 3PT Revolution"


def test_annotate_era_adds_columns():
    df = pd.DataFrame({"TEAM_ID": ["TEST"], "SEASON_YEAR": [2008], "IS_PLAYOFFS": [False]})
    annotated = annotate_era(df)
    assert "ERA_KEY" in annotated.columns
    assert annotated.loc[0, "ERA_KEY"] == "pace_and_space_rise"


def test_summarize_by_era_weighted_average():
    df = pd.DataFrame(
        {
            "ERA_KEY": ["modern_three_point", "modern_three_point"],
            "ERA_LABEL": ["Modern Pace & 3PT Revolution", "Modern Pace & 3PT Revolution"],
            "ERA_START_YEAR": [2014, 2014],
            "ERA_END_YEAR": [pd.NA, pd.NA],
            "IS_PLAYOFFS": [False, False],
            "PACE": [100.0, 110.0],
            "OFF_EFF_PER_100": [110.0, 120.0],
            "THREE_POINT_RATE": [0.35, 0.45],
            "AST_TOV_RATIO": [1.5, 2.0],
            "TOTAL_EST_POSSESSIONS": [1000.0, 2000.0],
            "WIN_PCT": [0.5, 0.75],
            "GAMES_PLAYED": [10, 20],
        }
    )

    summary = summarize_by_era(df)
    assert len(summary) == 1
    row = summary.iloc[0]
    # Weighted pace should be (100*10 + 110*20) / 30 = 106.666...
    assert abs(row["PACE"] - 106.6667) < 1e-3
    assert row["TOTAL_GAMES"] == 30
    assert pytest.approx(row["WEIGHTED_WIN_PCT"], rel=1e-3) == (0.5 * 10 + 0.75 * 20) / 30
