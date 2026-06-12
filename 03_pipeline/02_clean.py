"""Clean raw data into model-ready tables, with embedded validation.

Outputs (02_processed_data/):
  matches.csv         all played internationals, cleaned, chronological
  wc2026_matches.csv  the 104 WC 2026 fixtures/results + group labels
  name_map.csv        openfootball name -> results.csv canonical name
  bracket.json        groups, R32 slots (incl. third-place constraints), KO graph
  cleaning_log.txt    every coercion/anomaly, for the audit trail
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "01_raw_data"
OUT = ROOT / "02_processed_data"

WC_START, WC_END = "2026-06-11", "2026-07-19"

GROUND_COUNTRY = {
    "Mexico City": "Mexico", "Guadalajara (Zapopan)": "Mexico", "Monterrey (Guadalupe)": "Mexico",
    "Toronto": "Canada", "Vancouver": "Canada",
}  # every other 2026 ground is in the United States

log_lines: list[str] = []


def log(msg: str) -> None:
    log_lines.append(msg)
    print(msg)


def clean_scores(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("home_score", "away_score"):
        raw = df[col].astype("string")
        odd = raw.dropna()[~raw.dropna().str.fullmatch(r"\d+")]
        for i, v in odd.items():
            log(f"anomaly: row {i} {df.loc[i, 'date']} {df.loc[i, 'home_team']}-{df.loc[i, 'away_team']} {col}={v!r} -> coerced")
        lead0 = raw.dropna()[raw.dropna().str.fullmatch(r"0\d+")]
        for i, v in lead0.items():
            log(f"anomaly: leading-zero score {v!r} at row {i} ({df.loc[i, 'date']} {df.loc[i, 'home_team']} v {df.loc[i, 'away_team']}) -> {int(v)}")
        df[col] = pd.to_numeric(raw, errors="coerce")
    return df


KNOWN_ALIASES = {
    "USA": "United States",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "Czechia": "Czech Republic",
    "Curaçao": "Curacao",
}


def build_name_map(of_teams: set[str], rs_teams: set[str]) -> dict[str, str]:
    """Map openfootball names to results.csv names: exact match, then known
    aliases. The map is independently validated downstream by requiring every
    openfootball fixture to match exactly one results.csv row (±1 day)."""
    mapping = {t: t for t in of_teams if t in rs_teams}
    for t in sorted(of_teams - set(mapping)):
        alias = KNOWN_ALIASES.get(t)
        if alias and alias in rs_teams:
            mapping[t] = alias
            log(f"name map: openfootball {t!r} -> results {alias!r}")
    leftover = of_teams - set(mapping)
    assert not leftover, f"unmapped openfootball teams (extend KNOWN_ALIASES): {leftover}"
    return mapping


def main() -> int:
    OUT.mkdir(exist_ok=True)
    df = pd.read_csv(RAW / "results.csv", dtype={"home_score": "string", "away_score": "string"})
    df["neutral"] = df["neutral"].astype(bool)
    df = clean_scores(df)

    played = df.dropna(subset=["home_score", "away_score"]).copy()
    played[["home_score", "away_score"]] = played[["home_score", "away_score"]].astype(int)
    played = played.sort_values("date", kind="stable").reset_index(drop=True)
    assert (played["home_score"] >= 0).all() and (played["home_score"] <= 31).all(), "score out of range"
    log(f"played matches: {len(played):,} ({played['date'].min()} -> {played['date'].max()})")

    # --- WC 2026 fixtures + group labels from openfootball ---
    of = json.loads((RAW / "worldcup2026.json").read_text())
    of_matches = of["matches"]
    assert len(of_matches) == 104, f"expected 104 openfootball matches, got {len(of_matches)}"
    # results.csv pre-loads only the 72 group fixtures; knockout rows appear
    # once pairings are known (verified 2026-06-12). Bracket comes from openfootball.
    wc_rows = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= WC_START) & (df["date"] <= WC_END)].copy()
    assert 72 <= len(wc_rows) <= 104, f"expected 72-104 results.csv WC fixtures, got {len(wc_rows)}"

    of_group = [m for m in of_matches if str(m.get("group", "")).startswith("Group")]
    of_teams = {m[k] for m in of_group for k in ("team1", "team2")}
    rs_teams = set(wc_rows["home_team"]) | set(wc_rows["away_team"])
    assert len(of_teams) == 48, f"expected 48 teams, got {len(of_teams)}"
    mapping = build_name_map(of_teams, rs_teams)

    # validate mapping fixture-by-fixture (±1 day for timezone differences)
    # and attach group / match num / ground onto results.csv rows
    wc_dates = pd.to_datetime(wc_rows["date"])
    wc_rows["group"], wc_rows["match_num"], wc_rows["ground"] = None, None, None
    mismatches = 0
    for m in of_group:
        d = pd.Timestamp(m["date"])
        h, a = mapping[m["team1"]], mapping[m["team2"]]
        near = (wc_dates - d).abs() <= pd.Timedelta(days=1)
        hit = wc_rows[(wc_rows["home_team"] == h) & (wc_rows["away_team"] == a) & near]
        flipped = False
        if len(hit) != 1:  # sources may disagree on home/away designation
            hit = wc_rows[(wc_rows["home_team"] == a) & (wc_rows["away_team"] == h) & near]
            flipped = True
        assert len(hit) == 1, f"fixture {m['date']} {m['team1']} v {m['team2']} -> {h} v {a}: {len(hit)} results.csv rows (name map wrong?)"
        i = hit.index[0]
        wc_rows.loc[i, ["group", "match_num", "ground"]] = (m["group"], m.get("num"), m["ground"])
        # cross-source score validation on played matches
        ft = (m.get("score") or {}).get("ft")
        if ft and not pd.isna(wc_rows.loc[i, "home_score"]):
            if flipped:
                ft = ft[::-1]
            rs_ft = [int(wc_rows.loc[i, "home_score"]), int(wc_rows.loc[i, "away_score"])]
            if rs_ft != ft:
                mismatches += 1
                log(f"SCORE MISMATCH {m['date']} {m['team1']}-{m['team2']}: openfootball {ft} vs results.csv {rs_ft}")
    assert wc_rows["group"].notna().sum() == 72, "not all 72 group fixtures matched"
    log(f"cross-source score mismatches: {mismatches}")
    assert mismatches == 0, "sources disagree on a played score — investigate before modeling"

    # --- bracket.json ---
    groups: dict[str, list] = {}
    for m in of_matches:
        g = str(m.get("group", ""))
        if g.startswith("Group"):
            for t in (mapping[m["team1"]], mapping[m["team2"]]):
                if t not in groups.setdefault(g[-1], []):
                    groups[g[-1]].append(t)
    assert sorted(groups) == list("ABCDEFGHIJKL") and all(len(v) == 4 for v in groups.values())

    ko = [m for m in of_matches if not str(m.get("group", "")).startswith("Group")]
    bracket = {
        "groups": groups,
        "ground_country": {m["ground"]: GROUND_COUNTRY.get(m["ground"], "United States") for m in of_matches},
        "knockout": [
            {"num": m["num"], "round": m["round"], "team1": m["team1"], "team2": m["team2"], "ground": m["ground"], "date": m["date"]}
            for m in sorted(ko, key=lambda x: x["num"])
        ],
    }

    # shootout winners for played knockout draws (knockouts begin 2026-06-28)
    so = pd.read_csv(RAW / "shootouts.csv")
    so[(so["date"] >= WC_START) & (so["date"] <= WC_END)].to_csv(OUT / "wc2026_shootouts.csv", index=False)

    played.to_csv(OUT / "matches.csv", index=False)
    wc_rows.sort_values(["date", "match_num"]).to_csv(OUT / "wc2026_matches.csv", index=False)
    pd.DataFrame(sorted(mapping.items()), columns=["openfootball", "canonical"]).to_csv(OUT / "name_map.csv", index=False)
    (OUT / "bracket.json").write_text(json.dumps(bracket, indent=2, ensure_ascii=False))
    (OUT / "cleaning_log.txt").write_text("\n".join(log_lines) + "\n")
    log(f"wrote {OUT / 'matches.csv'}, wc2026_matches.csv, name_map.csv, bracket.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
