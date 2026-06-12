"""Backtest the Elo->Poisson model on WC 2014/2018/2022 per frozen spec, and
fit the production beta for 2026. Tests claims C01 and C02."""
import json
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

BACKTESTS = {
    "WC2014": ("2014-06-12", "2014-07-13"),
    "WC2018": ("2018-06-14", "2018-07-15"),
    "WC2022": ("2022-11-20", "2022-12-18"),
}
PROD_WINDOW = ("2018-01-01", "2026-06-10")  # frozen spec Layer 2


def fit_window(df: pd.DataFrame, start: str, years: int = 8) -> pd.DataFrame:
    lo = (pd.Timestamp(start) - pd.DateOffset(years=years)).strftime("%Y-%m-%d")
    return df[(df["tournament"] != "Friendly") & (df["date"] >= lo) & (df["date"] < start)]


def predict(df: pd.DataFrame, dc: tuple, iid: tuple, draw_rate: float) -> pd.DataFrame:
    """dc = (b0, b1, rho) per D06 — the candidate model; iid = (b0, b1) — the
    original spec model, kept as a reference row per D06."""
    rows = []
    for r in df.itertuples():
        hadv = 0.0 if r.neutral else wcmodel.HOME_ADV
        lam_h, lam_a = wcmodel.goal_rates(r.r_home_pre, r.r_away_pre, hadv, dc[0], dc[1])
        pw, pd_, pl = wcmodel.outcome_probs(lam_h, lam_a, dc[2])
        il_h, il_a = wcmodel.goal_rates(r.r_home_pre, r.r_away_pre, hadv, iid[0], iid[1])
        iw, id_, il = wcmodel.outcome_probs(il_h, il_a)
        bw, bd, bl = wcmodel.raw_elo_baseline(r.r_home_pre, r.r_away_pre, hadv, draw_rate)
        y = 0 if r.home_score > r.away_score else (2 if r.home_score < r.away_score else 1)
        rows.append(dict(date=r.date, home=r.home_team, away=r.away_team,
                         hs=r.home_score, as_=r.away_score, y=y,
                         p_w=pw, p_d=pd_, p_l=pl, i_w=iw, i_d=id_, i_l=il,
                         b_w=bw, b_d=bd, b_l=bl, lam_h=lam_h, lam_a=lam_a))
    out = pd.DataFrame(rows)
    assert np.allclose(out[["p_w", "p_d", "p_l"]].sum(axis=1), 1, atol=1e-9)
    return out


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1))))


def rps(p: np.ndarray, y: np.ndarray) -> float:
    obs = np.zeros_like(p)
    obs[np.arange(len(y)), y] = 1.0
    return float(np.mean(np.sum((np.cumsum(p, 1) - np.cumsum(obs, 1))[:, :2] ** 2, 1) / 2))


