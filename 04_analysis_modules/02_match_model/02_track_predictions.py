"""Track how the live 2026 predictions are doing.

For every PLAYED WC-2026 match, recompute the model's PRE-MATCH prediction
from the leakage-free pre-match Elo in matches_elo.csv (the same ratings the
site showed before kickoff) and compare to the actual result:
  - outcome: headline raw-Elo W/D/L argmax vs actual (D07 headline model)
  - score:   most-likely Poisson scoreline vs actual (experimental layer)

Outputs (reproducible, no snapshot capture needed):
  tables/predictions_2026.csv   one row per played match
  tables/prediction_summary.json aggregates for the site scoreboard
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_pipeline"))
import wcmodel  # noqa: E402

MOD = Path(__file__).resolve().parent
WC_START = "2026-06-11"


def main() -> int:
    df = pd.read_csv(ROOT / "02_processed_data" / "matches_elo.csv")
    params = json.loads((MOD / "tables" / "model_params.json").read_text())
    b0, b1, draw_rate = params["b0"], params["b1"], params["draw_rate"]

    wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= WC_START)].copy()
    wc = wc.sort_values("date", kind="stable")

    rows = []
    for r in wc.itertuples(index=False):
        hadv = 0.0 if r.neutral else wcmodel.HOME_ADV
        # headline outcome prediction (raw-Elo, D07)
        pw, pdr, pl = wcmodel.raw_elo_baseline(r.r_home_pre, r.r_away_pre, hadv, draw_rate)
        probs = {"H": pw, "D": pdr, "A": pl}
        pred_outcome = max(probs, key=probs.get)
        # most-likely scoreline (experimental Poisson)
        lam_h, lam_a = wcmodel.goal_rates(r.r_home_pre, r.r_away_pre, hadv, b0, b1)
        grid = wcmodel.score_matrix(lam_h, lam_a)
        gi, gj = np.unravel_index(int(np.argmax(grid)), grid.shape)
        top_score_prob = float(grid[gi, gj])
        # actual
        hs, as_ = int(r.home_score), int(r.away_score)
        actual_outcome = "H" if hs > as_ else ("A" if hs < as_ else "D")
        prob_actual = probs[actual_outcome]
        rows.append(dict(
            date=r.date, home=r.home_team, away=r.away_team, home_score=hs, away_score=as_,
            p_home=round(pw, 4), p_draw=round(pdr, 4), p_away=round(pl, 4),
            pred_outcome=pred_outcome, actual_outcome=actual_outcome,
            outcome_hit=int(pred_outcome == actual_outcome),
            top_score_home=int(gi), top_score_away=int(gj),
            top_score=f"{gi}-{gj}", top_score_prob=round(top_score_prob, 4), actual_score=f"{hs}-{as_}",
            score_hit=int((gi, gj) == (hs, as_)),
            prob_actual=round(prob_actual, 4), logloss=round(-np.log(max(prob_actual, 1e-12)), 4),
        ))

    pred = pd.DataFrame(rows)
    (MOD / "tables").mkdir(exist_ok=True)
    pred.to_csv(MOD / "tables" / "predictions_2026.csv", index=False)

    n = len(pred)
    summary = dict(
        n=n,
        outcome_correct=int(pred["outcome_hit"].sum()) if n else 0,
        outcome_pct=round(float(pred["outcome_hit"].mean()), 4) if n else None,
        score_correct=int(pred["score_hit"].sum()) if n else 0,
        score_pct=round(float(pred["score_hit"].mean()), 4) if n else None,
        mean_prob_actual=round(float(pred["prob_actual"].mean()), 4) if n else None,
        mean_logloss=round(float(pred["logloss"].mean()), 4) if n else None,
        uniform_logloss=round(float(np.log(3)), 4),  # uninformed 3-way baseline
        results_through=str(pred["date"].max()) if n else None,
    )
    (MOD / "tables" / "prediction_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"tracked {n} played matches")
    if n:
        print(f"  outcome: {summary['outcome_correct']}/{n} ({summary['outcome_pct']:.0%})  "
              f"exact score: {summary['score_correct']}/{n} ({summary['score_pct']:.0%})")
        print(f"  mean log-loss {summary['mean_logloss']} vs uniform {summary['uniform_logloss']}")
        print(pred[["date", "home", "away", "actual_score", "pred_outcome", "actual_outcome", "outcome_hit", "top_score", "score_hit"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
