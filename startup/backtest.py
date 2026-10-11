#!/usr/bin/env python3
"""
Site-selection backtest on real ClinicalTrials.gov data.

The test, in one line:
  Take past trials (multiple myeloma; asthma before), hide which hospitals ran them, and see whether our
  ranking picks those hospitals, compared with simply picking the hospitals
  with the most past trials.

Rules (no peeking at the answer):
  - For each target trial, the ranker only sees trials that STARTED BEFORE it.
  - The target trial's own site list is the answer key and is never used to rank.

Only uses the Python standard library. Run:  python3 backtest.py
Data is cached in <condition>_trials.json after the first download.
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date

CONDITION = "multiple myeloma"   # was "asthma": big asthma sponsors hide site names
K = 50                       # how many sites each ranker gets to pick
TARGET_START = date(2018, 1, 1)
TARGET_END = date(2023, 12, 31)
MIN_US_SITES = 10
CACHE = CONDITION.replace(" ", "_") + "_trials.json"
TAGS = "trial_tags.json"   # asthma-only AI tags; skipped for other conditions
API = "https://clinicaltrials.gov/api/v2/studies"

# ---------------------------------------------------------------- download

def download():
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            return json.load(f)
    studies, token = [], None
    while True:
        params = {"query.cond": CONDITION, "pageSize": 1000, "format": "json"}
        if token:
            params["pageToken"] = token
        url = API + "?" + urllib.parse.urlencode(params)
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "site-backtest/1.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    page = json.load(r)
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"  retrying after error: {e}")
                time.sleep(3)
        studies.extend(page.get("studies", []))
        print(f"  downloaded {len(studies)} studies...")
        token = page.get("nextPageToken")
        if not token:
            break
    with open(CACHE, "w") as f:
        json.dump(studies, f)
    return studies

# ---------------------------------------------------------------- parsing

def parse_date(s):
    if not s:
        return None
    parts = s.split("-")
    try:
        y = int(parts[0]); m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return date(y, m, d)
    except Exception:
        return None

# Sponsor placeholders ("Research Site", "GSK Investigational Site", "Site Number 840001")
# hide the real hospital, so a match would only mean "same city". Drop them.
# ponytail: regex blocklist; sponsor-named facilities ("Pearl Therapeutics") still slip through.
PLACEHOLDER = re.compile(r"\b(sites?|investigat\w*)\b|^for additional")

GENERIC = {"inc", "llc", "pc", "pa", "pllc", "ltd", "corp", "the"}

def norm_name(name):
    s = name.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = [w for w in s.split() if w not in GENERIC]
    return " ".join(words)

def site_key(loc):
    return (norm_name(loc.get("facility", "")),
            (loc.get("city") or "").strip().lower(),
            (loc.get("state") or "").strip().lower())

def phase_bucket(phases):
    p = set(phases or [])
    if "PHASE3" in p: return "P3"
    if "PHASE2" in p: return "P2"
    if "PHASE1" in p: return "P1"
    if "PHASE4" in p: return "P4"
    return "NA"

def parse(studies):
    trials = []
    for s in studies:
        ps = s.get("protocolSection", {})
        design = ps.get("designModule", {})
        if design.get("studyType") != "INTERVENTIONAL":
            continue
        # query.cond also matches trials that only mention asthma (e.g. eosinophilic esophagitis)
        conds = ps.get("conditionsModule", {}).get("conditions", [])
        if not any(CONDITION in c.lower() for c in conds):
            continue
        status = ps.get("statusModule", {})
        start = parse_date(status.get("startDateStruct", {}).get("date"))
        end = parse_date((status.get("completionDateStruct") or {}).get("date")) or \
              parse_date((status.get("primaryCompletionDateStruct") or {}).get("date"))
        if not start:
            continue
        sponsor = ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
        locs = ps.get("contactsLocationsModule", {}).get("locations", []) or []
        sites = {site_key(l) for l in locs
                 if l.get("country") == "United States" and l.get("facility")}
        sites = {k for k in sites if k[0] and not PLACEHOLDER.search(k[0])}
        if not sites:
            continue
        trials.append({
            "nct": ps.get("identificationModule", {}).get("nctId"),
            "title": ps.get("identificationModule", {}).get("briefTitle", ""),
            "start": start, "end": end,
            "status": status.get("overallStatus"),
            "phase": phase_bucket(design.get("phases")),
            "sponsor": sponsor.get("name", ""),
            "sponsor_class": sponsor.get("class", ""),
            "sites": sites,
        })
    return trials

# ---------------------------------------------------------------- rankers

def history_before(trials, target):
    return [t for t in trials if t["start"] < target["start"] and t["nct"] != target["nct"]]

def rank_count(history, target):
    score = defaultdict(float)
    for t in history:
        for s in t["sites"]:
            score[s] += 1
    return score

def shared_tags(tags, a, b):
    """How many AI tags (pop, severity, drug, eos) two trials share; 0 if either is untagged."""
    ta, tb = tags.get(a["nct"]), tags.get(b["nct"])
    return sum(ta[k] == tb[k] for k in ta) if ta and tb else 0

def rank_ours(history, target, use_sponsor, tags=None):
    """Past experience, weighted toward recent and same-phase trials,
    minus trials the site is still running when the target starts (competition).
    Optionally boosts sites that worked with the same sponsor before,
    and (with tags) past trials that look like the target (AI-tagged)."""
    score = defaultdict(float)
    for t in history:
        years_ago = (target["start"] - t["start"]).days / 365.25
        w = math.exp(-years_ago / 4.0)                    # recent counts more
        if t["phase"] == target["phase"]:
            w *= 1.5                                      # same phase counts extra
        if use_sponsor and t["sponsor"] == target["sponsor"]:
            w *= 3.0                                      # repeat sponsor-site pairs
        if tags:
            w *= 1 + shared_tags(tags, t, target)         # similar trials count more
        still_running = t["end"] is None or t["end"] > target["start"]
        for s in t["sites"]:
            score[s] += w
            if still_running and t["sponsor"] != target["sponsor"]:
                score[s] -= 0.3                           # competing trial right now
    return score

def top_k(score, k):
    return [s for s, _ in sorted(score.items(), key=lambda x: (-x[1], x[0]))[:k]]

# ---------------------------------------------------------------- main

def main():
    print(f"Downloading {CONDITION} trials from ClinicalTrials.gov (cached after first run)...")
    trials = parse(download())
    print(f"{len(trials)} interventional {CONDITION} trials with US sites.\n")

    targets = [t for t in trials
               if t["status"] in ("COMPLETED", "ACTIVE_NOT_RECRUITING")  # enrollment over, site list final
               and t["sponsor_class"] == "INDUSTRY"
               and t["phase"] in ("P2", "P3")
               and TARGET_START <= t["start"] <= TARGET_END
               and len(t["sites"]) >= MIN_US_SITES]
    targets.sort(key=lambda t: t["start"])
    print(f"Test set: {len(targets)} completed industry Phase 2/3 {CONDITION} trials, "
          f"started {TARGET_START.year}-{TARGET_END.year}, with {MIN_US_SITES}+ US sites.\n")
    if not targets:
        sys.exit("No target trials found; check the download.")

    # AI tags made by Claude from title/conditions/interventions only (see tag_input.py)
    tags = json.load(open(TAGS)) if CONDITION == "asthma" else None
    names = ["Random pick", "Most past trials", "Ours", "Ours + same sponsor"] + (["Ours + AI similarity"] if tags else [])
    totals = {n: 0.0 for n in names}
    true_total = reachable_total = 0
    rows = []
    for tgt in targets:
        hist = history_before(trials, tgt)
        cands = set().union(*[t["sites"] for t in hist]) if hist else set()
        truth = tgt["sites"]
        reachable = truth & cands
        true_total += len(truth); reachable_total += len(reachable)
        hits = {}
        hits["Random pick"] = (min(K, len(cands)) * len(reachable) / len(cands)) if cands else 0
        hits["Most past trials"] = len(set(top_k(rank_count(hist, tgt), K)) & truth)
        hits["Ours"] = len(set(top_k(rank_ours(hist, tgt, False), K)) & truth)
        hits["Ours + same sponsor"] = len(set(top_k(rank_ours(hist, tgt, True), K)) & truth)
        if tags:
            hits["Ours + AI similarity"] = len(set(top_k(rank_ours(hist, tgt, False, tags), K)) & truth)
        for n in names:
            totals[n] += hits[n]
        rows.append((tgt, len(truth), len(reachable), hits))

    # per-trial table
    with open("results_per_trial.csv", "w") as f:
        f.write("nct_id,start,phase,sponsor,true_sites,findable_sites," +
                ",".join(names) + "\n")
        for tgt, n_true, n_reach, h in rows:
            f.write(f'{tgt["nct"]},{tgt["start"]},{tgt["phase"]},"{tgt["sponsor"]}",'
                    f'{n_true},{n_reach},' + ",".join(f"{h[n]:.1f}" for n in names) + "\n")

    lines = []
    lines.append(f"# Site-selection backtest: {len(targets)} past {CONDITION} trials\n")
    lines.append(f"Each ranker picks {K} US sites per trial using only trials that started earlier.\n")
    lines.append(f"Real sites across all test trials: {true_total} "
                 f"(of which {reachable_total} had run an earlier {CONDITION} trial, "
                 f"so {100*reachable_total/true_total:.0f}% is the most any ranker could find).\n")
    lines.append("| Ranker | Real sites found | Share of real sites |")
    lines.append("|---|---|---|")
    for n in names:
        lines.append(f"| {n} | {totals[n]:.0f} | {100*totals[n]/true_total:.1f}% |")
    if tags:
        d = [h["Ours + AI similarity"] - h["Ours"] for _, _, _, h in rows]
        lines.append(f"\nOurs + AI similarity vs Ours, per trial: {sum(x > 0 for x in d)} wins, "
                     f"{sum(x == 0 for x in d)} ties, {sum(x < 0 for x in d)} losses.")
    summary = "\n".join(lines)
    print(summary)
    with open("results_summary.md", "w") as f:
        f.write(summary + "\n")
    print("\nWrote results_summary.md and results_per_trial.csv")

if __name__ == "__main__":
    main()
