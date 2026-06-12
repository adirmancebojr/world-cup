---
date: 2026-06-12
updates: C03
result: supported
script: 04_analysis_modules/03_simulation/01_simulate.py
output: 04_analysis_modules/03_simulation/tables/consistency_checks.csv
fresh: yes
---

The Monte Carlo machinery respects every structural identity of the 2026 format (headline run: 20,000 sims, seed 42). Stage-count sums are exact: Σ P(R32)=32, Σ P(R16)=16, Σ P(QF)=8, Σ P(SF)=4, Σ P(final)=2, Σ P(champion)=1. Per-team probabilities are monotone non-increasing across stages for all 48 teams. Every group's expected qualifier count lies in [2, 3] (2 guaranteed + at most one third). The D05 third-place matching found a feasible assignment in all 120,000 simulations across all runs (no infeasibility raised). Challenge passed; transition to `supported` proposed, awaiting owner signature.
