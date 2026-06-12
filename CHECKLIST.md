# Checklist — World Cup 2026 Pulse   (mode: full)

## Frame & spec
- [x] • Data availability researched and filed (A) — 00_admin/data-availability-research.md, 2026-06-12
- [x] • Brief signed: question, audience, deliverable, scope + D01–D04 decisions (H signed 2026-06-12; D03 amended: no play diagrams)
- [x] • Spec drafted: model math, metric definitions, training filters, baselines, eval metric, split design, leakage rules, a challenge per claim (A, 2026-06-12)
- [x] • Spec FROZEN (H signed 2026-06-12: "freeze it")

## Data
- [x] • Backbone sources verified by live pull: openfootball 2026 (June 11 results present) + martj42 results.csv (CC0, 49,477 rows, ~1-day result latency) (A, 2026-06-12)
- [x] • Data dictionary written for verified sources (A, 2026-06-12)
- [x] • Environment pinned: requirements.txt exact pins, venv at ~/.venvs/world-cup, snapshot manifest with sha256 (A, 2026-06-12)
- [x] • Raw data write-discipline: 01_raw_data/ written only by 03_pipeline/01_fetch_raw.py (snapshots + checksum manifest); never hand-edited (A, 2026-06-12)
- [x] • Pipeline scripts (fetch → clean → model inputs) with embedded validation checks; caught 1 score typo + 0 cross-source mismatches (A, 2026-06-12)
- [x] • Drift baseline recorded: check_drift.py --update, 6 tables fingerprinted (A, 2026-06-12)
- [ ] • Raw data inspected visually: figures ready (01_team_strength/figures/), awaiting human eyes (B)

## Analysis modules
### Module 01: team strength priors
- [x] README: question, inputs, claims tested (A, 2026-06-12)
- [x] • Numbered scripts produce Elo/strength tables; source_trace.csv current (A, 2026-06-12)
- [x] • Findings filed (A — no direct claims; feeds C01–C04)
### Module 02: match outcome model + Bayesian updating
- [x] README (A, 2026-06-12)
- [x] • Numbered scripts: fit, update rule, calibration on held-out tournaments (A, 2026-06-12)
- [x] • Findings filed: C01 not_supported, C02 challenge passed (A, 2026-06-12)
### Module 03: tournament simulation
- [x] README (A, 2026-06-12)
- [x] • Numbered scripts: Monte Carlo bracket sim, advancement/champion tables (A, 2026-06-12)
- [x] • Findings filed: C03 + C04 challenges passed (A, 2026-06-12)

## Challenge
- [x] • Every register claim has run its challenge — evidence ladder walked (B, 2026-06-12)
- [ ] • Headline numbers (champion odds) independently recomputed in a fresh session (A)
- [ ] • Claim statuses signed: C02/C03/C04 → supported; C01 remediation path chosen (H)

## Build & deliver (platform)
- [ ] MODEL.md model card written from the spec + findings (A)
- [ ] GitHub Actions pipeline: scheduled fetch → model update → commit JSON (A)
- [ ] Three.js frontend: stats views, near-live scoreboard, prediction dashboards (B) — no play diagrams (D03)
- [ ] Attribution page (openfootball, martj42 CC0, Wikipedia CC BY-SA if used, football-data.org if used) (A)
- [ ] Deployed to free host (GitHub Pages / Cloudflare Pages) (B)
- [ ] • Mechanical audit passed: trace, map, regenerate, verify (A)
- [ ] • Referee run in a fresh session on MODEL.md + pipeline (B)
- [ ] • Final site inspected visually (B)
