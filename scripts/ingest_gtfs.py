#!/usr/bin/env python3
"""Ingest GTFS zip and print stats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.gtfs import ingest_gtfs_from_zip  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    stats = ingest_gtfs_from_zip(args.zip_path)
    print(stats)
    if stats["routes"] < 200:
        print("WARNING: route count below staleness threshold", file=sys.stderr)


if __name__ == "__main__":
    main()
