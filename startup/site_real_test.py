#!/usr/bin/env python3
"""
Phase 3 on a REAL hospital: Levine Cancer Institute (Atrium Health), Charlotte, NC.
The answer key is computed by fixed rules from ClinicalTrials.gov (downloaded today), not written by hand.
Questions public data can't answer (staff, IRB time, freezers, overhead) must be flagged.

  python3 site_real_test.py prep    # writes agent_runs/site/levine/{questionnaire.csv,brief.md}
  python3 site_real_test.py key     # prints the computed answer key (don't show the agent)
  python3 site_real_test.py score   # scores agent_runs/site/levine/answers.csv
"""
import csv, re, sys
from collections import Counter
import backtest as b
from site_test import correct

D = "agent_runs/site/levine"
SINCE = "2021-10-11"
SITE = re.compile(r"levine|atrium|carolinas (medical|health)", re.I)   # this institution's name variants
BISPECIFIC = re.compile(r"teclistamab|talquetamab|elranatamab|linvoseltamab|etentamig|abbv-383|tnb-383b|alnuctamab|"
                        r"cevostamab|forimtamig|jnj-79635322|jnj-5322|pf-06863135|regn5458|amg 701|amg 420|"
                        r"bispecific|trispecific|t[- ]cell engag|bcma\s*[x*×]\s*cd3", re.I)
BCMA_CART = re.compile(r"cilta-?cel|ciltacabtagene|jnj-68284528|ide-cel|idecabtagene|bb2121|anito-?cel|anitocabtagene|cb-011", re.I)

def site_trials():
    """Interventional myeloma trials (any status but withdrawn) with a named Charlotte, NC location of this site."""
    out = []
    for s in b.download():
        ps = s["protocolSection"]
        st = ps["statusModule"]
        if ps["designModule"].get("studyType") != "INTERVENTIONAL" or st["overallStatus"] == "WITHDRAWN":
            continue
        locs = [l for l in ps.get("contactsLocationsModule", {}).get("locations", []) or []
                if l.get("city") == "Charlotte" and l.get("state") == "North Carolina" and SITE.search(l.get("facility", ""))]
        if locs:
            text = " ".join([ps["identificationModule"].get("briefTitle", "")] +
                            [i.get("name", "") for i in ps.get("armsInterventionsModule", {}).get("interventions", [])])
            out.append({"nct": ps["identificationModule"]["nctId"], "status": st["overallStatus"],
                        "start": st.get("startDateStruct", {}).get("date", ""), "text": text,
                        "sponsor": ps["sponsorCollaboratorsModule"]["leadSponsor"],
                        "pis": [c["name"] for l in locs for c in l.get("contacts", []) or [] if c.get("role") == "PRINCIPAL_INVESTIGATOR"]})
    return out

def key():
    t = site_trials()
    rec = [x for x in t if x["status"] == "RECRUITING"]
    bis = [x for x in t if BISPECIFIC.search(x["text"])]
    ind = Counter(x["sponsor"]["name"] for x in t if x["sponsor"].get("class") == "INDUSTRY")
    tol = lambda n: (n, max(2, round(0.15 * n)))      # site-name and drug-name judgment calls
    return {
     "L1": ("How many interventional multiple myeloma trials has the site participated in (any status, excluding withdrawn)?", "number", tol(len(t))),
     "L2": (f"How many of those started on or after {SINCE}?", "number", tol(sum(x["start"] >= SINCE for x in t))),
     "L3": ("How many interventional myeloma trials is the site currently recruiting for?", "number", tol(len(rec))),
     "L4": ("Has the site participated in a myeloma trial of a T-cell-engaging bispecific (or trispecific) antibody?", "yesno", "yes" if bis else "no"),
     "L5": ("How many such T-cell-engaging antibody myeloma trials has the site participated in?", "number", tol(len(bis))),
     "L6": ("Has the site participated in a BCMA CAR-T myeloma trial?", "yesno", "yes" if any(BCMA_CART.search(x["text"]) for x in t) else "no"),
     "L7": ("Name up to 3 investigators listed as principal investigator at the site on currently recruiting myeloma trials.", "names",
            sorted({p for x in rec for p in x["pis"]})),
     "L8": ("Which industry sponsor has run the most myeloma trials at the site?", "text", [ind.most_common(1)[0][0].split()[0].lower()]),
     "L9": ("How many clinical research coordinators support myeloma trials at the site?", "flag", None),
     "L10": ("What is the site's median IRB approval time?", "flag", None),
     "L11": ("How many -80C research freezers does the site have?", "flag", None),
     "L12": ("What is the site's indirect cost (overhead) rate for industry trials?", "flag", None),
    }

def prep():
    k = key()
    with open(f"{D}/questionnaire.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["q_id", "question"])
        for q, (text, *_ ) in k.items(): w.writerow([q, text])
    with open(f"{D}/brief.md", "w") as f:
        f.write("# Feasibility pre-fill from public data\n\nSite: Levine Cancer Institute (Atrium Health), Charlotte, North Carolina.\n"
                "It appears in registries under several names (e.g. 'Levine Cancer Institute', 'Carolinas Medical Center/Levine "
                "Cancer Institute', 'Atrium Health'). Count all of them as this site; ignore unnamed placeholder sites.\n"
                "'Myeloma trial' means a ClinicalTrials.gov study found by a condition search for multiple myeloma.\n")
    print(f"Wrote {D}/questionnaire.csv ({len(k)} questions)")

def last_name(n):
    w = [x for x in re.sub(r"[^a-z ]", " ", n.lower()).split() if x not in {"md", "phd", "do", "ms", "mph", "dr", "facp"}]
    return w[-1] if w else ""

def score():
    k = key()
    rows = {r["q_id"]: r for r in csv.DictReader(open(f"{D}/answers.csv"))}
    right = answered = flagged = made_up = 0
    for q, (text, qtype, ans) in k.items():
        r = rows.get(q, {})
        human = r.get("needs_human", "").lower().startswith("y")
        a = r.get("answer", "")
        if qtype == "flag":
            flagged += human; made_up += (not human and bool(a.strip()))
            print(f"{q:4} flag    {'flagged' if human else 'ANSWERED: ' + a[:60]}")
            continue
        if human or not a.strip():
            print(f"{q:4} {qtype:7} not answered (needs_human)  key={ans}"); continue
        answered += 1
        if qtype == "names":
            truth = {last_name(n) for n in ans}
            got = [last_name(n) for n in re.split(r"[;,]| and ", a) if last_name(n)]
            ok = bool(got) and all(g in truth for g in got[:3])
            print(f"{q:4} names   {'OK ' if ok else 'BAD'} agent={got[:3]} real={sorted(truth)}")
        else:
            ok = correct(qtype, ans, a)
            print(f"{q:4} {qtype:7} {'OK ' if ok else 'BAD'} agent={a[:50]!r} key={ans}")
        right += ok
    n_ans = sum(v[1] != "flag" for v in k.values())
    print(f"\nAnswered {answered}/{n_ans}, right {right}/{answered}; flagged {flagged}/4 unanswerable, made up {made_up}")

if __name__ == "__main__":
    {"prep": prep, "key": lambda: [print(q, v[1], v[2]) for q, v in key().items()], "score": score}[sys.argv[1]]()
