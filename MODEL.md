# MODEL.md — how the predictions work, exactly

**TL;DR — read this part even if you skip the math.** The headline match odds on this site come from a simple, transparent Elo baseline. We built a fancier Poisson scoring model, pre-registered a test it had to pass to earn the headline spot — **and it failed, twice**. We publish it anyway, demoted and labeled *experimental*, because the failure is part of the story. Every number is reproducible from public, freely-licensed data with the code in this repository, and every model update is a git commit you can diff.

---

## 1. Principles

1. **Pre-registration:** metrics, baselines, data filters, and pass/fail thresholds were frozen in [`00_admin/analysis-spec.md`](00_admin/analysis-spec.md) *before* any model was fit ("frozen 2026-06-12").
2. **No silent changes:** every deviation is a numbered entry in [`00_admin/decision-log.md`](00_admin/decision-log.md) written *before* the changed analysis ran.
3. **Every number traces to a script:** see `audit/source_trace.csv` in each module.
4. **The audit log is the git log:** the scheduled pipeline commits its inputs and outputs, so the full prediction history is public and immutable.

## 2. Data (all free, all legal)

| Dataset | Used for | License |
|---|---|---|
| [martj42/international_results](https://github.com/martj42/international_results) — 49k+ men's internationals, 1872→present, updated within ~1 day | Elo ratings, model fitting, 2026 results | CC0-1.0 |
| [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) — 2026 fixtures, groups, bracket, goalscorers | Tournament structure, scorers, cross-validation | Public domain |

Raw snapshots are checksummed in `01_raw_data/manifest.json`. Cleaning is one script ([`03_pipeline/02_clean.py`](03_pipeline/02_clean.py)) that logs every coercion and cross-checks scores between the two sources (build fails on disagreement).

## 3. Layer 1 — Team strength: Elo, recomputed from scratch

We do not import anyone's ratings. We replay all ~49,400 matches since 1872:

- `R' = R + K · G · (W − W_e)`, `W_e = 1 / (1 + 10^(−ΔR/400))`, `ΔR = R_team − R_opp + 100·home` (home = non-neutral venue per the dataset).
- K by importance: World Cup 60 · continental finals 50 · qualifiers 40 · other tournaments 30 · friendlies 20.
- Goal-difference multiplier G: 1 (margin ≤ 1) · 1.5 (margin 2) · (11+N)/8 (margin N ≥ 3).
- Everyone starts at 1500. Ratings are zero-sum (verified in-script).

During the tournament, each result updates ratings with K=60 — that sequential update is what makes every probability on the site move as the cup progresses.

## 4. Headline match odds (what you see first)

**Raw-Elo baseline:** `P(draw) = d` (the 2018–2026 competitive-match draw frequency, d ≈ 0.219), `P(home win) = (1−d)·W_e`, `P(away win) = (1−d)·(1−W_e)`.

Why so simple? Because it won. See §6.

## 5. Experimental layer — Poisson scorelines

Each team's goals ~ Poisson with `log λ = β0 + β1 · (ΔR + home adv)/400`, β fit by MLE on competitive internationals 2018-01-01 → 2026-06-10 (β0 = 0.1726, β1 = 0.7560, n = 5,836) and **frozen for the whole tournament**. This layer produces the scoreline heatmaps (labeled *experimental*) and, conditioned on the headline outcome, the goals needed for group tie-breakers inside the simulator (decision D07).

## 6. The honest part: the pre-registered test, and two failures

The spec required the model to beat two baselines on log-loss over **192 held-out matches** (every match of WC 2014, 2018, 2022, predicted sequentially with in-tournament Elo updating, β fit only on data before each tournament — no leakage):

| Method | Pooled log-loss | Beats raw-Elo in N/3 tournaments |
|---|---|---|
| Uniform (⅓,⅓,⅓) | 1.0986 | — |
| **Raw-Elo baseline** | **0.9831** | — |
| Poisson model (spec) | 0.9858 | 1/3 |
| Poisson + Dixon-Coles (D06 retry) | 0.9870 | 1/3 |

- **Attempt 1 (spec model): failed C01.** Filed as `not_supported` ([finding](05_claims/findings/2026-06-12_c01-backtest-model-vs-baselines.md)).
- **Attempt 2 (D06):** one pre-registered fix — Dixon-Coles draw correction, the mechanism we diagnosed. The fitted correlation was tiny (ρ ≈ −0.03) and out-of-sample it was *worse* ([finding](05_claims/findings/2026-06-12_c01-dixon-coles-rerun.md)). Per D06's own rule, no further attempts; the baseline takes the headline.

What *did* pass: **calibration** (C02 — max reliability gap 7pp, band 10pp), **simulator consistency** (C03 — all structural identities exact), and **seed stability** (C04 — champion odds move < 0.8pp across seeds).

## 7. Tournament simulation

20,000 Monte Carlo replays of the remaining tournament (seed 42), after every data refresh:

- Match outcomes sampled from the **headline** probabilities (so champion odds never contradict the match odds you see — D07); scorelines from the experimental grid conditional on the outcome.
- Exact 2026 format: 12 groups of 4 → top 2 + 8 best thirds → round of 32 with FIFA's slot constraints (third-place slots resolved by a deterministic feasibility matching — D05, our one documented approximation), numbered bracket through the final.
- Group tie-breaks: points, goal difference, goals scored, then random (proxy for FIFA's lower criteria).
- Hosts get +100 Elo when playing in their own country (group stage per the dataset's venue flags; knockouts via a stadium→country map).
- Knockout 90' draws: winner ~ Bernoulli(Elo win expectancy). Played knockout matches are fixed, with shootout winners from the data.
- Ratings evolve *inside* each simulated future, so a simulated upset makes the upsetter stronger downstream.

## 8. Known limitations (pre-registered or logged)

- No player-level information: injuries, suspensions, squad quality changes are invisible until they show up in results.
- "Live" means near-live: sources update within minutes–hours, not seconds (D02).
- Knockout scores in the historical backtest include extra time (the dataset's convention).
- Group tie-break randomness stands in for head-to-head; third-place allocation is a constraint-respecting approximation of FIFA's table (D05).
- The experimental Poisson layer failed its headline test (§6) — treat scoreline heatmaps as illustrative.

## 9. Reproduce it

```bash
git clone <this repo> && cd world-cup
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python 03_pipeline/01_fetch_raw.py        # snapshot data (or use committed snapshots)
.venv/bin/python 03_pipeline/02_clean.py            # validate + clean
.venv/bin/python 04_analysis_modules/01_team_strength/01_compute_elo.py
.venv/bin/python 04_analysis_modules/02_match_model/01_backtest.py   # re-run the honest backtest yourself
.venv/bin/python 04_analysis_modules/03_simulation/01_simulate.py    # 120k sims, ~4 min
.venv/bin/python 03_pipeline/03_build_site_data.py  # rebuild the site JSON
```

Environment pins in `requirements.txt`; the audit trail (spec, decisions, claims, findings) lives in `00_admin/` and `05_claims/`.
