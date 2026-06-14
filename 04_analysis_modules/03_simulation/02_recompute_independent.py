"""INDEPENDENT re-derivation of the champion odds (challenge gate for the
headline numbers). Deliberately shares NO code with wcmodel.py or
01_simulate.py: every formula (Elo, raw-Elo outcomes per D07, bracket,
D05 third-place matching) is re-implemented here from the frozen spec +
decision log. Reads only 02_processed_data/. If this agrees with the
production team_probs.csv within Monte Carlo error, the headline is sound.

Run: python 04_analysis_modules/03_simulation/02_recompute_independent.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "02_processed_data"
N_SIMS = 20_000
SEED = 100  # different from production's 42 / 1-5
K_WC = 60.0
HOME_ADV = 100.0
MAXG = 10
HOSTS = {"United States", "Mexico", "Canada"}


# --- independent re-implementation of the spec's math ---
def win_exp(dr):
    return 1.0 / (1.0 + 10.0 ** (-dr / 400.0))


def gmult(margin):
    m = abs(int(margin))
    if m <= 1:
        return 1.0
    if m == 2:
        return 1.5
    return (11.0 + m) / 8.0


def update(rh, ra, hadv, gh, ga):
    e = win_exp(rh - ra + hadv)
    w = 1.0 if gh > ga else (0.0 if gh < ga else 0.5)
    d = K_WC * gmult(gh - ga) * (w - e)
    return rh + d, ra - d


_G = np.arange(MAXG + 1)
_LOGFAC = np.cumsum(np.concatenate(([0.0], np.log(np.arange(1, MAXG + 1)))))


def pois(lam):
    return np.exp(_G * np.log(lam) - lam - _LOGFAC)


def sample_score(rng, rh, ra, hadv, b0, b1, draw_rate):
    """D07: outcome ~ raw-Elo probs, scoreline ~ Poisson grid | outcome."""
    e = win_exp(rh - ra + hadv)
    pw = (1 - draw_rate) * e
    pdr = draw_rate
    u = rng.random()
    outcome = 0 if u < pw else (1 if u < pw + pdr else 2)
    lh = np.exp(b0 + b1 * (rh - ra + hadv) / 400.0)
    la = np.exp(b0 - b1 * (rh - ra + hadv) / 400.0)
    grid = np.outer(pois(lh), pois(la))
    if outcome == 0:
        mask = np.tril(np.ones_like(grid, bool), -1)
    elif outcome == 1:
        mask = np.eye(MAXG + 1, dtype=bool)
    else:
        mask = np.triu(np.ones_like(grid, bool), 1)
    flat = np.where(mask, grid, 0.0).ravel()
    idx = np.searchsorted(np.cumsum(flat), rng.random() * flat.sum())
    return divmod(int(idx), MAXG + 1)


# --- independent bipartite feasibility (max matching via augmenting paths) ---
def max_matching(slot_allow, items):
    assign = {}

    def aug(s, seen):
        for it in items:
            if it in slot_allow[s] and it not in seen:
                seen.add(it)
                if it not in assign or aug(assign[it], seen):
                    assign[it] = s
                    return True
        return False

    return sum(aug(s, set()) for s in range(len(slot_allow)))


def assign_thirds(slot_allow, thirds_best_first):
    rem = list(thirds_best_first)
    out = []
    for s in range(len(slot_allow)):
        for t in rem:
            if t in slot_allow[s]:
                rest = [x for x in rem if x != t]
                if max_matching(slot_allow[s + 1:], rest) == len(slot_allow) - s - 1:
                    out.append(t)
                    rem.remove(t)
                    break
        else:
            raise RuntimeError("infeasible third assignment")
    return out


def main():
    ratings0 = dict(pd.read_csv(ROOT / "04_analysis_modules/01_team_strength/tables/elo_current.csv")
                    [["team", "rating"]].to_numpy())
    p = json.loads((ROOT / "04_analysis_modules/02_match_model/tables/model_params.json").read_text())
    b0, b1, draw_rate = p["b0"], p["b1"], p["draw_rate"]
    bracket = json.loads((PROC / "bracket.json").read_text())
    wc = pd.read_csv(PROC / "wc2026_matches.csv")
    gc = bracket["ground_country"]

    group_of = {t: g for g, ts in bracket["groups"].items() for t in ts}
    teams = sorted(group_of)
    assert len(teams) == 48

    # group fixtures (72): (home, away, neutral, played, gh, ga)
    gs = wc[wc["group"].notna()].sort_values("date")
    assert len(gs) == 72
    fixtures = []
    for r in gs.itertuples():
        played = pd.notna(r.home_score)
        fixtures.append((r.home_team, r.away_team, bool(r.neutral), played,
                         int(r.home_score) if played else -1, int(r.away_score) if played else -1))

    # knockout bracket
    ko = sorted(bracket["knockout"], key=lambda m: m["num"])
    r32 = [m for m in ko if m["round"] == "Round of 32"]
    third_slots = []  # (match_num, slot_index_in_match, allowed_groups)
    for m in r32:
        for slot, code in (("team1", m["team1"]), ("team2", m["team2"])):
            if code.startswith("3"):
                third_slots.append((m["num"], slot, set(code[1:].split("/"))))
    round_key = {"Round of 32": "r32", "Round of 16": "r16", "Quarter-final": "qf",
                 "Semi-final": "sf", "Final": "final"}

    def host_adv(team, ground):
        return HOME_ADV if (team in HOSTS and gc.get(ground) == team) else 0.0

    champ = {t: 0 for t in teams}
    reach = {k: {t: 0 for t in teams} for k in round_key.values()}
    rng = np.random.default_rng(SEED)

    for _ in range(N_SIMS):
        r = dict(ratings0)
        pts = {t: 0 for t in teams}
        gf = {t: 0 for t in teams}
        ga = {t: 0 for t in teams}
        for home, away, neutral, played, gh, ga_ in fixtures:
            hadv = 0.0 if neutral else HOME_ADV
            if not played:
                gh, ga_ = sample_score(rng, r[home], r[away], hadv, b0, b1, draw_rate)
            gf[home] += gh; ga[home] += ga_; gf[away] += ga_; ga[away] += gh
            if gh > ga_:
                pts[home] += 3
            elif gh < ga_:
                pts[away] += 3
            else:
                pts[home] += 1; pts[away] += 1
            r[home], r[away] = update(r[home], r[away], hadv, gh, ga_)

        # standings: points, GD, GF, random
        slot = {}
        thirds = []
        for g, members in bracket["groups"].items():
            order = sorted(members, key=lambda t: (pts[t], gf[t] - ga[t], gf[t], rng.random()), reverse=True)
            slot[f"1{g}"], slot[f"2{g}"] = order[0], order[1]
            thirds.append(order[2])
        thirds_best = sorted(thirds, key=lambda t: (pts[t], gf[t] - ga[t], gf[t], rng.random()), reverse=True)[:8]
        qual_groups = [group_of[t] for t in thirds_best]
        slot_allow = [grps for (_, _, grps) in third_slots]
        chosen_groups = assign_thirds(slot_allow, qual_groups)
        third_by_group = {group_of[t]: t for t in thirds_best}
        for (mnum, mslot, _), g in zip(third_slots, chosen_groups):
            slot[f"__{mnum}_{mslot}"] = third_by_group[g]

        winners, losers = {}, {}

        def team_for(code, mnum, mslot):
            if code.startswith("W"):
                return winners[int(code[1:])]
            if code.startswith("L"):
                return losers[int(code[1:])]
            if code.startswith("3"):
                return slot[f"__{mnum}_{mslot}"]
            return slot[code]

        for m in ko:
            t1 = team_for(m["team1"], m["num"], "team1")
            t2 = team_for(m["team2"], m["num"], "team2")
            if m["round"] in round_key:  # "Match for third place" counts toward no stage
                reach[round_key[m["round"]]][t1] += 1
                reach[round_key[m["round"]]][t2] += 1
            hadv = host_adv(t1, m["ground"]) - host_adv(t2, m["ground"])
            g1, g2 = sample_score(rng, r[t1], r[t2], hadv, b0, b1, draw_rate)
            if g1 == g2:
                t1_adv = rng.random() < win_exp(r[t1] - r[t2] + hadv)
            else:
                t1_adv = g1 > g2
            r[t1], r[t2] = update(r[t1], r[t2], hadv, g1, g2)
            w, l = (t1, t2) if t1_adv else (t2, t1)
            winners[m["num"]], losers[m["num"]] = w, l
            if m["round"] == "Final":
                champ[w] += 1

    # --- compare to production headline ---
    prod = pd.read_csv(ROOT / "04_analysis_modules/03_simulation/tables/team_probs.csv").set_index("team")
    rows = []
    for t in teams:
        rows.append(dict(team=t, indep_champ=champ[t] / N_SIMS, prod_champ=float(prod.loc[t, "p_champion"]),
                         indep_r16=reach["r16"][t] / N_SIMS, prod_r16=float(prod.loc[t, "p_r16"])))
    df = pd.DataFrame(rows)
    df["champ_diff"] = (df["indep_champ"] - df["prod_champ"]).abs()
    df["r16_diff"] = (df["indep_r16"] - df["prod_r16"]).abs()
    df = df.sort_values("prod_champ", ascending=False)

    (Path(__file__).parent / "tables").mkdir(exist_ok=True)
    df.to_csv(Path(__file__).parent / "tables" / "recompute_comparison.csv", index=False)

    # MC tolerance: 2 indep runs of 20k each, SE ~ sqrt(2*p(1-p)/N). Use 4*SE,
    # floored at 0.5pp, as the per-team band.
    top = df[df["prod_champ"] >= 0.02]
    max_champ = float(df["champ_diff"].max())
    max_top = float(top["champ_diff"].max())
    se = np.sqrt(2 * top["prod_champ"] * (1 - top["prod_champ"]) / N_SIMS)
    band = float(np.maximum(4 * se, 0.005).max())
    print(df.head(10)[["team", "indep_champ", "prod_champ", "champ_diff", "indep_r16", "prod_r16"]].round(4).to_string(index=False))
    print(f"\nmax champ diff (all 48): {max_champ:.4f} | max among top teams (p>=2%): {max_top:.4f}")
    print(f"MC tolerance band (4*SE, top teams): {band:.4f}")
    ok = max_top <= band and max_champ <= 0.01
    print(f"INDEPENDENT RECOMPUTE {'PASS' if ok else 'FAIL'} — "
          f"{'agrees within MC error' if ok else 'DIVERGENCE, investigate'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
