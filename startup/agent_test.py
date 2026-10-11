#!/usr/bin/env python3
"""
Looser test: an AI agent picks the 50 sites itself, using the same history data
plus its own web research.

  python3 agent_test.py prep [NCT...]   # writes agent_runs/<condition>/t<hash>/{brief.md,history.csv,candidates.csv,ctg.py}
  (an agent per folder writes picks.txt (candidate ids) or picks.csv (facility,city,state), and sources.md)
  python3 agent_test.py score [NCT...]  # scores picks against the real site lists
Pass NCT IDs to test specific trials instead of the backtest's test set.

Folders are named by a hash, not the NCT ID, so the agent isn't handed the answer.
picks.txt: chosen from candidates.csv (same ceiling as the backtest).
picks.csv: any US site, matched by city + state + similar name; formula rankers are
scored the same way so the comparison stays fair.
"""
import csv, difflib, hashlib, json, os, shutil, sys
import backtest as b

OUT = "agent_runs/" + b.CONDITION.replace(" ", "_")

def folder(nct):
    return f"{OUT}/t{hashlib.sha256(nct.encode()).hexdigest()[:6]}"

COMMON = set("university of the and center medical hospital health cancer institute clinic clinical research "
             "school medicine system comprehensive college at division in for clinics hospitals centers".split())

def same_site(n, t, place):
    """n, t: normalized names in the same city. Shared distinctive word, near-identical spelling, or a bare
    "University of <city/state>" name inside the other ("University of Miami" vs "Sylvester ... University of Miami")."""
    dn, dt = set(n.split()) - COMMON - place, set(t.split()) - COMMON - place
    uni = lambda s: {w for w in place if f"university of {w}" in s}
    return bool(dn & dt or difflib.SequenceMatcher(None, n, t).ratio() >= 0.8 or ((not dn or not dt) and uni(n) & uni(t)))

def fuzzy_hits(picks, truth):
    """Count real sites matched by a pick in the same city+state with a similar name (each used once).
    ponytail: name heuristic (see same_site); hand-check hits before quoting."""
    left, hits = set(truth), 0
    for name, city, state in picks:
        n = b.norm_name(name)
        for t in sorted(left):
            if t[1] == city.strip().lower() and t[2] == state.strip().lower() and same_site(n, t[0], set(f"{t[1]} {t[2]}".split())):
                left.discard(t); hits += 1
                break
    return hits

def setup(ncts=()):
    studies = b.download()
    raw = {s["protocolSection"]["identificationModule"]["nctId"]: s["protocolSection"] for s in studies}
    trials = b.parse(studies)
    targets = sorted([t for t in trials
                      if t["status"] in ("COMPLETED", "ACTIVE_NOT_RECRUITING") and t["sponsor_class"] == "INDUSTRY"
                      and t["phase"] in ("P2", "P3")
                      and b.TARGET_START <= t["start"] <= b.TARGET_END
                      and len(t["sites"]) >= b.MIN_US_SITES], key=lambda t: t["start"])
    if ncts:
        targets = [t for t in trials if t["nct"] in ncts]
    return raw, trials, targets

