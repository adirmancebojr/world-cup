# Module 03: tournament simulation

- **Question:** Given current ratings and the frozen match model, what are each team's advancement and champion probabilities, and is the Monte Carlo machinery sound?
- **Inputs:** 04_analysis_modules/01_team_strength/tables/elo_current.csv, 04_analysis_modules/02_match_model/tables/model_params.json, 02_processed_data/wc2026_matches.csv, 02_processed_data/bracket.json
- **Claims tested:** C03 (internal consistency), C04 (seed stability).
- **Planned outputs:** team_probs.csv (headline run, seed 42, 20k sims), match_probs_group.csv (per-fixture W/D/L as of today), consistency_checks.csv, seed_stability.csv.
- **Validation checks:** stage-count identities (Σ R32=32 … Σ champion=1), per-team monotonicity, feasible third-place matching in every simulation.
- **Known limitations:** third-place slot allocation uses D05's deterministic matching (FIFA's exact combination table not in open data); knockout draws resolved by Elo-expectancy Bernoulli (no explicit ET/penalty model, per spec); group tie-breaks use points/GD/GF then random (head-to-head not implemented, logged in spec).
