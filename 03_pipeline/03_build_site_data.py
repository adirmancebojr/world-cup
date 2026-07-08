"""Assemble docs/data/site_data.json for the static Three.js site.
Pure repackaging — every number comes from a module output (see source_trace)."""
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data"
sys.path.insert(0, str(ROOT / "03_pipeline"))
import wcmodel  # noqa: E402

HOSTS = {"United States", "Mexico", "Canada"}


def ko_odds(rh, ra, hadv, params):
    """Raw-Elo W/D/L (D07 headline) + experimental top scorelines for a drawn
    but unplayed knockout match."""
    pw, pdr, pl = wcmodel.raw_elo_baseline(rh, ra, hadv, params["draw_rate"])
    lam_h, lam_a = wcmodel.goal_rates(rh, ra, hadv, params["b0"], params["b1"])
    m = wcmodel.score_matrix(lam_h, lam_a)
    top = np.unravel_index(np.argsort(m, axis=None)[::-1][:3], m.shape)
    scores = "; ".join(f"{i}-{j} ({m[i, j]:.0%})" for i, j in zip(*top))
    return round(pw, 4), round(pdr, 4), round(pl, 4), scores

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


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def match_id(date: str, home: str, away: str) -> str:
    return f"{date}-{slug(home)}-{slug(away)}"


