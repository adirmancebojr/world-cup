"""Fetch raw data snapshots into 01_raw_data/ with a checksum manifest.

Sources (licenses verified, see 00_admin/data-availability-research.md):
  - martj42/international_results (CC0-1.0): results.csv, shootouts.csv
  - openfootball/worldcup.json (public domain): 2026/worldcup.json
"""
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "01_raw_data"

SOURCES = {
    "results.csv": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
    "shootouts.csv": "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv",
    "worldcup2026.json": "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
}


def main() -> int:
    RAW.mkdir(exist_ok=True)
    manifest = {"pulled_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
    for name, url in SOURCES.items():
        data = urllib.request.urlopen(url, timeout=60).read()
        if len(data) < 1000:
            print(f"VALIDATION FAIL: {name} suspiciously small ({len(data)} bytes)")
            return 1
        (RAW / name).write_bytes(data)
        manifest["files"][name] = {
            "url": url,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        print(f"fetched {name}: {len(data):,} bytes")
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
