# STATUS — World Cup 2026 Pulse

> Regenerated 2026-06-15 00:35 America/Los_Angeles. Never hand-edit; underlying files win.

## Where we are
The model/site pipeline has been refreshed with the latest public data available from the approved sources. The static site now reports results through 2026-06-14, with 12 played WC26 matches and a model run generated at 2026-06-15 07:29 UTC.
- [x] Brief + D01-D08 logged; spec FROZEN
- [x] Pipeline built + validated; environment pinned; drift baseline recorded
- [x] Modules 01-03 run; claims challenged; findings filed
- [x] C01 remediation resolved (D06 retry failed -> D07 raw-Elo headline)
- [x] C02/C03/C04 signed `supported`; raw-Elo headline ratified
- [x] Latest data refresh completed and browser-verified (2026-06-15)
- ➜ [ ] Commit pending work and deploy when ready
- [ ] Referee pass on MODEL.md + pipeline

## Since your last visit
Latest refresh fetched `results.csv`, `shootouts.csv`, and `worldcup2026.json` at 2026-06-15 07:17 UTC. Cleaning passed with 0 cross-source score mismatches. Elo, prediction tracking, full tournament simulation, seed stability, independent recompute, site JSON, and champion history were rerun. Browser smoke test confirmed the refreshed public page renders the updated odds and prediction results with no console warnings.

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
- 2026-06-15 refresh: processed historical matches advanced to 49,417 rows through 2026-06-14; WC26 site data now has 12 played matches and 15 scorers.
- Prediction tracker: outcome calls 6/12 (50%), exact scores 3/12 (25%), mean log-loss 1.0614 vs uniform 1.0986.
- Simulation: Spain 17.965%, Argentina 15.660%, France 9.335%, England 6.495%, Colombia 5.140%, Brazil 4.670%.
- Independent recompute: PASS, max champion-probability difference 0.47pp vs 1.54pp Monte Carlo tolerance band.

## Pipeline health
Fresh: 30 | Stale: 0 | Missing: 0 | Orphaned: 0 | Drifted: 0 after intentional data-refresh re-baseline.

## Next step
Commit/deploy the refreshed site when ready. If keeping strict agentic-ds discipline before public launch, run a fresh-session referee pass on `MODEL.md`, the claims register, and the refreshed pipeline.