def main() -> int:
    df = pd.read_csv(ROOT / "02_processed_data" / "matches_elo.csv")
    (MOD / "tables").mkdir(exist_ok=True)
    (MOD / "figures").mkdir(exist_ok=True)

    metrics, all_preds = [], []
    for name, (start, end) in BACKTESTS.items():
        fitdf = fit_window(df, start)
        b0, b1, rho = wcmodel.fit_dixon_coles(fitdf)
        iid = wcmodel.fit_poisson(fitdf)
        draw_rate = float((fitdf["home_score"] == fitdf["away_score"]).mean())
        wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= start) & (df["date"] <= end)]
        assert len(wc) == 64, f"{name}: expected 64 matches, got {len(wc)}"
        preds = predict(wc, (b0, b1, rho), iid, draw_rate)
        preds["tournament"] = name
        all_preds.append(preds)

        y = preds["y"].to_numpy()
        pm = preds[["p_w", "p_d", "p_l"]].to_numpy()
        pi = preds[["i_w", "i_d", "i_l"]].to_numpy()
        pb = preds[["b_w", "b_d", "b_l"]].to_numpy()
        pu = np.full_like(pm, 1 / 3)
        for method, p in (("model", pm), ("poisson_iid", pi), ("raw_elo", pb), ("uniform", pu)):
            metrics.append(dict(tournament=name, method=method, n=len(y),
                                log_loss=log_loss(p, y), rps=rps(p, y),
                                b0=b0, b1=b1, rho=rho, draw_rate=draw_rate))
        print(f"{name}: b0={b0:.4f} b1={b1:.4f} rho={rho:.4f} draw_rate={draw_rate:.3f} fit_n={len(fitdf)}")

    preds = pd.concat(all_preds, ignore_index=True)
    y = preds["y"].to_numpy()
    for method, cols in (("model", ["p_w", "p_d", "p_l"]), ("poisson_iid", ["i_w", "i_d", "i_l"]),
                         ("raw_elo", ["b_w", "b_d", "b_l"]), ("uniform", None)):
        p = preds[cols].to_numpy() if cols else np.full((len(y), 3), 1 / 3)
        metrics.append(dict(tournament="POOLED", method=method, n=len(y),
                            log_loss=log_loss(p, y), rps=rps(p, y), b0=None, b1=None, rho=None, draw_rate=None))
    mdf = pd.DataFrame(metrics)
    mdf.to_csv(MOD / "tables" / "backtest_metrics.csv", index=False)
    preds.to_csv(MOD / "tables" / "backtest_predictions.csv", index=False)

    # ---- C01: pooled model beats both baselines; beats raw_elo in >=2 of 3 ----
    pooled = mdf[mdf["tournament"] == "POOLED"].set_index("method")["log_loss"]
    per_t = mdf[mdf["tournament"] != "POOLED"].pivot(index="tournament", columns="method", values="log_loss")
    beats_per_t = int((per_t["model"] < per_t["raw_elo"]).sum())
    c01 = pooled["model"] < pooled["raw_elo"] and pooled["model"] < pooled["uniform"] and beats_per_t >= 2
    print(f"\nPooled log-loss: model={pooled['model']:.4f} raw_elo={pooled['raw_elo']:.4f} uniform={pooled['uniform']:.4f}")
    print(per_t.round(4).to_string())
    print(f"C01 {'PASS' if c01 else 'FAIL'} (beats raw_elo in {beats_per_t}/3 tournaments)")

    # ---- C02: calibration, pooled, all three outcome classes ----
    p_flat = preds[["p_w", "p_d", "p_l"]].to_numpy().ravel()
    obs = np.zeros((len(y), 3))
    obs[np.arange(len(y)), y] = 1.0
    o_flat = obs.ravel()
    bins = np.clip((p_flat * 10).astype(int), 0, 9)
    rows = []
    for b in range(10):
        m = bins == b
        if m.sum() >= 30:
            rows.append(dict(bin_lo=b / 10, n=int(m.sum()),
                             p_mean=float(p_flat[m].mean()), obs_freq=float(o_flat[m].mean())))
    cal = pd.DataFrame(rows)
    cal["gap"] = (cal["p_mean"] - cal["obs_freq"]).abs()
    cal.to_csv(MOD / "tables" / "calibration.csv", index=False)
    c02 = bool((cal["gap"] < 0.10).all())
    print(f"\nCalibration (bins n>=30):\n{cal.round(3).to_string(index=False)}")
    print(f"C02 {'PASS' if c02 else 'FAIL'} (max gap {cal['gap'].max():.3f})")

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.plot(cal["p_mean"], cal["obs_freq"], "o-", color="#2a9d8f")
    ax.set_xlabel("predicted probability")
    ax.set_ylabel("observed frequency")
    ax.set_title("Reliability — pooled backtests (WC 2014/2018/2022)")
    fig.tight_layout()
    fig.savefig(MOD / "figures" / "calibration.png", dpi=150)

    # ---- production parameters for 2026 ----
    # D06's DC candidate failed adoption; per its rule the headline is the
    # raw-Elo baseline (D07). The spec Poisson (iid) is kept, demoted to
    # "experimental", for scorelines only. DC fit recorded for the audit.
    prod = df[(df["tournament"] != "Friendly") & (df["date"] >= PROD_WINDOW[0]) & (df["date"] <= PROD_WINDOW[1])]
    b0, b1 = wcmodel.fit_poisson(prod)
    dc = wcmodel.fit_dixon_coles(prod)
    params = dict(headline="raw_elo (D06/D07 fallback)", scoreline_model="poisson_iid (spec, experimental)",
                  b0=b0, b1=b1,
                  draw_rate=float((prod["home_score"] == prod["away_score"]).mean()),
                  d06_dc_rejected=dict(b0=dc[0], b1=dc[1], rho=dc[2]),
                  fit_window=PROD_WINDOW, fit_n=len(prod), fit_date="2026-06-12")
    (MOD / "tables" / "model_params.json").write_text(json.dumps(params, indent=2))
    print(f"\nproduction params: {params}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
