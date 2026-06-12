# Data Dictionary

## results.csv — international match results (model backbone)
- **Source:** https://github.com/martj42/international_results (raw CSV, master branch). Same data as the Kaggle mirror but no auth needed.
- **License:** CC0-1.0 (verified via GitHub API, 2026-06-12).
- **Accessed:** 2026-06-12 (verification pull; pipeline snapshot pending). Repo pushed 2026-06-12 08:17 UTC.
- **Unit of observation:** one men's full international match.
- **Coverage:** 49,477 rows, 1872 → present, incl. WC 2026 fixtures as placeholder rows (`NA` scores) filled in within ~1 day of each match.
- **Key variables:** `date, home_team, away_team, home_score, away_score, tournament, city, country, neutral`.
- **Known anomalies:** score typo `"00"` (away_score, South Africa, 2026-06-11) → cleaning must coerce + log; `NA` scores mark unplayed fixtures; companion `shootouts.csv` exists in repo for penalty outcomes; team names need harmonization with openfootball (e.g., "United States" vs "USA").
- **Bears on:** Elo computation (Layer 1), β fit (Layer 2), backtests, 2026 results ingestion.

## worldcup.json — WC 2026 schedule, results, goalscorers (site backbone)
- **Source:** https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json
- **License:** public domain (openfootball).
- **Accessed:** 2026-06-12 (verification pull). June 11 results already present (~1 day latency).
- **Unit of observation:** one WC 2026 match (104 total).
- **Key fields:** `round, date, time, team1, team2, group, ground, score{ht,ft}, goals1[], goals2[]` (goalscorer name + minute).
- **Known anomalies:** `score`/`goals` keys absent until played; hand-maintained (wiki-style) so occasional lag or typos possible — cross-check against results.csv in pipeline validation.
- **Bears on:** near-live scores, scorer/standings stats, prediction trigger (a newly appeared result triggers a model re-run).