def parse_kickoff_utc(date: str, time_label: str) -> str | None:
    """Convert openfootball labels like "12:00 UTC-7" to a UTC ISO string."""
    match = re.fullmatch(r"(\d{1,2}):(\d{2}) UTC([+-]\d{1,2})(?::?(\d{2}))?", time_label or "")
    if not match:
        return None
    hour, minute, offset_hour, offset_minute = match.groups()
    offset = timedelta(hours=int(offset_hour), minutes=int(offset_minute or 0))
    local = datetime.fromisoformat(f"{date}T{int(hour):02d}:{minute}:00").replace(tzinfo=timezone(offset))
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def goal_event(goal: dict, team: str, side: str) -> dict:
    details = []
    if goal.get("penalty"):
        details.append("penalty")
    if goal.get("owngoal"):
        details.append("own goal")
    return {
        "minute": str(goal.get("minute", "")),
        "team": team,
        "side": side,
        "player": goal.get("name", ""),
        "type": "goal",
        "detail": ", ".join(details),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tp = pd.read_csv(ROOT / "04_analysis_modules/03_simulation/tables/team_probs.csv")
    try:  # empty once the group stage is complete (no remaining group fixtures)
        mp = pd.read_csv(ROOT / "04_analysis_modules/03_simulation/tables/match_probs_group.csv")
    except pd.errors.EmptyDataError:
        mp = pd.DataFrame(columns=["date", "home", "away", "group", "p_home", "p_draw", "p_away", "top_scores"])
    elo = pd.read_csv(ROOT / "04_analysis_modules/01_team_strength/tables/elo_wc48.csv").set_index("team")
    params = json.loads((ROOT / "04_analysis_modules/02_match_model/tables/model_params.json").read_text())
    wc = pd.read_csv(ROOT / "02_processed_data/wc2026_matches.csv")
    manifest = json.loads((ROOT / "01_raw_data/manifest.json").read_text())
    of = json.loads((ROOT / "01_raw_data/worldcup2026.json").read_text())
    name_map = dict(pd.read_csv(ROOT / "02_processed_data/name_map.csv").to_numpy())
    pred_path = ROOT / "04_analysis_modules/02_match_model/tables/predictions_2026.csv"
    pred_summary_path = ROOT / "04_analysis_modules/02_match_model/tables/prediction_summary.json"
    predictions = pd.read_csv(pred_path) if pred_path.exists() else pd.DataFrame()
    prediction_summary = json.loads(pred_summary_path.read_text()) if pred_summary_path.exists() else None
    prediction_lookup = {
        (r.date, r.home, r.away): r
        for r in predictions.itertuples(index=False)
    } if len(predictions) else {}
    fixture_meta = {}
    for om in of["matches"]:
        if not str(om.get("group", "")).startswith("Group"):
            continue
        teams_key = tuple(sorted((
            name_map.get(om.get("team1"), om.get("team1")),
            name_map.get(om.get("team2"), om.get("team2")),
        )))
        team1 = name_map.get(om.get("team1"), om.get("team1"))
        team2 = name_map.get(om.get("team2"), om.get("team2"))
        key = (
            om.get("date"),
            om.get("group"),
            teams_key,
        )
        kickoff_local = om.get("time")
        ft = (om.get("score") or {}).get("ft")
        ht = (om.get("score") or {}).get("ht")
        fixture_meta[key] = dict(
            source_home=team1,
            source_away=team2,
            kickoff_local=kickoff_local,
            kickoff_utc=parse_kickoff_utc(om.get("date"), kickoff_local) if kickoff_local else None,
            feed=dict(
                source="openfootball/worldcup.json",
                status="played" if ft else "scheduled",
                home_score=int(ft[0]) if ft else None,
                away_score=int(ft[1]) if ft else None,
                ht_home=int(ht[0]) if ht else None,
                ht_away=int(ht[1]) if ht else None,
                events=(
                    [goal_event(g, team1, "home") for g in (om.get("goals1") or [])]
                    + [goal_event(g, team2, "away") for g in (om.get("goals2") or [])]
                ),
            ),
        )

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
        m = dict(id=match_id(r.date, r.home_team, r.away_team), date=r.date,
                 home=r.home_team, away=r.away_team, group=r.group, ground=r.ground)
        meta = fixture_meta.get((r.date, r.group, tuple(sorted((r.home_team, r.away_team)))))
        if meta:
            feed = meta["feed"]
            if (r.home_team, r.away_team) != (meta["source_home"], meta["source_away"]):
                feed = {
                    **feed,
                    "home_score": feed["away_score"],
                    "away_score": feed["home_score"],
                    "ht_home": feed["ht_away"],
                    "ht_away": feed["ht_home"],
                    "events": [
                        {**e, "side": "home" if e["side"] == "away" else "away"}
                        for e in feed["events"]
                    ],
                }
            m.update(kickoff_local=meta["kickoff_local"], kickoff_utc=meta["kickoff_utc"], feed=feed)
        if pd.notna(r.home_score):
            m.update(status="played", hs=int(r.home_score), as_=int(r.away_score))
            pred = prediction_lookup.get((r.date, r.home_team, r.away_team))
            if pred:
                m["prediction"] = dict(
                    p_home=round(float(pred.p_home), 4),
                    p_draw=round(float(pred.p_draw), 4),
                    p_away=round(float(pred.p_away), 4),
                    pred_outcome=pred.pred_outcome,
                    actual_outcome=pred.actual_outcome,
                    outcome_hit=bool(pred.outcome_hit),
                    top_score=pred.top_score,
                    top_score_prob=round(float(pred.top_score_prob), 4) if hasattr(pred, "top_score_prob") else None,
                    actual_score=pred.actual_score,
                    score_hit=bool(pred.score_hit),
                    prob_actual=round(float(pred.prob_actual), 4),
                    logloss=round(float(pred.logloss), 4),
                )
        else:
            p = mp[(mp["home"] == r.home_team) & (mp["away"] == r.away_team) & (mp["date"] == r.date)]
            m.update(status="upcoming")
            if len(p) == 1:
                p = p.iloc[0]
                m.update(p_home=round(p["p_home"], 4), p_draw=round(p["p_draw"], 4), p_away=round(p["p_away"], 4),
                         exp_scores=p["top_scores"])
        matches.append(m)

    # ---- knockout bracket: resolve teams from played results ----
    so_path = ROOT / "02_processed_data/wc2026_shootouts.csv"
    so = pd.read_csv(so_path) if so_path.exists() else pd.DataFrame(columns=["home_team", "away_team", "winner"])
    so_winner = {frozenset((r.home_team, r.away_team)): r.winner for r in so.itertuples()}
    team_names = {t["name"] for t in teams}
    ground_country = json.loads((ROOT / "02_processed_data/bracket.json").read_text()).get("ground_country", {})

    raw = {}
    for om in sorted((x for x in of["matches"] if not str(x.get("group", "")).startswith("Group")), key=lambda x: x["num"]):
        ft = (om.get("score") or {}).get("ft")
        raw[om["num"]] = dict(
            num=om["num"], round=om["round"], ground=om.get("ground"), date=om.get("date"),
            team1=name_map.get(om["team1"], om["team1"]), team2=name_map.get(om["team2"], om["team2"]),
            kickoff_local=om.get("time"),
            kickoff_utc=parse_kickoff_utc(om.get("date"), om.get("time")) if om.get("time") else None,
            hs=int(ft[0]) if ft else None, as_=int(ft[1]) if ft else None,
        )

    def ko_winner(e):
        if e is None or e["hs"] is None:
            return None
        if e["hs"] > e["as_"]:
            return e["team1"]
        if e["as_"] > e["hs"]:
            return e["team2"]
        return so_winner.get(frozenset((e["team1"], e["team2"])))

    def ko_loser(e):
        w = ko_winner(e)
        return None if not w else (e["team2"] if w == e["team1"] else e["team1"])

    for _ in range(6):  # propagate W##/L## references through the rounds
        for e in raw.values():
            for side in ("team1", "team2"):
                c = e[side]
                if not isinstance(c, str) or c in team_names:
                    continue
                if c[:1] in ("W", "L") and c[1:].isdigit() and int(c[1:]) in raw:
                    r = ko_winner(raw[int(c[1:])]) if c[:1] == "W" else ko_loser(raw[int(c[1:])])
                    if r:
                        e[side] = r

    def slot_label(c):
        if isinstance(c, str) and c[:1] in ("W", "L") and c[1:].isdigit():
            return ("Winner" if c[0] == "W" else "Loser") + " " + c[1:]
        return c

    def pred_block(date, home, away):
        for h, a, flip in ((home, away, False), (away, home, True)):
            p = prediction_lookup.get((date, h, a))
            if p is None:
                continue
            ts = p.top_score.split("-") if isinstance(p.top_score, str) and "-" in p.top_score else None
            asc = p.actual_score.split("-") if isinstance(p.actual_score, str) and "-" in p.actual_score else None
            swap = {"H": "A", "A": "H", "D": "D"}
            return dict(
                p_home=round(float(p.p_away if flip else p.p_home), 4),
                p_draw=round(float(p.p_draw), 4),
                p_away=round(float(p.p_home if flip else p.p_away), 4),
                pred_outcome=swap[p.pred_outcome] if flip else p.pred_outcome,
                actual_outcome=swap[p.actual_outcome] if flip else p.actual_outcome,
                outcome_hit=bool(p.outcome_hit),
                top_score=f"{ts[1]}-{ts[0]}" if (flip and ts) else p.top_score,
                top_score_prob=round(float(p.top_score_prob), 4) if hasattr(p, "top_score_prob") else None,
                actual_score=f"{asc[1]}-{asc[0]}" if (flip and asc) else p.actual_score,
                score_hit=bool(p.score_hit),
                prob_actual=round(float(p.prob_actual), 4), logloss=round(float(p.logloss), 4),
            )
        return None

    bracket = []
    ko_played = 0
    for num in sorted(raw):
        e = raw[num]
        winner = ko_winner(e)
        bracket.append(dict(
            num=num, round=e["round"], date=e["date"], ground=e["ground"],
            team1=slot_label(e["team1"]), team2=slot_label(e["team2"]),
            code1=code(e["team1"]) if e["team1"] in team_names else None,
            code2=code(e["team2"]) if e["team2"] in team_names else None,
            hs=e["hs"], as_=e["as_"], winner=winner, winner_code=code(winner) if winner else None,
        ))
        if e["team1"] in team_names and e["team2"] in team_names:
            km = dict(id=match_id(e["date"], e["team1"], e["team2"]), date=e["date"],
                      home=e["team1"], away=e["team2"], round=e["round"], ground=e["ground"],
                      kickoff_local=e["kickoff_local"], kickoff_utc=e["kickoff_utc"])
            if e["hs"] is not None:
                km.update(status="played", hs=e["hs"], as_=e["as_"])
                ko_played += 1
                pb = pred_block(e["date"], e["team1"], e["team2"])
                if pb:
                    km["prediction"] = pb
            else:
                km.update(status="upcoming")
                if e["team1"] in elo.index and e["team2"] in elo.index:
                    rh, ra = float(elo.loc[e["team1"], "rating"]), float(elo.loc[e["team2"], "rating"])
                    g = e["ground"]
                    hadv = (wcmodel.HOME_ADV if (e["team1"] in HOSTS and ground_country.get(g) == e["team1"]) else 0.0) \
                        - (wcmodel.HOME_ADV if (e["team2"] in HOSTS and ground_country.get(g) == e["team2"]) else 0.0)
                    pw, pdr, pl, scores = ko_odds(rh, ra, hadv, params)
                    km.update(p_home=pw, p_draw=pdr, p_away=pl, exp_scores=scores)
            matches.append(km)

    # results/counts across the whole tournament (group + knockout)
    ko_dates = [e["date"] for e in raw.values() if e["hs"] is not None]
    all_dates = list(played_rows["date"]) + ko_dates
    results_through_all = max(all_dates) if all_dates else None
    matches_played_all = int(len(played_rows)) + ko_played

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
        results_through=results_through_all,
        matches_played=matches_played_all,
        group_matches_played=int(len(played_rows)),
        stage="knockout" if len(mp) == 0 and matches_played_all >= 72 else "group",
        headline_model=params["headline"], scoreline_model=params["scoreline_model"],
        n_sims=20000, sim_seed=42,
        prediction_summary=prediction_summary,
        teams=teams, groups=groups, matches=matches, bracket=bracket, scorers=top_scorers,
    )
    (OUT / "site_data.json").write_text(json.dumps(data, ensure_ascii=False))
    (ROOT / "docs" / "MODEL.md").write_text((ROOT / "MODEL.md").read_text())
    print(f"site_data.json: {len(teams)} teams, {len(matches)} matches, {data['matches_played']} played, "
          f"{len(top_scorers)} scorers, generated {data['generated_utc']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