def prep(ncts):
    raw, trials, targets = setup(ncts)
    tags = json.load(open(b.TAGS)) if b.CONDITION == "asthma" else {}
    for i, tgt in enumerate(targets, 1):
        d = folder(tgt["nct"])
        os.makedirs(d, exist_ok=True)
        shutil.copy("ctg.py", d)
        json.dump({"cutoff": str(tgt["start"]), "hidden": hashlib.sha256(tgt["nct"].encode()).hexdigest()},
                  open(f"{d}/ctg_config.json", "w"))
        ps = raw[tgt["nct"]]
        ivs = [f'{v.get("type", "")}: {v.get("name", "")}' for v in ps.get("armsInterventionsModule", {}).get("interventions", [])]
        el = ps.get("eligibilityModule", {})
        with open(f"{d}/brief.md", "w") as f:
            f.write(f"# New trial (sponsor's view before site selection)\n\n"
                    f"- Sponsor: {tgt['sponsor']}\n- Phase: {tgt['phase']}\n"
                    f"- Planned start: {tgt['start']:%Y-%m}\n"
                    f"- Conditions: {'; '.join(ps.get('conditionsModule', {}).get('conditions', []))}\n"
                    f"- Interventions: {'; '.join(ivs)}\n"
                    f"- Ages: {el.get('minimumAge', '?')} to {el.get('maximumAge', 'no max')}\n\n"
                    f"## Summary\n{ps.get('descriptionModule', {}).get('briefSummary', '')}\n\n"
                    f"## Eligibility\n{el.get('eligibilityCriteria', '')}\n")
        hist = b.history_before(trials, tgt)
        with open(f"{d}/history.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["nct", "start", "end", "phase", "sponsor", "sponsor_class", "title",
                        "pop", "severity", "drug", "eos", "facility", "city", "state"])
            for t in hist:
                tg = tags.get(t["nct"], {})
                for s in sorted(t["sites"]):
                    w.writerow([t["nct"], t["start"], t["end"], t["phase"], t["sponsor"], t["sponsor_class"],
                                t["title"], tg.get("pop"), tg.get("severity"), tg.get("drug"), tg.get("eos"), *s])
        with open(f"{d}/candidates.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "facility", "city", "state"])
            for j, s in enumerate(sorted(set().union(*[t["sites"] for t in hist])), 1):
                w.writerow([j, *s])
    print(f"Wrote {len(targets)} folders in {OUT}/")

def score(ncts):
    raw, trials, targets = setup(ncts)
    tot = {"agent": 0, "ours": 0.0, "count": 0.0, "truth": 0}
    print("run  nct          true  findable  agent  ours  +sponsor  count")
    for i, tgt in enumerate(targets, 1):
        d = folder(tgt["nct"])
        tot["truth"] += len(tgt["sites"])
        hist = b.history_before(trials, tgt)
        if os.path.exists(f"{d}/picks.csv"):          # free-text picks: fuzzy match everyone
            picks = [(r["facility"], r["city"], r["state"]) for r in csv.DictReader(open(f"{d}/picks.csv"))][:b.K]
            hits = lambda sites: fuzzy_hits(sites, tgt["sites"])
        elif os.path.exists(f"{d}/picks.txt"):
            cands = {r["id"]: (r["facility"], r["city"], r["state"]) for r in csv.DictReader(open(f"{d}/candidates.csv"))}
            ids = [x.strip() for x in open(f"{d}/picks.txt").read().split() if x.strip() in cands]
            picks = [cands[x] for x in dict.fromkeys(ids)][:b.K]   # first K distinct valid ids only
            hits = lambda sites: len(set(sites) & tgt["sites"])
        else:
            print(f"t{i:02d}  {tgt['nct']}  missing picks"); continue
        hit = hits(picks)
        ours = hits(b.top_k(b.rank_ours(hist, tgt, False), b.K))
        spon = hits(b.top_k(b.rank_ours(hist, tgt, True), b.K))
        count = hits(b.top_k(b.rank_count(hist, tgt), b.K))
        reach = len(tgt["sites"] & set().union(*[t["sites"] for t in hist]))
        tot["agent"] += hit; tot["ours"] += ours; tot["count"] += count
        print(f"t{i:02d}  {tgt['nct']}  {len(tgt['sites']):4}  {reach:9}  {hit:5}  {ours:4}  {spon:10}  {count:5}")
    print(f"\nShare of real sites: agent {100*tot['agent']/tot['truth']:.1f}%, "
          f"ours {100*tot['ours']/tot['truth']:.1f}%, most past trials {100*tot['count']/tot['truth']:.1f}%")

if __name__ == "__main__":
    {"prep": prep, "score": score}[sys.argv[1] if len(sys.argv) > 1 else ""](sys.argv[2:])
