#!/usr/bin/env python3
"""
End-to-end run on LINKER-MM3 (NCT05730036), one stage at a time with pass gates.

  python3 e2e.py prep1   | gate1     stage 1: find sites (sponsor agent, pre-start data only)
  python3 e2e.py prep2   | gate2     stage 2: contacts for the top 12
  python3 e2e.py prep3a  | gate3a    stage 3a: draft questionnaire
  python3 e2e.py prep3b  | gate3b    stage 3b: site answers (public pre-fill for 12 + Riverside from its files)
  python3 e2e.py prep4   | gate4     stage 4: select
  python3 e2e.py build               -> app/runs/linker-mm3.json (what the page shows)

Agents work only inside runs/linker-mm3/stageN/. Answer keys and gate reports live one level up.
Gates are fixed in gates.json before stage 1 runs; a failed gate writes FLAG.md and the run stops.
"""
import csv, glob, hashlib, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request
from datetime import date
import backtest as b, agent_test as a

TARGET, START = "NCT05730036", "2023-09-18"
R = "runs/linker-mm3"
GATES = {
    "1": {"min_real_sites": 4, "note": "beats best formula baseline (3 of 10 with fuzzy matching); every pick cites a real pre-start trial; never names the target"},
    "2": {"min_still_there": 10, "of": 12, "active_since": "2025-04-11", "min_room_ok": 10,
          "note": "PI filed a 1572 in the site's city in the 18 months before the run; all 4 criteria reported; seniority-only picks routed "
                  "to the office; competing-trial count within 2 of script rule; no dead URLs; no emails/phones"},
    "3a": {"min_must_cover": 12, "max_questions": 16, "max_redundant": 0, "min_closed_share": 0.9},
    "3b": {"min_public_facts_ok": 0.9, "riverside_made_up": 0, "note": "public counts within +-15%/3 of script rule; Riverside unanswerables flagged"},
    "4": {"riverside_reason": "gcp", "note": "every decision cites answers; every flag gets a follow-up; nothing sent"},
}

def raw():
    return {s["protocolSection"]["identificationModule"]["nctId"]: s["protocolSection"] for s in b.download()}

def trials():
    return b.parse(b.download())

def target():
    return next(t for t in trials() if t["nct"] == TARGET)

def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, default=str)

def report(stage, checks):
    """checks: list of (name, ok, detail). Writes gate report; on failure writes FLAG.md and exits 1."""
    ok = all(c[1] for c in checks)
    save(f"{R}/gate{stage}.json", {"stage": stage, "passed": ok, "checks": [{"check": n, "ok": o, "detail": d} for n, o, d in checks]})
    for n, o, d in checks:
        print(f"  [{'PASS' if o else 'FAIL'}] {n}: {d}")
    if not ok:
        open(f"{R}/FLAG.md", "w").write(f"# Stage {stage} failed its gate\n\n" +
            "\n".join(f"- {'PASS' if o else '**FAIL**'} {n}: {d}" for n, o, d in checks) +
            "\n\nOptions: fix the input and rerun this stage (logged), change the bar with a stated reason, or stop.\n")
        print(f"\nSTAGE {stage} FAILED -> {R}/FLAG.md")
        sys.exit(1)
    print(f"\nStage {stage} passed.")

def ctg_folder(d, cutoff, hidden):
    shutil.copy("ctg.py", d)
    json.dump({"cutoff": cutoff, "hidden": hidden}, open(f"{d}/ctg_config.json", "w"))

