"""
Command-line utility to generate team-season summaries.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.data_ingest import NBADataIngestor
from src.pipeline.season_summary import generate_team_season_summary
from src.preprocess import Preprocessor
from src.validation import validate_team_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate team-season aggregates with optional playoffs/regular-season filters.",
    )

    season_group = parser.add_mutually_exclusive_group()
    season_group.add_argument(
        "--playoffs",
        action="store_true",
        help="Restrict to playoff games.",
    )
    season_group.add_argument(
        "--regular-season",
        action="store_true",
        help="Restrict to regular season games.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to store the generated CSV (default: data/processed).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write the output CSV; still prints a preview.",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=5,
        help="Number of rows from the summary to display (default: 5).",
    )
    parser.add_argument(
        "--prefer-sqlite",
        action="store_true",
        help="Prefer reading from SQLite when available (default).",
    )
    parser.add_argument(
        "--prefer-csv",
        action="store_true",
        help="Force reading from CSV exports instead of SQLite.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prefer_sqlite = True
    if args.prefer_csv and args.prefer_sqlite:
        raise ValueError("Only one of --prefer-sqlite or --prefer-csv may be specified.")
    if args.prefer_csv:
        prefer_sqlite = False

    ingestor = NBADataIngestor(prefer_sqlite=prefer_sqlite)
    preprocessor = Preprocessor()

    summary = generate_team_season_summary(
        ingestor,
        preprocessor=preprocessor,
        playoffs_only=args.playoffs,
        regular_season_only=args.regular_season,
        output_dir=args.output_dir,
        save=not args.no_save,
    )

    preview = summary.head(args.preview_rows)
    print(preview.to_string(index=False))

    issues = validate_team_summary(summary)
    if issues:
        print("Validation issues detected:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
    else:
        print("Validation checks passed.", file=sys.stderr)


if __name__ == "__main__":
    main()
