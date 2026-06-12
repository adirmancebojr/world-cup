---
date: 2026-06-12
updates: C02
result: supported
script: 04_analysis_modules/02_match_model/01_backtest.py
output: 04_analysis_modules/02_match_model/tables/calibration.csv
fresh: yes
---

The model's outcome probabilities are well calibrated on the pooled backtests (WC 2014/2018/2022; 192 matches × 3 outcome classes). Reliability curve with 10 equal-width bins, keeping bins with n ≥ 30: six bins qualify (predicted probabilities 0.1–0.7), and the maximum |predicted − observed| gap is 0.069 — inside the pre-registered 0.10 band. Largest deviations: bin 0.5–0.6 (predicted 0.539 vs observed 0.608) and bin 0.4–0.5 (0.451 vs 0.509), i.e., the model is slightly underconfident on favorites, consistent with the draw over-/under-pricing noted in the C01 finding. Challenge passed; transition to `supported` proposed, awaiting owner signature.
