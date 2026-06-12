# Data Availability Research — Free & Legal Sources for World Cup 2026

- **Date:** 2026-06-12 (tournament started 2026-06-11; runs to 2026-07-19)
- **Constraint:** $0 budget, no legal gray zones, deployable for free.
- **Method:** web research (searches + direct fetch of pricing/license pages). Desk research, not yet verified by live API calls — verification is a checklist gate.

## Verdicts by source

### Tier 1 — clearly legal, recommended

| Source | What it gives | License / terms | Latency | Notes |
|---|---|---|---|---|
| [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) | 2026 fixtures, results, group standings, squads as JSON; no API key | **Public domain** | Hours (hand-maintained, wiki-style; auto-rebuilt on commit) | Backbone candidate. A faster community mirror exists (`upbound-web/worldcup-live.json`), reliability unverified. |
| [football-data.org](https://www.football-data.org/pricing) free tier | Fixtures, league tables, scores for 12 competitions **incl. FIFA World Cup** | Official free tier, ToS-sanctioned; 10 calls/min | Scores delayed (free tier excludes true live) | No player stats or lineups on free tier. Good secondary/cross-check feed. |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Full event data for **WC 2018 + WC 2022** (all 64 matches each): every pass/shot/carry with x,y coordinates, xG, freeze frames, 360 frames (2022) | Free with attribution per user agreement (non-commercial) | Historical only — no 2026 | Enables real play diagrams (replay-style) and xG-calibrated model priors. |
| [Kaggle: martj42 international results 1872–2026](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017) | ~49k international match results | CC0 public domain | Updated periodically | Model training backbone. |
| Kaggle Elo ratings datasets ([1](https://www.kaggle.com/datasets/saifalnimri/international-football-elo-ratings), [2](https://www.kaggle.com/datasets/afonsofernandescruz/2026-fifa-world-cup-historical-elo-ratings)) | Historical Elo per team incl. 2026 cohort | CC0 / CC BY-SA 4.0 | Static snapshot | Prior team strengths. We can also recompute Elo ourselves from the CC0 results data — fully reproducible, no license question. |
| Wikipedia / Wikidata | Squads, player bios, tournament metadata | CC BY-SA 4.0 (attribute + share-alike) | Minutes–hours (heavily maintained during WC) | Player-level info source. Attribution footer required. |

### Tier 2 — usable with caveats

| Source | Caveat |
|---|---|
| [rezarahiminia/worldcup2026](https://github.com/rezarahiminia/worldcup2026) (ISC, no key, claims live scores) | Community project sourced from Wikipedia; uptime/accuracy unproven. Optional tertiary cross-check only. |

### Tier 3 — rejected (legal risk or cost)

| Source | Why rejected |
|---|---|
| ESPN "hidden" API (`site.api.espn.com`) | Unofficial/undocumented; usage outside official ESPN clients may violate ESPN ToS ([guide](https://zuplo.com/learning-center/espn-hidden-api-guide), [docs repo](https://github.com/pseudo-r/Public-ESPN-API)). User constraint: "do not want to get sued" → out. |
| Scraping FotMob/Sofascore/FlashScore/FIFA.com | ToS prohibit scraping; same legal-risk rejection. |
| Opta/Stats Perform, Sportmonks, API-Football paid tiers | Cost. API-Football free tier (100 req/day) also excludes live coverage depth we'd want. |
| FiveThirtyEight SPI | Discontinued (site shut down); no 2026 ratings. |

## Feature feasibility (the honest matrix)

| Requested feature | Verdict | How |
|---|---|---|
| Updated team & player tournament stats | ✅ Feasible | openfootball + Wikipedia (squads, scorers) + football-data.org (standings cross-check). |
| Live game statistics (possession, shots, in-match) | ⚠️ Partial | True in-match stat feeds (possession %, shots) are paid-only everywhere. Free ceiling: **near-live scores + goal/card events** (minutes of delay) + post-match stats. |
| Live play diagrams (real positional data, 2026, real time) | ❌ Not free/legal | Live event/tracking data is the most expensive commodity in football. Free alternative: **3D replay diagrams of WC 2018/2022 from StatsBomb event data** (real passes/shots/xG on a Three.js pitch) + **schematic live match timeline** for 2026 (goals/cards/subs rendered as match moments on the 3D pitch). |
| Bayesian-updating predictions (match, advancement, champion) | ✅ Fully feasible | Own model from CC0 data: team-strength goals model (Poisson family) with Elo-informed priors, posterior updated after every 2026 result, Monte Carlo simulation of the remaining bracket. 100% transparent and reproducible. |

## Architecture implication (hosting research)

Railway no longer has a true free tier (one-time $5 trial credit, then ~$1/mo credit — [pricing](https://www.srvrlss.io/provider/railway/)). Better $0 fit: **no backend at all** —
- A scheduled **GitHub Actions** workflow (free cron) pulls Tier-1 sources, recomputes the model, commits static JSON.
- The **Three.js frontend is a static site** reading those JSON files; host on **GitHub Pages** or **Cloudflare Pages** (free, unlimited bandwidth, non-commercial fine).
- Bonus for auditability: **every model update is a git commit** — the entire prediction history is public, diffable, and reproducible by anyone. The audit log is the git log.

## Sources consulted
- https://www.football-data.org/pricing
- https://github.com/openfootball/worldcup.json
- https://github.com/statsbomb/open-data
- https://blogarchive.statsbomb.com/news/statsbomb-release-free-2022-world-cup-data/
- https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017
- https://www.kaggle.com/datasets/saifalnimri/international-football-elo-ratings
- https://www.kaggle.com/datasets/afonsofernandescruz/2026-fifa-world-cup-historical-elo-ratings
- https://github.com/rezarahiminia/worldcup2026
- https://zuplo.com/learning-center/espn-hidden-api-guide
- https://github.com/pseudo-r/Public-ESPN-API
- https://www.thestatsapi.com/blog/free-world-cup-api-alternatives
- https://www.srvrlss.io/provider/railway/
- https://agentdeals.dev/hosting-free-tier-comparison-2026
