# STATUS — World Cup 2026 Pulse

> Regenerated 2026-06-12 (Opus session). Never hand-edit; underlying files win.

## Where we are
24 of 30 gates done. The model is built, honest, and verified; what remains is human sign-off, a fresh-session recompute, deploy, and a commit.
- [x] Brief + D01–D07 logged; spec FROZEN
- [x] Pipeline built + validated; environment pinned; drift baseline recorded
- [x] Modules 01–03 run; all four claims challenged; findings filed
- [x] C01 remediation resolved (D06 retry failed → D07 raw-Elo headline)
- [x] MODEL.md, GitHub Actions pipeline, Three.js site built + visually verified
- [x] C02/C03/C04 signed `supported`; raw-Elo headline ratified (Adir 2026-06-12)
- [x] Headline champion odds independently recomputed — agree within 0.43pp (2026-06-12)
- [x] Palette re-theme: is-this-the-end light/paper scheme applied as starting canvas (D08, 2026-06-12)
- ➜ [ ] Design the rest of the site together (Three.js, new palette)   ← current
- [ ] Then: commit pending work · deploy (GitHub Pages) · referee

## Since your last visit
WC26 Pulse — a free, legal, Three.js platform showing World Cup 2026 stats and Bayesian-updating predictions. Since the dashboard was last written, the entire back half got built: you chose remediation path (a), the Dixon-Coles retry (D06) **also failed** the backtest (pooled 0.9870, still 1/3 tournaments), so per its own pre-registered rule the model fell back (D07) to a **raw-Elo headline** with the Poisson layer demoted to "experimental" scorelines. C03/C04 were re-challenged under the new simulator and still pass. Then: MODEL.md (the honest model card), the GitHub Actions auto-refresh workflow, and the full Three.js site (a 3D champion-odds skyline + odds/matches/groups/scorers) — all built, run, and screenshot-verified. Pipeline is clean: 26 fresh, 0 stale, 0 drift. First commit landed; the latest site-build changes are still uncommitted.

## Needs you
- [x] ~~Sign C02, C03, C04 → `supported`~~ — signed by Adir 2026-06-12.
- [x] ~~Confirm raw-Elo baseline as headline~~ — ratified by Adir 2026-06-12 (logged on D07).
- [ ] Optional: glance at `04_analysis_modules/01_team_strength/figures/` (Elo top-16, goals-vs-Poisson) — the last unchecked data-inspection gate.

## Nudges
- **Uncommitted work:** the D06/D07 outputs, MODEL.md, and the frontend are modified-but-uncommitted in git (8 paths + `.claude/`, `docs/MODEL.md` untracked). Not lost, but not yet in the audit log either. Should be committed before deploy.
- Everything else is clean — no stale outputs, no unexplained drift, no unfiled results.

## Claims
| ID | Claim | Status | Last moved by |
|---|---|---|---|
| C01 | Model beats baselines | **not_supported** (closed) | agent 2026-06-12 |
| C02 | Probabilities calibrated | **supported** (signed Adir) | Adir 2026-06-12 |
| C03 | Simulation internally consistent | **supported** (signed Adir) | Adir 2026-06-12 |
| C04 | Champion odds seed-stable | **supported** (signed Adir) | Adir 2026-06-12 |

## Recent decisions & findings
- [D06] 2026-06-12: Dixon-Coles draw correction, one pre-registered retry of the backtest.
- [D07] 2026-06-12: retry failed → raw-Elo becomes the headline; Poisson demoted to "experimental".
- 2026-06-12 c01-dixon-coles-rerun: DC retry pooled log-loss 0.9870, still beats raw-Elo in only 1/3 → not_supported.
- 2026-06-12 c03-c04-rerun-under-d07: both re-challenged under the D07 simulator, both pass.

## Pipeline health
Fresh: 26 | Stale: 0 | Missing: 0 | Orphaned: 0 | Drifted: 0 (baseline 7 tables)
Current headline champion odds (seed 42, 20k sims): Spain 17.8% · Argentina 15.5% · France 9.3% · England 6.1% · Brazil 5.3%.

## Next step
Design the rest of the site together, in Three.js, on the new light/paper palette (D08). The palette is applied as a starting canvas; layout/components are the open creative work. The analysis is locked and verified — this is frontend only, no pipeline/model impact. After the design: commit pending work, deploy to GitHub Pages, referee pass.
