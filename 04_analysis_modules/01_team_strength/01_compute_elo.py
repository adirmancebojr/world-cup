"""Compute Elo ratings per frozen spec Layer 1. Numbered script — every Elo
number shown anywhere traces here.

Set WC_AS_OF=YYYY-MM-DD to replay the tournament as of the end of that day
(drops matches after the cutoff) — used by the history backfill. Unset =
current behaviour, byte-identical."""
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_pipeline"))
import wcmodel  # noqa: E402

MOD = Path(__file__).resolve().parent


def main() -> int:
    matches = pd.read_csv(ROOT / "02_processed_data" / "matches.csv")
    as_of = os.environ.get("WC_AS_OF")
    if as_of:
        matches = matches[matches["date"] <= as_of].reset_index(drop=True)
    with_elo, ratings = wcmodel.run_elo(matches)

    # validation: zero-sum conservation + finiteness
    assert np.isfinite(list(ratings.values())).all()
    drift = abs(np.mean(list(ratings.values())) - wcmodel.INITIAL_RATING)
    assert drift < 1e-6, f"Elo not conserved: mean drifted {drift}"

    with_elo.to_csv(ROOT / "02_processed_data" / "matches_elo.csv", index=False)

    cur = pd.DataFrame(sorted(ratings.items(), key=lambda kv: -kv[1]), columns=["team", "rating"])
    cur["rank"] = range(1, len(cur) + 1)
    (MOD / "tables").mkdir(exist_ok=True)
    cur.to_csv(MOD / "tables" / "elo_current.csv", index=False)

    wc = pd.read_csv(ROOT / "02_processed_data" / "wc2026_matches.csv")
    wc48 = sorted(set(wc["home_team"]) | set(wc["away_team"]))
    assert len(wc48) == 48
    missing = [t for t in wc48 if t not in ratings]
    assert not missing, f"WC teams without ratings: {missing}"
    cur[cur["team"].isin(wc48)].to_csv(MOD / "tables" / "elo_wc48.csv", index=False)

    (MOD / "figures").mkdir(exist_ok=True)
    top = cur[cur["team"].isin(wc48)].head(16).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["team"], top["rating"], color="#2a9d8f")
    ax.set_xlim(left=top["rating"].min() - 60)
    ax.set_title("Recomputed Elo — top 16 of the WC-48 (as of last played match)")
    fig.tight_layout()
    fig.savefig(MOD / "figures" / "elo_top16.png", dpi=150)

    recent = with_elo[with_elo["date"] >= "2018-01-01"]
    fig, ax = plt.subplots(figsize=(7, 4))
    counts = recent["home_score"].value_counts(normalize=True).sort_index().loc[:8]
    lam = recent["home_score"].mean()
    from scipy.stats import poisson
    ax.bar(counts.index, counts.values, alpha=0.6, label="observed home goals (2018+)")
    ax.plot(np.arange(9), poisson.pmf(np.arange(9), lam), "o-", color="#e76f51", label=f"Poisson(λ={lam:.2f})")
    ax.legend()
    ax.set_title("Goals distribution vs Poisson — visual sanity")
    fig.tight_layout()
    fig.savefig(MOD / "figures" / "goals_dist.png", dpi=150)

    print(cur[cur["team"].isin(wc48)].head(10).to_string(index=False))
    print(f"matches_elo.csv rows: {len(with_elo):,}; teams rated: {len(cur)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
