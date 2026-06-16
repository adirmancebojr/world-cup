# Module 02: match outcome model + backtests

- **Question:** Does the Elo→Poisson model (frozen spec Layer 2) produce better-calibrated W/D/L probabilities than the baselines on held-out World Cups?
- **Inputs:** 02_processed_data/matches_elo.csv
- **Claims tested:** C01 (beats baselines), C02 (calibration).
- **Planned metrics:** log-loss (primary), RPS (secondary), reliability curve (10 bins, n≥30).
- **Planned outputs:** backtest_metrics.csv, backtest_predictions.csv, calibration.csv + calibration.png, model_params.json (production β for 2026), predictions_2026.csv + prediction_summary.json (completed-match tracking).
- **Validation checks:** MLE convergence; probability simplex sums to 1; observed-outcome counts match 64 matches per tournament.
- **Known limitations:** knockout scores in results.csv include extra time, so a 120' draw counts as a draw vs our 90' probabilities; β frozen during tournaments per spec.
