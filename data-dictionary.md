# Data Dictionary

## results.csv — international match results (model backbone)
- **Source:** https://github.com/martj42/international_results (raw CSV, master branch). Same data as the Kaggle mirror but no auth needed.
- **License:** CC0-1.0 (verified via GitHub API, 2026-06-12).
- **Accessed:** 2026-06-12 (verification pull; pipeline snapshot pending). Repo pushed 2026-06-12 08:17 UTC.
- **Unit of observation:** one men's full international match.
- **Coverage:** 49,477 rows, 1872 → present, incl. WC 2026 fixtures as placeholder rows (`NA` scores) usually filled in within ~1 day of each match.
- **Key variables:** `date, home_team, away_team, home_score, away_score, tournament, city, country, neutral`.
- **Known anomalies:** score typo `"00"` (away_score, South Africa, 2026-06-11) → cleaning must coerce + log; `NA` scores mark unplayed fixtures; companion `shootouts.csv` exists in repo for penalty outcomes; team names need harmonization with openfootball (e.g., "United States" vs "USA").
- **Bears on:** Elo computation (Layer 1), β fit (Layer 2), backtests, 2026 results ingestion.

## worldcup.json — WC 2026 schedule, results, goalscorers (site backbone)
- **Source:** https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json
- **License:** public domain (openfootball).
- **Accessed:** 2026-06-12 (verification pull). June 11 results already present (~1 day latency).
- **Unit of observation:** one WC 2026 match (104 total).
- **Key fields:** `round, date, time, team1, team2, group, ground, score{ht,ft}, goals1[], goals2[]` (goalscorer name + minute).
- **Known anomalies:** `score`/`goals` keys absent until played; hand-maintained (wiki-style) so occasional lag or typos possible — cross-check against results.csv in pipeline validation when both sources have a score.
- **Bears on:** match scores, scorer/standings stats, and prediction refreshes. When `results.csv` lags but openfootball has a WC 2026 full-time score, the cleaner can fill that missing WC score from openfootball and logs the fill.

## countries-110m.geojson — world country polygons (frontend only)
- **Source:** Natural Earth via github.com/nvkelso/natural-earth-vector (ne_110m_admin_0_countries).
- **License:** public domain (Natural Earth) — no attribution required; credited on the site as courtesy.
- **Accessed:** 2026-06-12. Size 819 KB, 177 features.
- **Used for:** the hero globe ONLY (country outlines + extruded participant shapes). NOT a model input — bears on no claim.
- **Known limitations (handled in docs/main.js):** 110m is coarse/low-detail; UK is one polygon (assigned to England; Scotland → pin marker); Cape Verde and Curaçao absent at 110m → pin markers; team↔NE name matching via an alias table.

## docs/flags/4x3/*.svg — country flag images (frontend only)
- **Source:** lipis/flag-icons (github.com/lipis/flag-icons), 4x3 SVG set; 48 files vendored (one per WC team).
- **License:** MIT (docs/flags/LICENSE included; credited in site footer). Flag designs themselves are public domain.
- **Accessed:** 2026-06-13.
- **Used for:** skinning the extruded countries on the hero globe (real flags replaced hand-drawn canvas flags). NOT a model input — bears on no claim.
- **Mapping:** FIFA code → flag file via FLAG_CODE in docs/main.js (ISO 3166-1 alpha-2; England=gb-eng, Scotland=gb-sct). `drawFlag` (hand-drawn) retained as the fallback if an SVG fails to load.
