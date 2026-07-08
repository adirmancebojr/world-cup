# STATUS — World Cup 2026 Pulse

> Regenerated 2026-06-15 22:18 America/Los_Angeles. Never hand-edit; underlying files win.

## Where we are
The model/site pipeline has been refreshed with the latest public data available from the approved sources. The static site now reports results through 2026-06-15, with 16 played WC26 matches and a model run generated at 2026-06-16 05:17 UTC.
- [x] Brief + D01-D08 logged; spec FROZEN
- [x] Pipeline built + validated; environment pinned; drift baseline recorded
- [x] Modules 01-03 run; claims challenged; findings filed
- [x] C01 remediation resolved (D06 retry failed -> D07 raw-Elo headline)
- [x] C02/C03/C04 signed `supported`; raw-Elo headline ratified
- [x] Latest data refresh completed and browser-verified (2026-06-15)
- ➜ [ ] Commit pending work and deploy when ready
- [ ] Referee pass on MODEL.md + pipeline

## Since your last visit
Latest refresh fetched `results.csv`, `shootouts.csv`, and `worldcup2026.json` at 2026-06-16 05:10 UTC. `results.csv` still lagged at 2026-06-14 for World Cup scores, but openfootball had the four 2026-06-15 full-time results; the cleaner now fills missing WC 2026 scores from openfootball and still fails on any cross-source score disagreement. Cleaning passed with 0 cross-source score mismatches. Elo, prediction tracking, full tournament simulation, seed stability, independent recompute, site JSON, and champion history were rerun.

## Needs you
- [ ] Decide when to commit/deploy the accumulated site + data refresh work.
- [ ] Optional: run a fresh-session referee pass before public deployment.

## Nudges
- **Uncommitted work remains substantial.** This includes earlier site/methodology changes plus the latest raw-data/model refresh.
- **Public data delay still applies.** The site is current through the latest public source data pulled here, not a live official feed.

## Claims
| ID | Claim | Status | Last moved by |
|---|---|---|---|
| C01 | Model beats baselines | **not_supported** (closed) | agent 2026-06-12 |
| C02 | Probabilities calibrated | **supported** (signed Adir) | Adir 2026-06-12 |
| C03 | Simulation internally consistent | **supported** | refreshed pass 2026-06-15 |
| C04 | Champion odds seed-stable | **supported** | refreshed pass 2026-06-15 |

## Recent decisions & findings
- 2026-06-15 PDT refresh: processed historical matches advanced to 49,421 rows through 2026-06-15; WC26 site data now has 16 played matches.
- June 15 results added from openfootball fallback: Belgium 1-1 Egypt, Iran 2-2 New Zealand, Spain 0-0 Cape Verde, Saudi Arabia 1-1 Uruguay.
- Prediction tracker: outcome calls 6/16 (38%), exact scores 3/16 (19%), mean log-loss 1.1751 vs uniform 1.0986.
- Simulation: Argentina 16.970%, Spain 12.420%, France 10.215%, England 6.285%, Colombia 5.435%, Brazil 4.845%.
- Independent recompute: PASS, max champion-probability difference 0.44pp vs 1.50pp Monte Carlo tolerance band.

## Pipeline health
Manual refresh checks: 0 cross-source score mismatches; C03 passed; C04 passed with max seed spread 1.10pp; independent recompute passed; site JSON reports results through 2026-06-15.

## Next step
Commit/deploy the refreshed site when ready. If keeping strict agentic-ds discipline before public launch, run a fresh-session referee pass on `MODEL.md`, the claims register, and the refreshed pipeline.
