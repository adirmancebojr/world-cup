---
date: 2026-06-12
updates: C03, C04
result: supported
script: 04_analysis_modules/03_simulation/02_recompute_independent.py
output: 04_analysis_modules/03_simulation/tables/recompute_comparison.csv
fresh: yes
---

The headline champion odds survive an independent re-derivation (the agentic-ds challenge gate for headline numbers). A second simulator (`02_recompute_independent.py`) was written from the frozen spec + decision log, sharing NO code with `wcmodel.py` or `01_simulate.py` — every formula (Elo update, raw-Elo D07 outcomes, conditional Poisson scoreline, the bracket, and the D05 third-place feasibility matching) re-implemented from scratch, reading only `02_processed_data/`, run at 20,000 sims with a different RNG seed (100 vs production's 42). Result: the two implementations agree within Monte Carlo error. Max champion-probability difference across all 48 teams = 0.0043 (0.43pp, Argentina/Portugal), versus a 4×SE tolerance band of 0.0153 (1.53pp) for the top teams; round-of-16 reach probabilities also align (e.g. Spain 0.7204 vs 0.7196). This independently confirms the production headline (Spain 17.8%, Argentina 15.5%, France 9.3%, England 6.1%, Brazil 5.3%) is not an artifact of the production simulator's code.
