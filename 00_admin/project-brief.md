# Project Brief: World Cup 2026 Pulse — open stats & prediction platform

- **Date:** 2026-06-12
- **Owner:** Adir (adir_jr@hotmail.com)
- **Mode:** full
- **Status:** SIGNED 2026-06-12 by Adir (with D03 amended: play diagrams dropped entirely; predictions + updating stats are the core)

## Question
Can we build a beautiful, interactive (Three.js), $0-cost, fully legal platform that shows World Cup 2026 stats and produces transparent, Bayesian-updating predictions for match outcomes, knockout advancement, and the champion?

## Interrogation
1. **Target quantity (model):** For every remaining 2026 match: P(home win / draw / away win) and expected scoreline distribution. For every team: P(advance from group), P(reach each knockout round), P(champion). All probabilities re-estimated after each completed match.
2. **Population:** The 48 teams and 104 matches of FIFA World Cup 2026 (2026-06-11 → 2026-07-19). Training population: men's international A-matches from the CC0 historical results dataset (exclusions — e.g., friendlies down-weighting, era cutoff — to be fixed in the spec).
3. **Comparison (baseline to beat):** (a) uniform 1/3-1/3-1/3 baseline; (b) raw-Elo win-expectancy baseline. Model must beat both on log-loss / ranked probability score over 2026 matches as they complete.
4. **Mechanism:** Team attacking/defensive strength drives goal rates; goals → outcomes via a Poisson-family scoring model; strengths drift, so posteriors update with each observed result (Bayesian updating).
5. **Kill condition:** If by end of group stage (72 matches) the model's log-loss is worse than the raw-Elo baseline, the model is demoted on the site to "experimental" and the baseline becomes the headline prediction.
6. **Sub-claims:** (C-candidates) match-level calibration; advancement probabilities consistent under simulation; champion odds stable under random-seed variation.

## Delivery
- **Audience:** Public football fans + anyone auditing the model (the platform doubles as a portfolio piece of transparent modeling).
- **Decision supported:** None high-stakes — entertainment + education. This lowers the risk bar but NOT the transparency bar (the whole point).
- **Format:** Static Three.js web app + auto-updating data/model pipeline + `MODEL.md` (full model card: assumptions, math, priors, update rule, evaluation, limitations) + public git history as the audit log.
- **Technical level:** Layered — fan-friendly visuals up front, full math documentation one click away.
- **In scope:** tournament stats (teams, scorers, standings) updating as the cup progresses, near-live scores/moments, Bayesian-updating predictions (match / advancement / champion) — predictions and updating stats are the core (owner, 2026-06-12).
- **Out of scope:** game play diagrams of any kind (D03), true real-time positional data, betting advice, in-match possession/shot feeds (paid-only), any scraping that violates a site's ToS.
- **Credibility bar:** Every number on the site traceable to a pipeline script and a public data source; model reproducible by a stranger from the repo alone; prediction history immutable in git.
