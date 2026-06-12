# Module 01: team strength priors (Elo)

- **Question:** What are each team's current strength ratings, recomputed from scratch per the frozen spec (Layer 1)?
- **Inputs:** 02_processed_data/matches.csv
- **Claims tested:** none directly (feeds C01–C04); visual sanity gate for the data section.
- **Planned outputs:** matches_elo.csv (pre-match ratings per row, leakage-free), elo_current.csv, elo_wc48.csv, figures (top-16 bar, goals distribution).
- **Validation checks:** ratings finite; mean rating conservation (Elo is zero-sum); WC-48 coverage complete.
- **Known limitations:** point estimates, no rating uncertainty (per spec, v1).
