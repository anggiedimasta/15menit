#!/usr/bin/env python3
"""Extend merged GTFS with Bodetabek (Bogor) feeds.

See ``docs/bodetabek-gtfs.md`` for Bogor GTFS download steps.

Quick merge:

```powershell
python scripts/merge_bodetabek.py
```

Output: ``data/gtfs/jakarta-bodetabek-merged.zip`` (Jakarta-only copy when Bogor zip missing).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from merge_gtfs import merge

BOGOR_DEFAULT = Path("data/gtfs/bogor.zip")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge Jakarta GTFS with optional Bogor/Bodetabek feed."
    )
    parser.add_argument("--jakarta", default="data/gtfs/jakarta-merged.zip")
    parser.add_argument("--bogor", default=str(BOGOR_DEFAULT))
    parser.add_argument("--output", default="data/gtfs/jakarta-bodetabek-merged.zip")
    args = parser.parse_args()
    inputs = [Path(args.jakarta)]
    bogor = Path(args.bogor)
    if bogor.exists():
        inputs.append(bogor)
        print(f"Including Bogor feed: {bogor}")
    else:
        print(f"Skip missing Bogor feed: {bogor}")
        print(
            "Download Bogor GTFS — see docs/bodetabek-gtfs.md — "
            f"save to {BOGOR_DEFAULT}, then re-run."
        )
    merge(inputs, Path(args.output))
