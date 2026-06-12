# STATUS — World Cup 2026 Pulse

> Regenerated 2026-06-12 16:30. Never hand-edit; underlying files win.

## Where we are
17 of 26 gates done.
- [x] Brief + D01–D05 signed/logged; spec FROZEN (2026-06-12)
- [x] Pipeline built + validated; drift baseline recorded; environment pinned
- [x] Modules 01–03 run; all four claims challenged; findings filed
- ➜ [ ] C01 remediation decision + sign C02/C03/C04 (H)        ← current
- [ ] Fresh-session recomputation of headline numbers (A)
- [ ] Build & deliver: MODEL.md, GitHub Actions pipeline, Three.js site, deploy

## Since your last visit
You froze the spec; I built and ran everything. The honest headline: **the model failed its own pre-registered test (C01)** — pooled backtest log-loss 0.9858 vs the raw-Elo baseline's 0.9831, beating it in only 1 of 3 held-out World Cups (2022 yes, 2014/2018 no). It clearly beats uniform, and its probabilities are well calibrated (C02 passed, max gap 6.9pp). The simulator machinery is sound: structural identities exact (C03) and champion odds stable across seeds, max 0.71pp (C04). Current odds from the (caveated) model: Spain 20.8%, Argentina 17.2%, France 9.3%. Per the frozen spec, this model cannot take the headline spot as-is.

## Needs you
- [ ] **C01 remediation — pick a path (this gates everything downstream):**
  - **(a) Recommended — D06: one pre-registered fix.** The known mechanism is that independent Poisson under-prices draws. Log a decision adopting a Dixon-Coles-style draw adjustment, re-run the same backtest ONCE. Adopt if it then passes C01; fall back to (b) if not. Transparent: one change, named in advance, one shot.
  - **(b) Ship the baseline as headline.** Raw-Elo probabilities (which won the backtest) become the headline match odds; the Poisson layer still powers scorelines/simulation, labeled "experimental" per the spec's demotion rule.
- [ ] Sign C02, C03, C04 → `supported` (challenges passed; details in 05_claims/findings/).
- [ ] Glance at the two sanity figures: 04_analysis_modules/01_team_strength/figures/ (Elo top-16, goals-vs-Poisson).

## Nudges
None — pipeline fully green (23 fresh / 0 stale / 0 missing / 0 orphaned; drift baseline recorded).

## Claims
| ID | Claim | Status | Last moved by |
|---|---|---|---|
| C01 | Model beats baselines | **not_supported** | agent 2026-06-12 |
| C02 | Probabilities calibrated | testing → supported proposed | agent 2026-06-12 |
| C03 | Simulation consistent | testing → supported proposed | agent 2026-06-12 |
| C04 | Seed-stable | testing → supported proposed | agent 2026-06-12 |

## Recent decisions & findings
- [D05] 2026-06-12: third-place R32 allocation via deterministic feasibility matching.
- 2026-06-12 c01 finding: model loses to raw-Elo by 0.0027 nats pooled — not_supported.
- 2026-06-12 c02/c03/c04 findings: calibration, consistency, stability all passed.

## Pipeline health
Fresh: 23 | Stale: 0 | Missing: 0 | Orphaned: 0 | Drifted: 0 (baseline 6 tables, 2026-06-12)

## Next step
You choose the C01 path — say "go with (a)" (or (b)), and whether C02–C04 are signed.
