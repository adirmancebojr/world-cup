"""Append the current champion-odds snapshot to docs/data/champion_history.json
so the site can chart how the odds move as the cup progresses.

Deduped by matches_played: one point per completed-match state (re-runs with the
same results just refresh the timestamp). This is a forward-accumulating log of
convenience — the authoritative history is still the git log of site_data.json,
from which this file can be fully rebuilt (see scripts/seed note in the README).
Run AFTER 03_build_site_data.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "data" / "site_data.json"
HIST = ROOT / "docs" / "data" / "champion_history.json"


def snapshot(site: dict) -> dict:
    return {
        "t": site.get("results_through"),
        "generated_utc": site.get("generated_utc"),
        "matches_played": int(site.get("matches_played") or 0),
        "odds": {t["code"]: round(float(t["p_champion"]), 4) for t in site["teams"]},
    }


def main() -> int:
    site = json.loads(SITE.read_text())
    snap = snapshot(site)
    hist = json.loads(HIST.read_text()) if HIST.exists() else {"snapshots": []}
    # one snapshot per tournament day: keep the latest state for each date, so a
    # day's point finalises at end-of-day as its matches complete.
    snaps = [s for s in hist["snapshots"] if s.get("t") != snap["t"]]
    snaps.append(snap)
    snaps.sort(key=lambda s: (s.get("matches_played", 0), s.get("t") or ""))
    HIST.write_text(json.dumps({"snapshots": snaps}, ensure_ascii=False))
    print(f"champion_history.json: {len(snaps)} snapshots (latest {snap['t']}, {snap['matches_played']} matches)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
