#!/usr/bin/env python3
"""Download TransJakarta GTFS feed."""

from __future__ import annotations

import argparse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

TJ_URL = "https://gtfs.transjakarta.co.id/files/file_gtfs.zip"


def download(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "transjakarta.zip"
    print(f"Fetching {TJ_URL} ...")
    urllib.request.urlretrieve(TJ_URL, dest)
    meta = out_dir / "transjakarta.meta.txt"
    meta.write_text(
        f"fetched_at={datetime.now(UTC).isoformat()}\nurl={TJ_URL}\n",
        encoding="utf-8",
    )
    print(f"Saved {dest} ({dest.stat().st_size // 1024} KB)")
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/gtfs")
    args = parser.parse_args()
    download(Path(args.out))
