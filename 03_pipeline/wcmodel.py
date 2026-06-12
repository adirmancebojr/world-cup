"""Shared model library — implements 00_admin/analysis-spec.md exactly.

Layer 1: Elo recomputed from scratch (K by importance, goal-diff multiplier,
         +100 home advantage on non-neutral venues).
Layer 2: independent Poisson, log lambda = b0 + b1 * (R_i - R_j + hadv_i) / 400.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

INITIAL_RATING = 1500.0
HOME_ADV = 100.0
MAX_GOALS = 10  # Poisson grid 0..10 per spec

CONTINENTAL_FINALS = {
    "UEFA Euro", "Copa América", "African Cup of Nations", "AFC Asian Cup",
    "CONCACAF Championship", "Gold Cup", "Oceania Nations Cup", "Confederations Cup",
}


def k_factor(tournament: str) -> float:
    if tournament == "FIFA World Cup":
        return 60.0
    if "qualification" in tournament.lower():
        return 40.0
    if tournament in CONTINENTAL_FINALS:
        return 50.0
    if tournament == "Friendly":
        return 20.0
    return 30.0


def goal_mult(margin: int) -> float:
    margin = abs(margin)
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11.0 + margin) / 8.0


def win_expectancy(delta_r: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-delta_r / 400.0))


def run_elo(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """One chronological pass over played matches. Adds pre-match ratings
    (r_home_pre, r_away_pre) per row — these use only earlier matches, so any
    later train/predict split on them is leakage-free. Returns final ratings."""
    df = df.sort_values(["date"], kind="stable").reset_index(drop=True)
    ratings: dict[str, float] = {}
    rh_pre = np.empty(len(df))
    ra_pre = np.empty(len(df))
    for idx, row in enumerate(df.itertuples(index=False)):
        rh = ratings.get(row.home_team, INITIAL_RATING)
        ra = ratings.get(row.away_team, INITIAL_RATING)
        rh_pre[idx], ra_pre[idx] = rh, ra
        hadv = 0.0 if row.neutral else HOME_ADV
        we = win_expectancy(rh - ra + hadv)
        if row.home_score > row.away_score:
            w = 1.0
        elif row.home_score < row.away_score:
            w = 0.0
        else:
            w = 0.5
        delta = k_factor(row.tournament) * goal_mult(int(row.home_score - row.away_score)) * (w - we)
        ratings[row.home_team] = rh + delta
        ratings[row.away_team] = ra - delta
    out = df.copy()
    out["r_home_pre"] = rh_pre
    out["r_away_pre"] = ra_pre
    return out, ratings


def elo_update(rh: float, ra: float, hadv: float, gh: int, ga: int, k: float = 60.0) -> tuple[float, float]:
    we = win_expectancy(rh - ra + hadv)
    w = 1.0 if gh > ga else (0.0 if gh < ga else 0.5)
    delta = k * goal_mult(gh - ga) * (w - we)
    return rh + delta, ra - delta


def fit_poisson(df: pd.DataFrame) -> tuple[float, float]:
    """Poisson MLE of (b0, b1) on two observations per match.
    x_team = (R_team - R_opp + signed home adv) / 400."""
    hadv = np.where(df["neutral"].to_numpy(), 0.0, HOME_ADV)
    x_home = (df["r_home_pre"].to_numpy() - df["r_away_pre"].to_numpy() + hadv) / 400.0
    x_away = -x_home
    x = np.concatenate([x_home, x_away])
    y = np.concatenate([df["home_score"].to_numpy(float), df["away_score"].to_numpy(float)])

    def nll_grad(beta):
        lam = np.exp(beta[0] + beta[1] * x)
        nll = float(np.sum(lam - y * np.log(lam)))
        g = np.array([np.sum(lam - y), np.sum((lam - y) * x)])
        return nll, g

    res = minimize(nll_grad, x0=np.array([0.0, 1.0]), jac=True, method="L-BFGS-B")
    # accept the optimum if the per-observation gradient is effectively zero,
    # regardless of the optimizer's precision-loss flag
    grad_norm = float(np.max(np.abs(nll_grad(res.x)[1]))) / len(x)
    if grad_norm > 1e-4:
        raise RuntimeError(f"Poisson MLE did not converge (per-obs grad {grad_norm:.2e}): {res.message}")
    return float(res.x[0]), float(res.x[1])


def fit_dixon_coles(df: pd.DataFrame) -> tuple[float, float, float]:
    """Joint MLE of (b0, b1, rho) per D06. rho < 0 inflates low-score draws via
    the Dixon-Coles tau factors on cells (0,0), (0,1), (1,0), (1,1)."""
    hadv = np.where(df["neutral"].to_numpy(), 0.0, HOME_ADV)
    x = (df["r_home_pre"].to_numpy() - df["r_away_pre"].to_numpy() + hadv) / 400.0
    h = df["home_score"].to_numpy(float)
    a = df["away_score"].to_numpy(float)

    def nll(theta):
        b0, b1, rho = theta
        lam = np.exp(b0 + b1 * x)
        mu = np.exp(b0 - b1 * x)
        tau = np.ones_like(lam)
        m00 = (h == 0) & (a == 0)
        m01 = (h == 0) & (a == 1)
        m10 = (h == 1) & (a == 0)
        m11 = (h == 1) & (a == 1)
        tau[m00] = 1.0 - lam[m00] * mu[m00] * rho
        tau[m01] = 1.0 + lam[m01] * rho
        tau[m10] = 1.0 + mu[m10] * rho
        tau[m11] = 1.0 - rho
        tau = np.clip(tau, 1e-10, None)
        return float(np.sum(lam + mu - h * np.log(lam) - a * np.log(mu) - np.log(tau)))

    res = minimize(nll, x0=np.array([0.2, 0.75, -0.05]), method="L-BFGS-B",
                   bounds=[(-2, 2), (0, 3), (-0.2, 0.2)])
    if not res.success:
        raise RuntimeError(f"Dixon-Coles MLE did not converge: {res.message}")
    return float(res.x[0]), float(res.x[1]), float(res.x[2])


def goal_rates(rh: float, ra: float, hadv: float, b0: float, b1: float) -> tuple[float, float]:
    x = (rh - ra + hadv) / 400.0
    return float(np.exp(b0 + b1 * x)), float(np.exp(b0 - b1 * x))


_FACT = np.cumprod(np.concatenate(([1.0], np.arange(1, MAX_GOALS + 1))))
_GRID = np.arange(MAX_GOALS + 1)


def score_matrix(lam_h: float, lam_a: float, rho: float = 0.0) -> np.ndarray:
    """P(score == (i, j)) on the 0..MAX_GOALS grid, Dixon-Coles tau-adjusted
    (rho=0 reduces to independent Poisson), renormalized."""
    ph = np.exp(-lam_h) * lam_h ** _GRID / _FACT
    pa = np.exp(-lam_a) * lam_a ** _GRID / _FACT
    m = np.outer(ph, pa)
    if rho != 0.0:
        m[0, 0] *= 1.0 - lam_h * lam_a * rho
        m[0, 1] *= 1.0 + lam_h * rho
        m[1, 0] *= 1.0 + lam_a * rho
        m[1, 1] *= 1.0 - rho
        np.clip(m, 0.0, None, out=m)
    return m / m.sum()


def outcome_probs(lam_h: float, lam_a: float, rho: float = 0.0) -> tuple[float, float, float]:
    m = score_matrix(lam_h, lam_a, rho)
    p_home = float(np.tril(m, -1).sum())
    p_draw = float(np.trace(m))
    p_away = float(np.triu(m, 1).sum())
    return p_home, p_draw, p_away


def raw_elo_baseline(rh: float, ra: float, hadv: float, draw_rate: float) -> tuple[float, float, float]:
    we = win_expectancy(rh - ra + hadv)
    return (1.0 - draw_rate) * we, draw_rate, (1.0 - draw_rate) * (1.0 - we)
