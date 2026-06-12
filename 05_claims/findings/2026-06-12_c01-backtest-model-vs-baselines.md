---
date: 2026-06-12
updates: C01
result: not_supported
script: 04_analysis_modules/02_match_model/01_backtest.py
output: 04_analysis_modules/02_match_model/tables/backtest_metrics.csv
fresh: yes
---

The Elo→Poisson model does NOT beat the raw-Elo baseline on the pre-registered backtest. Pooled log-loss over 192 held-out matches (WC 2014/2018/2022, sequential prediction): model 0.9858, raw-Elo baseline 0.9831, uniform 1.0986. Per tournament the model beats raw-Elo only in WC2022 (1.0742 vs 1.0766), losing in WC2014 (0.9102 vs 0.9051) and WC2018 (0.9730 vs 0.9675) — 1 of 3, below the pre-registered ≥2 of 3 bar. The model clearly beats uniform everywhere. The margin to raw-Elo is small (+0.0027 nats pooled, ~0.3%), and the likely mechanism is known: independent Poisson under-prices draws (fit draw rates ~21–22% historically), which the draw-rate-anchored baseline gets for free. Per the frozen spec's ship threshold, the model cannot take the headline spot as-is; options (Dixon-Coles draw inflation via a new logged decision, or a raw-Elo-anchored hybrid) are with the owner.
