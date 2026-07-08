"""Monte Carlo simulation of the remaining WC 2026 per frozen spec Layer 3
and D07 (outcomes from headline raw-Elo probabilities).
Headline run: 20,000 sims, seed 42. Stability: seeds 1..5 x 20,000 (C04);
set WC_SKIP_STABILITY=1 to skip the stability runs (scheduled refreshes —
C04 was established interactively and re-checked at milestones).
Tests claims C03 and C04."""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03_pipeline"))
import wcmodel  # noqa: E402

MOD = Path(__file__).resolve().parent
N_SIMS = 20_000
HEADLINE_SEED = 42
STABILITY_SEEDS = [] if os.environ.get("WC_SKIP_STABILITY") == "1" else [1, 2, 3, 4, 5]
STAGES = ["r32", "r16", "qf", "sf", "final", "champion"]
HOST_COUNTRIES = {"United States", "Mexico", "Canada"}


def kuhn_matching_size(slot_sets: list[set], items: list[str]) -> int:
    match_of_item: dict[str, int] = {}

    def try_slot(si: int, seen: set) -> bool:
        for it in items:
            if it in slot_sets[si] and it not in seen:
                seen.add(it)
                if it not in match_of_item or try_slot(match_of_item[it], seen):
                    match_of_item[it] = si
                    return True
        return False

    return sum(try_slot(si, set()) for si in range(len(slot_sets)))


def assign_thirds(slot_sets: list[set], thirds_ranked: list[str]) -> list[str]:
    """D05: deterministic greedy — slots in match order get the best-ranked
    eligible third whose assignment keeps a perfect matching feasible."""
    remaining = list(thirds_ranked)
    out = []
    for si in range(len(slot_sets)):
        for t in remaining:
            if t in slot_sets[si]:
                rest_slots = slot_sets[si + 1:]
                rest = [x for x in remaining if x != t]
                if kuhn_matching_size(rest_slots, rest) == len(rest_slots):
                    out.append(t)
                    remaining.remove(t)
                    break
        else:
            raise RuntimeError("no feasible third-place assignment")
    return out


