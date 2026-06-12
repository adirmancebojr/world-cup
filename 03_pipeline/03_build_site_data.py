"""Assemble docs/data/site_data.json for the static Three.js site.
Pure repackaging — every number comes from a module output (see source_trace)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data"

FIFA_CODES = {
    "Spain": "ESP", "Argentina": "ARG", "France": "FRA", "England": "ENG", "Brazil": "BRA",
    "Colombia": "COL", "Portugal": "POR", "Ecuador": "ECU", "Netherlands": "NED", "Germany": "GER",
    "Mexico": "MEX", "Canada": "CAN", "United States": "USA", "Croatia": "CRO", "Morocco": "MAR",
    "Japan": "JPN", "Uruguay": "URU", "Belgium": "BEL", "Austria": "AUT", "Australia": "AUS",
    "Norway": "NOR", "Senegal": "SEN", "Egypt": "EGY", "Iran": "IRN", "Algeria": "ALG",
    "Ghana": "GHA", "Panama": "PAN", "Paraguay": "PAR", "Qatar": "QAT", "Scotland": "SCO",
    "Turkey": "TUR", "Tunisia": "TUN", "Jordan": "JOR", "Haiti": "HAI", "Iraq": "IRQ",
    "South Korea": "KOR", "South Africa": "RSA", "Saudi Arabia": "KSA", "Switzerland": "SUI",
    "New Zealand": "NZL", "Czech Republic": "CZE", "Bosnia and Herzegovina": "BIH",
    "DR Congo": "COD", "Cape Verde": "CPV", "Ivory Coast": "CIV", "Curacao": "CUW",
    "Uzbekistan": "UZB", "Wales": "WAL", "Poland": "POL", "Italy": "ITA", "Denmark": "DEN",
    "Sweden": "SWE", "Ukraine": "UKR", "Slovakia": "SVK", "Slovenia": "SVN", "Serbia": "SRB",
    "Romania": "ROU", "Greece": "GRE", "Albania": "ALB", "Kosovo": "KOS", "Honduras": "HON",
    "Costa Rica": "CRC", "Jamaica": "JAM", "Chile": "CHI", "Peru": "PER", "Venezuela": "VEN",
    "Bolivia": "BOL", "Nigeria": "NGA", "Cameroon": "CMR", "Mali": "MLI", "Burkina Faso": "BFA",
    "Gabon": "GAB", "Benin": "BEN", "Libya": "LBY", "Oman": "OMA", "Bahrain": "BHR",
    "China PR": "CHN", "Indonesia": "IDN", "Kuwait": "KUW", "United Arab Emirates": "UAE",
}


def code(team: str) -> str:
    return FIFA_CODES.get(team, team.upper().replace(" ", "")[:3])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tp = pd.read_csv(ROOT / "04_analysis_modules/03_simulation/tables/team_probs.csv")
    mp = pd.read_csv(ROOT / "04_analysis_modules/03_simulation/tables/match_probs_group.csv")
    elo = pd.read_csv(ROOT / "04_analysis_modules/01_team_strength/tables/elo_wc48.csv").set_index("team")
    params = json.loads((ROOT / "04_analysis_modules/02_match_model/tables/model_params.json").read_text())
    wc = pd.read_csv(ROOT / "02_processed_data/wc2026_matches.csv")
    manifest = json.loads((ROOT / "01_raw_data/manifest.json").read_text())
    of = json.loads((ROOT / "01_raw_data/worldcup2026.json").read_text())
    name_map = dict(pd.read_csv(ROOT / "02_processed_data/name_map.csv").to_numpy())

    # standings from played group matches (display order: pts, gd, gf)
    stats = {t: dict(played=0, pts=0, gf=0, ga=0) for t in tp["team"]}
    played_rows = wc[wc["group"].notna() & wc["home_score"].notna()]
    for r in played_rows.itertuples():
        hs, as_ = int(r.home_score), int(r.away_score)
        for t, f, a in ((r.home_team, hs, as_), (r.away_team, as_, hs)):
            s = stats[t]
            s["played"] += 1
            s["gf"] += f
            s["ga"] += a
            s["pts"] += 3 if f > a else (1 if f == a else 0)

    teams = []
    for r in tp.itertuples():
        s = stats[r.team]
        teams.append(dict(
            name=r.team, code=code(r.team), group=r.group,
            elo=round(float(elo.loc[r.team, "rating"]), 1), elo_rank=int(elo.loc[r.team, "rank"]),
            p_r32=r.p_r32, p_r16=r.p_r16, p_qf=r.p_qf, p_sf=r.p_sf,
            p_final=r.p_final, p_champion=r.p_champion, p_group_win=r.p_group_win,
            **s))

    # group tables ordered for display
    groups: dict[str, list] = {}
    for t in sorted(teams, key=lambda t: (t["pts"], t["gf"] - t["ga"], t["gf"], t["p_group_win"]), reverse=True):
        groups.setdefault(t["group"], []).append(t["name"])

    matches = []
    for r in wc[wc["group"].notna()].sort_values("date").itertuples():
        m = dict(date=r.date, home=r.home_team, away=r.away_team, group=r.group, ground=r.ground)
        if pd.notna(r.home_score):
            m.update(status="played", hs=int(r.home_score), as_=int(r.away_score))
        else:
            p = mp[(mp["home"] == r.home_team) & (mp["away"] == r.away_team) & (mp["date"] == r.date)]
            m.update(status="upcoming")
            if len(p) == 1:
                p = p.iloc[0]
                m.update(p_home=round(p["p_home"], 4), p_draw=round(p["p_draw"], 4), p_away=round(p["p_away"], 4),
                         exp_scores=p["top_scores"])
        matches.append(m)

    # top scorers from openfootball goal records (public domain)
    scorers: dict[str, dict] = {}
    for om in of["matches"]:
        for side, team_key in (("goals1", "team1"), ("goals2", "team2")):
            for g in om.get(side) or []:
                if g.get("owngoal"):
                    continue
                k = g["name"]
                scorers.setdefault(k, dict(name=k, team=name_map.get(om[team_key], om[team_key]), goals=0))
                scorers[k]["goals"] += 1
    top_scorers = sorted(scorers.values(), key=lambda s: -s["goals"])[:15]

    data = dict(
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        data_pulled_utc=manifest["pulled_utc"],
        results_through=str(played_rows["date"].max()) if len(played_rows) else None,
        matches_played=int(len(played_rows)),
        headline_model=params["headline"], scoreline_model=params["scoreline_model"],
        n_sims=20000, sim_seed=42,
        teams=teams, groups=groups, matches=matches, scorers=top_scorers,
    )
    (OUT / "site_data.json").write_text(json.dumps(data, ensure_ascii=False))
    print(f"site_data.json: {len(teams)} teams, {len(matches)} matches, {data['matches_played']} played, "
          f"{len(top_scorers)} scorers, generated {data['generated_utc']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
