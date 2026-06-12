# Analysis Spec: World Cup 2026 prediction model

- **Status:** FROZEN 2026-06-12 by Adir ("freeze it")
- Deviations after freezing require a decision-log entry BEFORE the changed analysis runs.
- **Amendment A1 (2026-06-12, per D06):** after C01 failed as specified, the owner authorized the Dixon-Coles draw correction (the alternative this spec had named) via decision D06: joint MLE of (β0, β1, ρ), τ-adjusted renormalized score grid, one re-run of the identical backtest, adopt iff C01's original criteria pass.
- This spec is the source for the public `MODEL.md` model card. Nothing is fit until it is frozen.

## Model overview (three layers, all transparent)

**Layer 1 — Team strength (Elo, recomputed from scratch).**
Ratings computed from the CC0 results data, 1872 → present, by us — no dependence on third-party ratings.

- Update rule: `R' = R + K · G · (W − W_e)` where `W ∈ {1, 0.5, 0}` (win/draw/loss) and win expectancy `W_e = 1 / (1 + 10^(−ΔR/400))`, with `ΔR = R_team − R_opponent + 100·home` (home = 1 if not a neutral venue, using the dataset's `neutral` flag).
- K by match importance: World Cup finals 60; continental finals 50; WC & continental qualifiers 40; other tournaments 30; friendlies 20.
- Goal-difference multiplier G: 1 if margin ≤ 1; 1.5 if margin = 2; `(11 + N) / 8` if margin N ≥ 3.
- Initial rating 1500 for every team at first appearance.
- *Alternatives considered:* Glicko (adds rating variance — deferred to v2, adds opacity); using published eloratings.net values (rejected: scraping/license ambiguity, not reproducible by a stranger).

**Layer 2 — Scoreline model (Poisson regression on Elo difference).**
For a match i vs j: each team's goal count `~ Poisson(λ)` independently, with
`log λ_i = β0 + β1 · (R_i − R_j + 100·home_i) / 400` (symmetric for j).

- β0, β1 fit once by Poisson MLE on competitive internationals (friendlies excluded) from 2018-01-01 to 2026-06-10, then **frozen for the whole tournament** — only ratings move after that.
- Match outcome probabilities P(win/draw/loss) and scoreline distribution from the Poisson grid (0–10 goals each side).
- *Alternatives considered:* Dixon-Coles low-score correction and bivariate Poisson (deferred — adopt only via logged decision if C02 calibration fails); including friendlies with a dummy (rejected for v1: simplicity).

**Layer 3 — Sequential updating + tournament simulation.**
- After every completed 2026 match, the Elo update (K=60) moves both teams' ratings; all future predictions use the new ratings. This is the "Bayesian-style" sequential update — and `MODEL.md` will say honestly that it is a point-estimate filter, not a full posterior.
- Tournament outcomes by Monte Carlo: **20,000 replications** of the remaining tournament, fixed base seed (42) + replication index. Within each replication, simulated results also update ratings, so strength evolves in-sim.
- 2026 format rules implemented exactly: 12 groups of 4; top 2 per group + 8 best third-placed teams to a round of 32; FIFA bracket mapping; tie-breakers (points, GD, goals scored, then random as proxy for drawing of lots).
- Knockout draws after 90': winner drawn Bernoulli with Elo expectancy `W_e` (extra time + penalties not modeled separately in v1; *alternative considered:* explicit ET Poisson at 1/3 rate + 50/50 penalties — deferred).
- Published outputs per model run: per match P(W/D/L) + scoreline heatmap; per team P(advance group), P(reach R32/R16/QF/SF/F), P(champion).

## Metric definitions
| Metric | Formula | Units | Notes |
|---|---|---|---|
| Log-loss | −mean(log p(observed W/D/L)) | nats | Primary eval metric, chosen before fitting |
| RPS | mean ranked probability score over ordered (W,D,L) | — | Secondary |
| Calibration gap | max over bins (n≥30) of \|predicted − observed\| frequency | pp | Reliability curve, 10 bins |

## Population and filters
- Training (Elo): all men's full internationals in `results.csv`, 1872 → prediction date.
- Training (β): competitive matches only (tournament ≠ "Friendly"), 2018-01-01 → 2026-06-10.
- Prediction target: the 104 matches of WC 2026.
- Cleaning rules: scores coerced to int with explicit anomaly log (known: "00" typo, SA row 2026-06-11); team-name harmonization table between martj42 and openfootball names, kept as a versioned CSV.

## Comparisons and baselines
1. **Uniform:** P = (1/3, 1/3, 1/3).
2. **Raw-Elo:** W_e split to W/D/L using the historical draw rate of competitive internationals (computed once on the β training window).

## Backtest (split design, leakage rules)
- Held-out tournaments: **WC 2014, 2018, 2022.** For each: Elo from all data strictly before tournament start; β fit on the prior 8 years of competitive matches; predict all 64 matches sequentially with in-tournament Elo updating, exactly as 2026 will run.
- Leakage rules: any prediction may use only matches with date < that match's date; β never refit inside a tournament; no squad/player/market information anywhere in the model.

## Challenges (one per candidate claim)
| Claim | Challenge | Expected if real |
|---|---|---|
| C01 model beats baselines | Pooled backtest log-loss < both baselines AND beats raw-Elo in ≥2 of 3 tournaments | Passes both |
| C02 probabilities are calibrated | Reliability curve on pooled backtest; calibration gap < 10pp | Within band |
| C03 simulation is internally consistent | Σ P(champion) = 1 ± MC error; per group, Σ P(advance) ≈ expected qualifier count; monotone round probabilities per team | All identities hold |
| C04 outputs are seed-stable | 5 independent seeds × 20k sims: max champion-prob spread < 1.5pp for any team | Within band |

## Decision thresholds
- **Ship:** publish model predictions as headline only if C01–C04 pass and Adir signs.
- **Kill (from brief):** if cumulative 2026 log-loss > raw-Elo baseline at end of group stage, demote model to "experimental" on the site; baseline becomes headline.

## Robustness checks
- Champion-odds sensitivity to: K_WC ∈ {45, 60, 75}; β fit window {2014–, 2018–, 2022–}; friendlies in/out of β fit. Reported in MODEL.md, not silently chosen.

## Modeling project requirements
- **Evaluation metric:** log-loss (primary), RPS (secondary) — fixed here, before fitting.
- **Split design:** time-based (backtest tournaments above).
- **Leakage rules:** as above.
- **Baseline to beat:** raw-Elo expectancy baseline.