def main() -> int:
    ratings_df = pd.read_csv(ROOT / "04_analysis_modules/01_team_strength/tables/elo_current.csv")
    params = json.loads((ROOT / "04_analysis_modules/02_match_model/tables/model_params.json").read_text())
    wc = pd.read_csv(ROOT / "02_processed_data/wc2026_matches.csv")
    as_of = os.environ.get("WC_AS_OF")
    if as_of:  # replay the tournament as of this day: matches after it are unplayed
        wc.loc[wc["date"] > as_of, ["home_score", "away_score"]] = np.nan
    # WC_BRACKET_FILE: the history backfill passes an era-correct bracket (the
    # placeholder bracket for group-stage days) so past snapshots can't leak
    # knockout draws that weren't known yet. Unset = live bracket.
    bracket_file = os.environ.get("WC_BRACKET_FILE") or (ROOT / "02_processed_data/bracket.json")
    bracket = json.loads(Path(bracket_file).read_text())
    b0, b1 = params["b0"], params["b1"]

    draw_rate = params["draw_rate"]

    def sample_match(rng, r1, r2, hadv):
        """D07: outcome from headline raw-Elo probs; scoreline from the
        experimental Poisson grid conditional on that outcome."""
        pw, pdr, pl = wcmodel.raw_elo_baseline(r1, r2, hadv, draw_rate)
        u = rng.random()
        outcome = 0 if u < pw else (1 if u < pw + pdr else 2)
        lam_h, lam_a = wcmodel.goal_rates(r1, r2, hadv, b0, b1)
        m = wcmodel.score_matrix(lam_h, lam_a)
        mask = np.tril(np.ones_like(m, bool), -1) if outcome == 0 else (
            np.eye(m.shape[0], dtype=bool) if outcome == 1 else np.triu(np.ones_like(m, bool), 1))
        cond = np.where(mask, m, 0.0).ravel()
        idx = int(np.searchsorted(np.cumsum(cond), rng.random() * cond.sum()))
        return divmod(idx, m.shape[0])

    teams = sorted(set(wc["home_team"]) | set(wc["away_team"]))
    tix = {t: i for i, t in enumerate(teams)}
    base_ratings = np.array([float(ratings_df.set_index("team")["rating"][t]) for t in teams])
    group_of = {}
    for g, members in bracket["groups"].items():
        for t in members:
            group_of[tix[t]] = g
    groups = {g: [tix[t] for t in members] for g, members in bracket["groups"].items()}

    # group-stage fixtures only — knockout rows (group=NaN) appear in
    # wc2026_matches.csv from 06-28 and are handled via played_ko below
    gs = wc[wc["group"].notna()].sort_values("date", kind="stable")
    assert len(gs) == 72
    fx_h = gs["home_team"].map(tix).to_numpy()
    fx_a = gs["away_team"].map(tix).to_numpy()
    fx_neutral = gs["neutral"].to_numpy(bool)
    fx_played = gs["home_score"].notna().to_numpy()
    fx_hs = gs["home_score"].fillna(-1).to_numpy(int)
    fx_as = gs["away_score"].fillna(-1).to_numpy(int)

    # played knockout results are FIXED, not simulated (knockouts from 06-28).
    # keyed by team pair (a pair can meet at most once outside its group);
    # 90'/120' draws need the shootout winner from wc2026_shootouts.csv.
    ko_rows = wc[wc["group"].isna() & wc["home_score"].notna()]
    shootouts = pd.read_csv(ROOT / "02_processed_data/wc2026_shootouts.csv")
    so_winner = {frozenset((r.home_team, r.away_team)): r.winner for r in shootouts.itertuples()}
    played_ko: dict[frozenset, tuple] = {}
    for r in ko_rows.itertuples():
        hs, as_ = int(r.home_score), int(r.away_score)
        key = frozenset((r.home_team, r.away_team))
        if hs != as_:
            winner = r.home_team if hs > as_ else r.away_team
        elif key in so_winner:
            winner = so_winner[key]
        else:
            continue  # draw with no shootout row yet -> leave to simulation
        played_ko[key] = (r.home_team, hs, as_, winner)

    ko = bracket["knockout"]
    r32 = [m for m in ko if m["round"] == "Round of 32"]
    later = [m for m in ko if m["round"] != "Round of 32"]
    third_slot_sets = []
    for m in r32:
        for code in (m["team1"], m["team2"]):
            if code.startswith("3"):
                third_slot_sets.append(set(code[1:].split("/")))
    ground_country = bracket["ground_country"]

    def host_adv(i_team: int, ground: str) -> float:
        t = teams[i_team]
        return wcmodel.HOME_ADV if (t in HOST_COUNTRIES and ground_country.get(ground) == t) else 0.0

    def run(seed: int, n_sims: int) -> dict[str, np.ndarray]:
        rng = np.random.default_rng(seed)
        counts = {s: np.zeros(len(teams)) for s in STAGES}
        counts["group_win"] = np.zeros(len(teams))
        for _ in range(n_sims):
            r = base_ratings.copy()
            pts = np.zeros(len(teams))
            gf = np.zeros(len(teams))
            ga = np.zeros(len(teams))
            # --- group stage ---
            for i in range(len(fx_h)):
                h, a = fx_h[i], fx_a[i]
                if fx_played[i]:
                    gh, gaa = fx_hs[i], fx_as[i]
                else:
                    hadv = 0.0 if fx_neutral[i] else wcmodel.HOME_ADV
                    gh, gaa = sample_match(rng, r[h], r[a], hadv)
                gf[h] += gh; ga[h] += gaa; gf[a] += gaa; ga[a] += gh
                if gh > gaa:
                    pts[h] += 3
                elif gh < gaa:
                    pts[a] += 3
                else:
                    pts[h] += 1; pts[a] += 1
                hadv = 0.0 if fx_neutral[i] else wcmodel.HOME_ADV
                r[h], r[a] = wcmodel.elo_update(r[h], r[a], hadv, gh, gaa)
            # --- standings: points, GD, GF, then random (spec) ---
            slots: dict[str, int] = {}
            thirds = []
            for g, members in groups.items():
                key = sorted(members, key=lambda t: (pts[t], gf[t] - ga[t], gf[t], rng.random()), reverse=True)
                slots[f"1{g}"], slots[f"2{g}"] = key[0], key[1]
                thirds.append(key[2])
                counts["group_win"][key[0]] += 1
            thirds_ranked = sorted(thirds, key=lambda t: (pts[t], gf[t] - ga[t], gf[t], rng.random()), reverse=True)
            qual_thirds = thirds_ranked[:8]
            qual_groups = [group_of[t] for t in qual_thirds]
            assigned = assign_thirds(third_slot_sets, qual_groups)
            third_by_group = {group_of[t]: t for t in qual_thirds}
            third_iter = iter(assigned)
            # --- knockout ---
            winners: dict[int, int] = {}
            losers: dict[int, int] = {}

            def resolve(code: str) -> int:
                if code in tix:  # already a resolved team (a drawn/played knockout round)
                    return tix[code]
                if code.startswith("W"):
                    return winners[int(code[1:])]
                if code.startswith("L"):
                    return losers[int(code[1:])]
                if code.startswith("3"):
                    return third_by_group[next(third_iter)]
                return slots[code]

            for m in r32 + later:
                t1, t2 = resolve(m["team1"]), resolve(m["team2"])
                for s, rnd in (("r32", "Round of 32"), ("r16", "Round of 16"), ("qf", "Quarter-final"), ("sf", "Semi-final"), ("final", "Final")):
                    if m["round"] == rnd:
                        counts[s][t1] += 1; counts[s][t2] += 1
                hadv = host_adv(t1, m["ground"]) - host_adv(t2, m["ground"])
                key = frozenset((teams[t1], teams[t2]))
                if key in played_ko:
                    home_name, g1, g2, winner = played_ko[key]
                    if home_name != teams[t1]:
                        g1, g2 = g2, g1
                    t1_wins = winner == teams[t1]
                else:
                    g1, g2 = sample_match(rng, r[t1], r[t2], hadv)
                    if g1 == g2:  # spec: Bernoulli with Elo expectancy
                        t1_wins = rng.random() < wcmodel.win_expectancy(r[t1] - r[t2] + hadv)
                    else:
                        t1_wins = g1 > g2
                r[t1], r[t2] = wcmodel.elo_update(r[t1], r[t2], hadv, g1, g2)
                w, l = (t1, t2) if t1_wins else (t2, t1)
                winners[m["num"]], losers[m["num"]] = w, l
                if m["round"] == "Final":
                    counts["champion"][w] += 1
        return {k: v / n_sims for k, v in counts.items()}

    t0 = time.time()
    head = run(HEADLINE_SEED, N_SIMS)
    print(f"headline run: {N_SIMS} sims in {time.time() - t0:.0f}s")

    (MOD / "tables").mkdir(exist_ok=True)
    tp = pd.DataFrame({"team": teams, "group": [group_of[i] for i in range(len(teams))],
                       **{f"p_{s}": head[s] for s in STAGES}, "p_group_win": head["group_win"]})
    tp = tp.sort_values("p_champion", ascending=False)
    tp.to_csv(MOD / "tables" / "team_probs.csv", index=False)
    print(tp.head(10)[["team", "p_r32", "p_qf", "p_champion"]].to_string(index=False))

    # --- C03: structural identities + monotonicity ---
    expected = dict(r32=32, r16=16, qf=8, sf=4, final=2, champion=1)
    checks = []
    for s, tot in expected.items():
        checks.append(dict(check=f"sum p_{s} == {tot}", value=float(head[s].sum()), ok=bool(abs(head[s].sum() - tot) < 1e-9)))
    mono = np.all(np.diff(np.vstack([head[s] for s in STAGES]), axis=0) <= 1e-12)
    checks.append(dict(check="per-team monotone across stages", value=float(mono), ok=bool(mono)))
    for g, members in groups.items():
        v = float(sum(head["r32"][t] for t in members))
        checks.append(dict(check=f"group {g} expected qualifiers in [2,3]", value=v, ok=bool(2 - 1e-9 <= v <= 3 + 1e-9)))
    cdf = pd.DataFrame(checks)
    cdf.to_csv(MOD / "tables" / "consistency_checks.csv", index=False)
    c03 = bool(cdf["ok"].all())
    print(f"C03 {'PASS' if c03 else 'FAIL'}")
    if not c03:
        print(cdf[~cdf["ok"]].to_string(index=False))

    # --- C04: seed stability ---
    if STABILITY_SEEDS:
        champ_by_seed = {}
        for seed in STABILITY_SEEDS:
            t0 = time.time()
            champ_by_seed[seed] = run(seed, N_SIMS)["champion"]
            print(f"seed {seed}: {time.time() - t0:.0f}s")
        arr = np.vstack(list(champ_by_seed.values()))
        spread = arr.max(axis=0) - arr.min(axis=0)
        sdf = pd.DataFrame({"team": teams, "p_champ_min": arr.min(axis=0), "p_champ_max": arr.max(axis=0), "spread": spread})
        sdf = sdf.sort_values("spread", ascending=False)
        sdf.to_csv(MOD / "tables" / "seed_stability.csv", index=False)
        c04 = bool((spread < 0.015).all())
        print(f"C04 {'PASS' if c04 else 'FAIL'} (max spread {spread.max():.4f}, team {teams[int(spread.argmax())]})")
    else:
        print("C04 stability runs skipped (WC_SKIP_STABILITY=1); last recorded check stands")

    # --- per-fixture probabilities as of today (for the site) ---
    rows = []
    cur = {t: base_ratings[i] for t, i in tix.items()}
    for i in range(len(fx_h)):
        if fx_played[i]:
            continue
        h, a = teams[fx_h[i]], teams[fx_a[i]]
        hadv = 0.0 if fx_neutral[i] else wcmodel.HOME_ADV
        # headline odds = raw-Elo (D07); Poisson scorelines kept as "experimental"
        pw, pdr, pl = wcmodel.raw_elo_baseline(cur[h], cur[a], hadv, draw_rate)
        lam_h, lam_a = wcmodel.goal_rates(cur[h], cur[a], hadv, b0, b1)
        xw, xd, xl = wcmodel.outcome_probs(lam_h, lam_a)
        m = wcmodel.score_matrix(lam_h, lam_a)
        top = np.unravel_index(np.argsort(m, axis=None)[::-1][:3], m.shape)
        rows.append(dict(date=gs.iloc[i]["date"], home=h, away=a, group=gs.iloc[i]["group"],
                         p_home=pw, p_draw=pdr, p_away=pl,
                         exp_p_home=xw, exp_p_draw=xd, exp_p_away=xl, lam_h=lam_h, lam_a=lam_a,
                         top_scores="; ".join(f"{i_}-{j_} ({m[i_, j_]:.0%})" for i_, j_ in zip(*top))))
    pd.DataFrame(rows).to_csv(MOD / "tables" / "match_probs_group.csv", index=False)
    print(f"wrote match_probs_group.csv ({len(rows)} remaining group fixtures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
