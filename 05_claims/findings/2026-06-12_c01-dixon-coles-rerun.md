---
date: 2026-06-12
updates: C01
result: not_supported
script: 04_analysis_modules/02_match_model/01_backtest.py
output: 04_analysis_modules/02_match_model/tables/backtest_metrics.csv
fresh: yes
---

The D06 Dixon-Coles re-run (the single pre-registered fix) also fails C01 — and slightly underperforms the plain Poisson: pooled log-loss model_dc 0.9870 vs poisson_iid 0.9858 vs raw-Elo 0.9831 (uniform 1.0986); the DC model beats raw-Elo in only WC2022 (1.0752 vs 1.0766), same 1 of 3 as before. The fitted draw-inflation parameter is small in international data (ρ between −0.016 and −0.034 across fit windows), so the correction barely moves draw probabilities and costs a sliver of likelihood out of sample. Calibration remains fine (max gap 7.3pp < 10pp). Per D06's pre-registered rule, the fallback is adopted: raw-Elo probabilities become the headline match odds; the Poisson layer is demoted to "experimental" and retained for scorelines. No further model variants will be tried without a new logged decision.
