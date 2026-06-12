---
date: 2026-06-12
updates: C04
result: supported
script: 04_analysis_modules/03_simulation/01_simulate.py
output: 04_analysis_modules/03_simulation/tables/seed_stability.csv
fresh: yes
---

Published champion odds are stable to the random seed. Across 5 independent seeds × 20,000 simulations, the maximum absolute spread in any team's champion probability is 0.0071 (0.71pp, Argentina — the team with the second-highest odds, where Monte Carlo noise is largest in absolute terms), well inside the pre-registered 1.5pp band. All 48 teams are within the band. Challenge passed; transition to `supported` proposed, awaiting owner signature.
