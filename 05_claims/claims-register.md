# Claims Register

Statuses: proposed → testing → supported | not_supported | complicated.
A claim cannot be `supported` until its challenge passes and a human signs off.

## C01: Model beats baselines
- **Status:** not_supported
- **Claim:** The Elo-Poisson model's W/D/L predictions beat the uniform and raw-Elo baselines on log-loss.
- **Metric & population:** pooled log-loss over all 192 backtest matches (WC 2014/2018/2022), sequential prediction.
- **Challenge:** must also beat raw-Elo in ≥2 of the 3 tournaments individually (guards against one lucky tournament).
- **Scripts:** 04_analysis_modules/02_match_model/01_backtest.py
- **Findings:** findings/2026-06-12_c01-backtest-model-vs-baselines.md
- **History:** 2026-06-12 proposed (pre-registered in spec before any fitting); 2026-06-12 challenge run → not_supported (pooled log-loss 0.9858 vs raw-Elo 0.9831; beats raw-Elo in 1/3 tournaments). Remediation options awaiting owner decision; 2026-06-12 owner chose (a) → D06 Dixon-Coles re-run also failed (pooled 0.9870; 1/3 tournaments) → D06 rule triggered fallback (b): raw-Elo headline, Poisson demoted to experimental (D07). C01 closed as not_supported.

## C02: Probabilities are calibrated
- **Status:** testing (challenge PASSED — `supported` proposed, awaiting owner signature)
- **Claim:** Predicted outcome probabilities match observed frequencies.
- **Metric & population:** reliability curve, 10 bins, pooled backtest predictions.
- **Challenge:** max calibration gap < 10pp in bins with n ≥ 30.
- **Scripts:** 04_analysis_modules/02_match_model/01_backtest.py
- **Findings:** findings/2026-06-12_c02-calibration.md
- **History:** 2026-06-12 proposed; 2026-06-12 challenge passed (max gap 6.9pp)

## C03: Tournament simulation is internally consistent
- **Status:** testing (challenge PASSED — `supported` proposed, awaiting owner signature)
- **Claim:** Monte Carlo advancement/champion probabilities respect all structural identities of the 2026 format.
- **Metric & population:** Σ P(champion)=1; per-group qualifier expectations; per-team round monotonicity; 20k sims.
- **Challenge:** every identity holds within Monte Carlo error.
- **Scripts:** 04_analysis_modules/03_simulation/01_simulate.py
- **Findings:** findings/2026-06-12_c03-simulation-consistency.md
- **History:** 2026-06-12 proposed; 2026-06-12 challenge passed (all identities exact, monotone); 2026-06-12 re-challenged and passed under D07 simulator (findings/2026-06-12_c03-c04-rerun-under-d07.md)

## C04: Outputs are seed-stable
- **Status:** testing (challenge PASSED — `supported` proposed, awaiting owner signature)
- **Claim:** Published champion odds do not depend materially on the random seed.
- **Metric & population:** max absolute spread of any team's champion probability across 5 seeds × 20k sims.
- **Challenge:** spread < 1.5pp for every team.
- **Scripts:** 04_analysis_modules/03_simulation/01_simulate.py
- **Findings:** findings/2026-06-12_c04-seed-stability.md
- **History:** 2026-06-12 proposed; 2026-06-12 challenge passed (max spread 0.71pp); 2026-06-12 re-challenged and passed under D07 simulator (max spread 0.70pp on final regeneration)
