#!/usr/bin/env python3
"""
Phase 2 test (contact the right person): for each site of a recruiting trial, can the agent
name the principal investigator (PI) that ClinicalTrials.gov lists for it?

  python3 contact_test.py prep    # writes agent_runs/contacts/t<hash>/{brief.md,sites.csv,ctg.py,ctg_config.json}
  (the agent writes contacts.csv: site_id,pi_1,pi_2,pi_3,npi_verified,contact_route_url,contact_domain,reason)
  python3 contact_test.py score [file]   # top-1 / top-3 PI match vs the real PI and a no-AI baseline,
                                         # plus contact_domain vs the real site coordinator's email domain
v1 (contacts_v1_hidden_sponsor.csv) hid the sponsor and drug; v2 gives the full sponsor view.

Baseline (no AI): the PI listed most often at the same site in other myeloma trials.
"""
import csv, hashlib, json, os, re, shutil, sys
from collections import Counter
from datetime import date
import backtest as b, agent_test as a

TARGET = "NCT05651932"    # K36 Therapeutics, recruiting; every US site lists a PI
D = "agent_runs/contacts/t" + hashlib.sha256(TARGET.encode()).hexdigest()[:6]
DEGREES = {"md", "phd", "do", "mph", "ms", "msc", "mba", "facp", "dr", "mbbs", "frcpc", "jr", "ii", "iii"}

def person(name):
    """'Thomas G. Martin, MD' -> ('martin', 't'). ponytail: no nickname handling (Bill vs William)."""
    words = [w for w in re.sub(r"[^a-z ]", " ", name.lower()).split() if w not in DEGREES]
    return (words[-1], words[0][0]) if len(words) >= 2 else None

def pis(loc):
    return [c.get("name", "") for c in loc.get("contacts", []) or [] if c.get("role") == "PRINCIPAL_INVESTIGATOR"]

def us_sites(ps):
    return [l for l in ps.get("contactsLocationsModule", {}).get("locations", []) or []
            if l.get("country") == "United States" and l.get("facility")]

def load():
    raw = {s["protocolSection"]["identificationModule"]["nctId"]: s["protocolSection"] for s in b.download()}
    return raw, us_sites(raw[TARGET])

def prep():
    raw, sites = load()
    os.makedirs(D, exist_ok=True)
    shutil.copy("ctg.py", D)
    # "now" framing: other current trials are fair game; only the target is hidden
    json.dump({"cutoff": str(date.today()), "hidden": hashlib.sha256(TARGET.encode()).hexdigest()},
              open(f"{D}/ctg_config.json", "w"))
    with open(f"{D}/sites.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["site_id", "facility", "city", "state"])
        for i, l in enumerate(sites, 1):
            w.writerow([i, l["facility"], l.get("city", ""), l.get("state", "")])
    ps = raw[TARGET]
    ivs = "; ".join(v.get("name", "") for v in ps.get("armsInterventionsModule", {}).get("interventions", []))
    with open(f"{D}/brief.md", "w") as f:
        f.write(f"# New trial (sponsor's view)\n\n- Sponsor: {ps['sponsorCollaboratorsModule']['leadSponsor']['name']}\n"
                f"- Phase 1, adults with relapsed/refractory multiple myeloma\n- Arms: {ivs}\n\n"
                f"## Summary\n{ps.get('descriptionModule', {}).get('briefSummary', '')}\n\n"
                "The sponsor has already chosen the sites in sites.csv and needs the right person to contact at each.\n")
    print(f"Wrote {D} ({len(sites)} sites)")

def baseline(raw, loc):
    """Most-listed PI at the same site (city+state+similar name) across other myeloma trials."""
    key = b.site_key(loc)
    c = Counter()
    for nct, ps in raw.items():
        if nct == TARGET:
            continue
        for l in us_sites(ps):
            if pis(l) and a.fuzzy_hits([(l["facility"], l.get("city", ""), l.get("state", ""))], {key}):
                c.update(p for p in map(person, pis(l)) if p)
    return [p for p, _ in c.most_common(3)]

def domain(s):
    """'crc@med.miami.edu' or 'https://www.sylvester.org/x' -> 'miami.edu' / 'sylvester.org'"""
    host = re.sub(r"^https?://", "", s.strip().lower()).split("/")[0].split("@")[-1]
    return ".".join(host.split(".")[-2:])

def score(file="contacts.csv"):
    raw, sites = load()
    rows = {r["site_id"]: r for r in csv.DictReader(open(f"{D}/{file}"))}
    tot = Counter()
    print(f"{'site':40} {'real PI':22} {'base@1':6} {'base@3':6} {'ai@1':5} {'ai@3':5} route npi")
    for i, l in enumerate(sites, 1):
        truth = {person(n) for n in pis(l)} - {None}
        base = baseline(raw, l)
        r = rows.get(str(i), {})
        ai = [person(r[k]) for k in ("pi_1", "pi_2", "pi_3") if r.get(k)]
        res = {"base@1": bool(base[:1] and base[0] in truth), "base@3": bool(set(base) & truth),
               "ai@1": bool(ai[:1] and ai[0] in truth), "ai@3": bool(set(ai) & truth)}
        real_domains = {domain(c["email"]) for c in l.get("contacts", []) or [] if c.get("email")}
        res["route"] = bool(r.get("contact_domain") and domain(r["contact_domain"]) in real_domains)
        tot["has_email"] += bool(real_domains)
        tot.update(k for k, v in res.items() if v)
        print(f"{l['facility'][:40]:40} {', '.join(pis(l))[:22]:22} " +
              " ".join(f"{'Y' if res[k] else '.':{len(k)}}" for k in res) + f" {r.get('npi_verified', '')}")
    n = len(sites)
    print(f"\nOf {n} sites: baseline top-1 {tot['base@1']}, top-3 {tot['base@3']} | "
          f"agent top-1 {tot['ai@1']}, top-3 {tot['ai@3']} | "
          f"contact domain matches real coordinator's: {tot['route']} of {tot['has_email']}")

if __name__ == "__main__":
    {"prep": prep, "score": score}[sys.argv[1]](*sys.argv[2:])