def ctg_lookup(ncts):
    """Fetch start dates for NCT IDs straight from the API (gate-side check, not the agent's)."""
    out = {}
    ids = sorted(set(ncts))
    for i in range(0, len(ids), 100):
        p = {"filter.ids": ",".join(ids[i:i + 100]), "fields": "NCTId,StartDate", "pageSize": 1000}
        page = json.load(urllib.request.urlopen("https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(p), timeout=60))
        for s in page.get("studies", []):
            ps = s["protocolSection"]
            out[ps["identificationModule"]["nctId"]] = ps.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
    return out

# ---------------------------------------------------------------- stage 1

def prep1():
    os.makedirs(f"{R}/stage1", exist_ok=True)
    if not os.path.exists(f"{R}/gates.json"):
        save(f"{R}/gates.json", {"fixed_on": str(date.today()), "gates": GATES})
    ps, tgt = raw()[TARGET], target()
    ivs = "; ".join(v.get("name", "") for v in ps["armsInterventionsModule"]["interventions"])
    el = ps["eligibilityModule"]
    open(f"{R}/stage1/brief.md", "w").write(
        f"# New trial (sponsor's view before site selection)\n\n- Sponsor: Regeneron Pharmaceuticals\n- Phase 3, randomized 1:1, ~410 participants\n"
        f"- Planned start: {START[:7]}\n- Conditions: {'; '.join(ps['conditionsModule']['conditions'])}\n- Interventions: {ivs}\n\n"
        f"## Summary\n{ps['descriptionModule']['briefSummary']}\n\n## Eligibility\n{el['eligibilityCriteria']}\n")
    ctg_folder(f"{R}/stage1", START, hashlib.sha256(TARGET.encode()).hexdigest())
    hist = b.history_before(trials(), tgt)
    with open(f"{R}/stage1/history.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["nct", "start", "end", "phase", "sponsor", "sponsor_class", "title", "facility", "city", "state"])
        for t in hist:
            for s in sorted(t["sites"]):
                w.writerow([t["nct"], t["start"], t["end"], t["phase"], t["sponsor"], t["sponsor_class"], t["title"], *s])
    # baselines on the same truth, same fuzzy matcher
    hits = lambda sites: a.fuzzy_hits(sites, tgt["sites"])
    base = {"most_past_trials": hits(b.top_k(b.rank_count(hist, tgt), b.K)), "ours": hits(b.top_k(b.rank_ours(hist, tgt, False), b.K)),
            "ours_same_sponsor": hits(b.top_k(b.rank_ours(hist, tgt, True), b.K)), "real_us_sites": len(tgt["sites"])}
    save(f"{R}/baselines1.json", base)
    print("prep1 done. Baselines:", base)

def gate1():
    tgt = target()
    d = json.load(open(f"{R}/stage1/sites.json"))
    sites = sorted(d["sites"], key=lambda s: s["rank"])[:50]
    picks = [(s["facility"], s["city"], s["state"]) for s in sites]
    hit = a.fuzzy_hits(picks, tgt["sites"])
    cited = sorted({n for s in sites for n in s.get("past_trials", [])})
    starts = ctg_lookup(cited)
    bad = [n for n in cited if n not in starts or not starts[n] or starts[n] >= START[:len(starts[n])] or n == TARGET]
    text = open(f"{R}/stage1/sites.json").read() + "".join(open(p).read() for p in glob.glob(f"{R}/stage1/*.md") if not p.endswith("brief.md"))
    leak = bool(re.search(r"NCT05730036|LINKER-MM3", text, re.I))
    base = json.load(open(f"{R}/baselines1.json"))
    report("1", [
        ("50 ranked picks", len(sites) == 50, f"{len(sites)} picks"),
        ("real sites found", hit >= GATES["1"]["min_real_sites"], f"{hit} of {len(tgt['sites'])} (baselines: count {base['most_past_trials']}, ours {base['ours']}, +sponsor {base['ours_same_sponsor']})"),
        ("every pick cites a past trial", all(s.get("past_trials") for s in sites), f"{sum(bool(s.get('past_trials')) for s in sites)}/50"),
        ("citations real and pre-start", not bad, f"{len(cited)} cited, bad: {bad[:8]}"),
        ("never names the target", not leak, "clean" if not leak else "target named in outputs"),
    ])

# ---------------------------------------------------------------- stage 2

STATE = {"Alabama":"AL","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC",
  "Florida":"FL","Georgia":"GA","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
  "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
  "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI",
  "South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV",
  "Wisconsin":"WI","Wyoming":"WY"}

def bmis_latest(name, city, state):
    """Gate-side check: latest 1572 received for this person at this city (BMIS, 2018-2026)."""
    from contact_test import person
    p = person(name or "")
    if not p: return None
    st, cty, best = STATE.get(state, state), city.strip().upper(), None
    for r in csv.DictReader(open("data/bmis_ci_us.tsv"), delimiter="\t"):
        if r["last"].lower() == p[0] and r["first"][:1].lower() == p[1] and r["state"] == st and r["city"].upper() == cty:
            best = max(best or "", r["received"])
    return best

def prep2():
    d = f"{R}/stage2"; os.makedirs(d, exist_ok=True)
    top = sorted(json.load(open(f"{R}/stage1/sites.json"))["sites"], key=lambda s: s["rank"])[:12]
    with open(f"{d}/sites.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["rank", "facility", "city", "state"])
        for s in top: w.writerow([s["rank"], s["facility"], s["city"], s["state"]])
    shutil.copy(f"{R}/stage1/brief.md", d)
    ctg_folder(d, str(date.today()), hashlib.sha256(TARGET.encode()).hexdigest())
    shutil.copy("bmis.py", d); shutil.copy("data/bmis_ci_us.tsv", d)
    print("prep2 done:", len(top), "sites")

def url_status(u):
    try:
        out = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-m", "15", "-A", "Mozilla/5.0", "-w", "%{http_code}", u], capture_output=True, text=True)
        return int(out.stdout or 0)
    except Exception:
        return 0

def competing(name, city, state):
    """Script rule for 'has room': recruiting myeloma trials listing this person as PI at a location in this city."""
    from contact_test import person, pis
    p = person(name or "")
    if not p: return None
    n = 0
    for ps in raw().values():
        if ps["statusModule"]["overallStatus"] != "RECRUITING": continue
        locs = [l for l in ps.get("contactsLocationsModule", {}).get("locations", []) or [] if l.get("city") == city and l.get("state") == state]
        n += any(person(x) == p for l in locs for x in pis(l))
    return n

CRITERIA = ("still_there", "same_drug", "same_kind", "has_room")

def gate2():
    g = GATES["2"]
    cs = json.load(open(f"{R}/stage2/contacts.json"))["contacts"]
    active, dead, room_ok, missing, misrouted = 0, [], 0, [], []
    for c in cs:
        c["bmis_latest"] = bmis_latest(c.get("pi"), c["city"], c["state"])
        active += bool(c["bmis_latest"] and c["bmis_latest"] >= g["active_since"])
        code = url_status(c.get("contact_url", "")) if c.get("contact_url") else 0
        c["url_status"] = code
        if code == 0 or code == 404 or code == 410 or code >= 500: dead.append(f"{c['rank']}:{code}")
        cr = c.get("criteria", {})
        if any(not cr.get(k, {}).get("finding") for k in CRITERIA): missing.append(c["rank"])
        if all(cr.get(k, {}).get("met") != "yes" for k in ("same_drug", "same_kind")) and c.get("route") != "office": misrouted.append(c["rank"])
        c["competing_rule"] = competing(c.get("pi"), c["city"], c["state"])
        got = cr.get("has_room", {}).get("competing")
        room_ok += got is not None and c["competing_rule"] is not None and abs(int(got) - c["competing_rule"]) <= 2
    save(f"{R}/stage2_checked.json", cs)
    text = open(f"{R}/stage2/contacts.json").read()
    pii = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+|\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}", text)
    report("2", [
        ("12 contacts", len(cs) == 12, f"{len(cs)}"),
        (f"PI still there: FDA 1572 in the site's city since {g['active_since']} (BMIS)", active >= g["min_still_there"], f"{active} of {len(cs)}"),
        ("all 4 criteria reported", not missing, f"missing at: {missing or 'none'}"),
        ("seniority-only picks routed to the office", not misrouted, f"misrouted: {misrouted or 'none'}"),
        ("competing-trial count within 2 of script rule", room_ok >= g["min_room_ok"], f"{room_ok} of {len(cs)}"),
        ("no dead contact URLs", not dead, f"dead: {dead}" if dead else "all reachable (403 = bot-blocked, counted reachable)"),
        ("no emails or phone numbers", not pii, f"found: {pii[:3]}" if pii else "none"),
    ])

# ---------------------------------------------------------------- stage 3a

def prep3a():
    d = f"{R}/stage3a"; os.makedirs(d, exist_ok=True)
    shutil.copy("agent_runs/draft/protocol.md", d)
    shutil.copy(f"{R}/stage2/sites.csv", d)
    ctg_folder(d, str(date.today()), hashlib.sha256(TARGET.encode()).hexdigest())
    print("prep3a done")

def gate3a():
    d = json.load(open(f"{R}/stage3a/questionnaire.json"))
    qs = d["questionnaire"]
    closed = sum(not q["format"].lower().startswith("short text") for q in qs)
    g = json.load(open(f"{R}/grade3a.json"))       # hand grade against draft_must_cover.md, written after reading outputs
    covered = sum(v in ("question", "prefill") for v in g["must_cover"].values())
    report("3a", [
        ("must-cover items (draft_must_cover.md)", covered >= GATES["3a"]["min_must_cover"], f"{covered} of 14; missing: {[k for k, v in g['must_cover'].items() if v == 'missing']}"),
        ("questions", len(qs) <= GATES["3a"]["max_questions"], f"{len(qs)}"),
        ("redundant (asks public facts)", len(g["redundant"]) <= GATES["3a"]["max_redundant"], f"{g['redundant'] or 'none'}"),
        ("closed-format share", closed / len(qs) >= GATES["3a"]["min_closed_share"], f"{closed}/{len(qs)}"),
    ])

# ---------------------------------------------------------------- stage 3b

def site_counts(facility, city, state):
    """Script rule: interventional myeloma trials (not withdrawn) with a US location at this site (city+state+similar name)."""
    rec = te = 0
    from site_real_test import BISPECIFIC
    for nct, ps in raw().items():
        if ps["designModule"].get("studyType") != "INTERVENTIONAL" or ps["statusModule"]["overallStatus"] == "WITHDRAWN": continue
        locs = [(l.get("facility", ""), l.get("city", ""), l.get("state", "")) for l in ps.get("contactsLocationsModule", {}).get("locations", []) or []
                if l.get("country") == "United States" and l.get("facility")]
        if not any(a.fuzzy_hits([loc], {b.site_key({"facility": facility, "city": city, "state": state})}) for loc in locs): continue
        rec += ps["statusModule"]["overallStatus"] == "RECRUITING"
        txt = ps["identificationModule"].get("briefTitle", "") + " " + " ".join(i.get("name", "") for i in ps.get("armsInterventionsModule", {}).get("interventions", []))
        te += bool(BISPECIFIC.search(txt))
    return rec, te

def prep3b():
    q = f"{R}/stage3a/questionnaire.json"
    pub, riv = f"{R}/stage3b_public", f"{R}/stage3b_riverside"
    for d in (pub, riv): os.makedirs(d, exist_ok=True); shutil.copy(q, d)
    shutil.copy(f"{R}/stage2/sites.csv", pub)
    ctg_folder(pub, str(date.today()), "none")
    if os.path.exists(f"{riv}/docs"): shutil.rmtree(f"{riv}/docs")
    src = "site_data/riverside" if os.path.isdir("site_data/riverside") else "agent_runs/site/riverside/docs"   # public/ + confidential/
    shutil.copytree(src, f"{riv}/docs")
    print("prep3b done")

def gate3b():
    pre = json.load(open(f"{R}/stage3b_public/prefill.json"))["sites"]
    sites = {r["rank"]: r for r in csv.DictReader(open(f"{R}/stage2/sites.csv"))}
    ok = n = 0; misses = []
    for s in pre:
        site = sites[str(s["rank"])]
        rec, te = site_counts(site["facility"], site["city"], site["state"])
        for label, truth, got in (("recruiting", rec, s.get("myeloma_trials_recruiting")), ("t-cell engager", te, s.get("tcell_engager_trials"))):
            n += 1
            good = got is not None and abs(float(got) - truth) <= max(3, 0.15 * truth)
            ok += good
            if not good: misses.append(f"#{s['rank']} {label}: agent {got} vs rule {truth}")
    save(f"{R}/stage3b_public_checked.json", {"ok": ok, "n": n, "misses": misses})
    g = json.load(open(f"{R}/grade3b.json"))      # hand grade of Riverside answers against its docs
    made_up = [k for k, v in g["riverside"].items() if v == "made_up"]
    unflagged = [k for k, v in g["riverside"].items() if v == "should_flag"]
    wrong = [k for k, v in g["riverside"].items() if v == "wrong"]
    report("3b", [
        ("public pre-fill counts match script rule (+-15% or 3)", n and ok / n >= GATES["3b"]["min_public_facts_ok"], f"{ok} of {n}; misses: {misses[:4]}"),
        ("Riverside: made-up answers", not made_up, f"{made_up or 'none'}"),
        ("Riverside: unanswerables flagged", not unflagged, f"unflagged: {unflagged or 'none'}"),
        ("Riverside: wrong answers (reported, not gated)", True, f"{wrong or 'none'} of {len(g['riverside'])}"),
    ])

# ---------------------------------------------------------------- stage 4

def prep4():
    d = f"{R}/stage4"; os.makedirs(d, exist_ok=True)
    shutil.copy(f"{R}/stage3a/questionnaire.json", d)
    shutil.copy(f"{R}/stage3b_public/prefill.json", f"{d}/public_prefill.json")
    shutil.copy(f"{R}/stage3b_public/answers.json", f"{d}/public_answers.json")
    shutil.copy(f"{R}/stage3b_riverside/answers.json", f"{d}/riverside_answers.json")
    print("prep4 done")

def gate4():
    ds = json.load(open(f"{R}/stage4/decisions.json"))["decisions"]
    riv = next((x for x in ds if x["site_key"] == "riverside"), None)
    pub = json.load(open(f"{R}/stage3b_public/answers.json"))["sites"]
    flagged = {str(s["rank"]) for s in pub if any(str(x.get("needs_human", "")).lower().startswith("y") for x in s["answers"])}
    no_fu = [x["site_key"] for x in ds if x["site_key"] in flagged and not x.get("follow_ups")]
    report("4", [
        ("13 decisions (12 sites + Riverside)", len(ds) == 13, f"{len(ds)}"),
        ("Riverside reason names the expired GCP certificate", bool(riv) and any("gcp" in r.lower() for r in riv.get("reasons", [])), next((r for r in (riv or {}).get("reasons", []) if "gcp" in r.lower()), "none")[:120]),
        ("every decision cites answers", all(x.get("cites") for x in ds), f"{sum(bool(x.get('cites')) for x in ds)}/{len(ds)}"),
        ("every site with open items gets a follow-up", not no_fu, f"missing: {no_fu or 'none'}"),
        ("nothing sent (all pending approval)", all(x.get("status") == "pending_approval" for x in ds), "all pending" if all(x.get("status") == "pending_approval" for x in ds) else "some not pending"),
    ])

# ---------------------------------------------------------------- build

def geo_index():
    """(city, state) -> (lat, lon) from ClinicalTrials.gov location geoPoints (city-level)."""
    g = {}
    for st in b.download():
        for l in st["protocolSection"].get("contactsLocationsModule", {}).get("locations", []) or []:
            gp = l.get("geoPoint")
            if gp and l.get("country") == "United States":
                g.setdefault(((l.get("city") or "").lower(), (l.get("state") or "").lower()), (gp["lat"], gp["lon"]))
    return g

def ctg_meta(ncts):
    out, ids = {}, sorted(set(ncts))
    for i in range(0, len(ids), 100):
        p = {"filter.ids": ",".join(ids[i:i + 100]), "fields": "NCTId,BriefTitle,LeadSponsorName,StartDate", "pageSize": 1000}
        for st in json.load(urllib.request.urlopen("https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(p), timeout=60)).get("studies", []):
            ps = st["protocolSection"]
            out[ps["identificationModule"]["nctId"]] = {"nct": ps["identificationModule"]["nctId"], "title": ps["identificationModule"].get("briefTitle", ""),
                "sponsor": ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", ""), "start": ps.get("statusModule", {}).get("startDateStruct", {}).get("date", "")}
    return out

def loadj(p, default=None):
    return json.load(open(p)) if os.path.exists(p) else default

def build():
    tgt, geo, run = target(), geo_index(), {}
    loc = lambda x: geo.get((x["city"].lower(), x["state"].lower()), (None, None))
    run["trial"] = {"nct": TARGET, "name": "LINKER-MM3", "sponsor": "Regeneron Pharmaceuticals", "drug": "linvoseltamab (BCMAxCD3)", "start": START, "real_us_sites": len(tgt["sites"])}
    run["recorded"] = str(date.today())
    run["timeline"] = loadj(f"{R}/timeline.json", [])
    run["gates"] = {k: loadj(f"{R}/gate{k}.json") for k in ("1", "2", "3a", "3b", "4") if os.path.exists(f"{R}/gate{k}.json")}
    passed = lambda k: (run["gates"].get(k) or {}).get("passed")
    if passed("1"):
        d = json.load(open(f"{R}/stage1/sites.json"))
        sites = sorted(d["sites"], key=lambda s: s["rank"])[:50]
        meta = ctg_meta([n for s in sites for n in s.get("past_trials", [])])
        for s in sites:
            s["lat"], s["lon"] = loc(s)
            s["real"] = a.fuzzy_hits([(s["facility"], s["city"], s["state"])], tgt["sites"]) == 1
            s["past_trials"] = [meta.get(n, {"nct": n}) for n in s.get("past_trials", [])]
        scored = [dict(x, lat=loc(x)[0], lon=loc(x)[1]) for x in d.get("scored", [])]
        base = json.load(open(f"{R}/baselines1.json"))
        run["stage1"] = {"sites": sites, "scored": scored, "n_candidates": len(sites) + len(scored),
                         "score": {"found": sum(s["real"] for s in sites), "of": len(tgt["sites"]), "baselines": base}}
    if passed("2"):
        cs = json.load(open(f"{R}/stage2_checked.json"))
        for c in cs: c["bmis_active"] = bool(c.get("bmis_latest") and c["bmis_latest"] >= GATES["2"]["active_since"])
        run["stage2"] = {"contacts": sorted(cs, key=lambda c: c["rank"])}
    if passed("3a") and passed("3b"):
        qd = json.load(open(f"{R}/stage3a/questionnaire.json"))
        pre = json.load(open(f"{R}/stage3b_public/prefill.json"))["sites"]
        pans = json.load(open(f"{R}/stage3b_public/answers.json"))["sites"]
        riv = json.load(open(f"{R}/stage3b_riverside/answers.json"))
        top = {r["rank"]: r for r in csv.DictReader(open(f"{R}/stage2/sites.csv"))}
        short = {str(c["rank"]): c.get("short") for c in run.get("stage2", {}).get("contacts", [])}
        sites = [{"key": "riverside", "name": "Riverside Cancer Center", "short": "Riverside", "kind": "synthetic"}] + \
                [{"key": str(r), "name": top[str(r)]["facility"], "short": short.get(str(r)) or top[str(r)]["facility"][:18], "kind": "public"} for r in sorted(map(int, top))]
        run["stage3"] = {"requirements": qd.get("requirements", []), "questionnaire": qd["questionnaire"], "sites": sites,
                         "prefill": {str(s["rank"]): s.get("facts", []) for s in pre} | {"riverside": []},
                         "answers": {str(s["rank"]): s["answers"] for s in pans} | {"riverside": riv["answers"]},
                         # Riverside's files as the agent saw them, so the client page can show each answer's quoted evidence in place
                         "site_docs": {os.path.relpath(os.path.join(d, f), f"{R}/stage3b_riverside/docs"): open(os.path.join(d, f), errors="replace").read()
                                       for d, _, fs in os.walk(f"{R}/stage3b_riverside/docs") for f in sorted(fs)}}
    if passed("4"):
        ds = json.load(open(f"{R}/stage4/decisions.json"))["decisions"]
        for x in ds: x["kind"] = "synthetic" if x["site_key"] == "riverside" else "public"
        run["stage4"] = {"decisions": ds}
    os.makedirs("app/runs", exist_ok=True)
    save("app/runs/linker-mm3.json", run)
    print("built app/runs/linker-mm3.json with", [k for k in run if k.startswith("stage")])

if __name__ == "__main__":
    globals()[sys.argv[1]]()
