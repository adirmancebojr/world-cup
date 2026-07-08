"""Rebuild docs/data/champion_history.json with one accurate snapshot per
completed tournament day — WITHOUT leaking information into the past.

The model is deterministic, so each day's odds are reconstructed by re-running
Elo + the tournament simulation as of the END of that day (WC_AS_OF masks all
later scores). The subtlety is the bracket: today's bracket.json contains the
drawn knockout pairings, which were NOT known during the group stage. So:

  - group-stage days (<= GROUP_END): use the PLACEHOLDER bracket (slot codes
    like "1A", "3A/B/C/D/F", "W74"), recovered from git history — the sim
    resolves slots from simulated/actual standings, exactly as it did then.
  - knockout days (> GROUP_END): use a HYBRID bracket — the real R32 draw
    (public knowledge from the end of the group stage) but W/L slot refs for
    every later round, so unplayed rounds resolve only from results <= the day.

Re-runnable and idempotent. Leaves Elo/simulation outputs at the LAST day's
state — run the normal live chain afterwards to refresh everything.

Run: python 03_pipeline/05_backfill_history.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
HIST = ROOT / "docs" / "data" / "champion_history.json"
TEAM_PROBS = ROOT / "04_analysis_modules/03_simulation/tables/team_probs.csv"
ELO = "04_analysis_modules/01_team_strength/01_compute_elo.py"
SIM = "04_analysis_modules/03_simulation/01_simulate.py"
PLACEHOLDER_COMMIT = "39bd98f"  # pre-knockout-draw bracket.json (slot codes only)
GROUP_END = "2026-06-27"


def run(script: str, extra_env: dict) -> None:
    env = {**os.environ, **extra_env}
    subprocess.run([PY, str(ROOT / script)], env=env, check=True, cwd=ROOT, stdout=subprocess.DEVNULL)


def main() -> int:
    wc = pd.read_csv(ROOT / "02_processed_data/wc2026_matches.csv")
    played = wc[wc["home_score"].notna()]
    days = sorted(played["date"].unique())
    if not days:
        print("no played days yet — nothing to backfill")
        return 0

    site = json.loads((ROOT / "docs/data/site_data.json").read_text())
    name_to_code = {t["name"]: t["code"] for t in site["teams"]}
    team_names = set(name_to_code)

    # era-correct brackets
    placeholder = json.loads(subprocess.run(
        ["git", "show", f"{PLACEHOLDER_COMMIT}:02_processed_data/bracket.json"],
        capture_output=True, text=True, check=True, cwd=ROOT).stdout)
    current = json.loads((ROOT / "02_processed_data/bracket.json").read_text())
    cur_by_num = {m["num"]: m for m in current["knockout"]}
    hybrid = copy.deepcopy(placeholder)
    for m in hybrid["knockout"]:
        if m["round"] == "Round of 32":  # the R32 draw became public at group end
            c = cur_by_num[m["num"]]
            for side in ("team1", "team2"):
                if c[side] in team_names:
                    m[side] = c[side]

    tmp = Path(tempfile.mkdtemp(prefix="wc-backfill-"))
    files = {"placeholder": tmp / "bracket_placeholder.json", "hybrid": tmp / "bracket_hybrid.json"}
    files["placeholder"].write_text(json.dumps(placeholder, ensure_ascii=False))
    files["hybrid"].write_text(json.dumps(hybrid, ensure_ascii=False))

    snaps = []
    for d in days:
        era = "placeholder" if d <= GROUP_END else "hybrid"
        run(ELO, {"WC_AS_OF": d})
        run(SIM, {"WC_AS_OF": d, "WC_SKIP_STABILITY": "1", "WC_BRACKET_FILE": str(files[era])})
        tp = pd.read_csv(TEAM_PROBS)
        odds = {name_to_code[r.team]: round(float(r.p_champion), 4) for r in tp.itertuples()}
        mp = int((played["date"] <= d).sum())
        top = sorted(odds.items(), key=lambda kv: -kv[1])[:2]
        snaps.append({"t": str(d), "matches_played": mp, "odds": odds})
        print(f"  as of {d} ({era[0].upper()}): {mp} matches · {top[0][0]} {top[0][1]:.3f} · {top[1][0]} {top[1][1]:.3f}")

    HIST.write_text(json.dumps({"snapshots": snaps}, ensure_ascii=False))
    print(f"champion_history.json rebuilt: {len(snaps)} daily snapshots (through {days[-1]})")
    print("NOTE: re-run the live chain (elo, backtest, tracking, simulate, recompute, build, update_history).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
