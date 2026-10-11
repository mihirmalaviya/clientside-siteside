#!/usr/bin/env python3
"""
Phase 3 test (feasibility questionnaire): can the site agent answer a new sponsor questionnaire
from the site's own documents: correctly, with sources, flagging what it can't know?

  python3 site_test.py prep           # writes agent_runs/site/riverside/questionnaire.csv
  (the agent writes answers.csv: q_id,answer,source,confidence,needs_human,note)
  python3 site_test.py score [file]   # agent (default answers.csv) vs the copy-last-answer baseline

The site, its people and documents are fictional (docs/ was written by hand with planted traps):
  stale  - an older questionnaire disagrees with a newer document; the newest must win
  cross  - needs combining documents (e.g. roster dates vs today)
  flag   - no document answers it; the right move is needs_human=yes (Q10: a range with reasoning)
Answer key is below, outside the agent's folder.
"""
import csv, difflib, glob, os, re, sys

D = "agent_runs/site/riverside"
TODAY = "2026-10-11"

# q_id: (question, type, answer, trap)   types: yesno | number (answer, tolerance) | text (keywords) | flag
KEY = {
 "Q1":  ("Is there an intensive care unit on site?", "yesno", "yes", ""),
 "Q2":  ("Can the site admit patients for inpatient step-up dosing?", "yesno", "yes", "stale"),
 "Q3":  ("How many inpatient beds can be reserved for step-up dosing admissions?", "number", (4, 0), ""),
 "Q4":  ("Is tocilizumab kept on site in sufficient quantity for CRS management?", "yesno", "yes", ""),
 "Q5":  ("Does the site have a written CRS/ICANS management SOP?", "yesno", "yes", ""),
 "Q6":  ("How many T-cell engager (bispecific antibody) trials has the site participated in?", "number", (2, 0), "cross"),
 "Q7":  ("How many patients did the site enroll in its most recent completed bispecific antibody trial?", "number", (7, 0), ""),
 "Q8":  ("How many trials currently enrolling relapsed/refractory myeloma patients at the site would compete with this study?", "number", (2, 0), "cross"),
 "Q9":  ("Approximately how many relapsed/refractory myeloma patients does the site see per year?", "number", (70, 0), "stale"),
 "Q10": ("How many patients per year at the site would meet this trial's eligibility criteria?", "flag", None, "flag"),
 "Q11": ("How many clinical research coordinators support hematologic malignancy trials?", "number", (4, 0), "stale"),
 "Q12": ("Does the site have a dedicated investigational drug pharmacist?", "yesno", "yes", ""),
 "Q13": ("Are GCP training certificates current for all investigators (PI and sub-investigators)?", "yesno", "no", "cross"),
 "Q14": ("How many years has the PI been conducting industry-sponsored trials?", "number", (12, 1), "cross"),
 "Q15": ("How many temperature-monitored -80C freezers are available?", "number", (2, 0), "stale"),
 "Q16": ("Is the local laboratory both CLIA certified and CAP accredited?", "yesno", "yes", ""),
 "Q17": ("Is PET-CT available on site?", "yesno", "no", ""),
 "Q18": ("Can MRD testing by NGS be performed locally?", "yesno", "no", ""),
 "Q19": ("Can bone marrow aspirates/biopsies be performed on site?", "yesno", "yes", ""),
 "Q20": ("Is 24/7 hematology on-call coverage available?", "yesno", "yes", ""),
 "Q21": ("What is the median local IRB approval time, in weeks?", "number", (6, 0), "stale"),
 "Q22": ("Does the site accept a central IRB?", "yesno", "yes", ""),
 "Q23": ("What is the median contract and budget execution time, in weeks?", "number", (10, 0), "stale"),
 "Q24": ("What is the institutional indirect cost (overhead) rate, in percent?", "number", (28, 0), "stale"),
 "Q25": ("Which EDC systems do site staff have experience with?", "text", ["rave", "veeva"], ""),
 "Q26": ("Can study monitors get remote read-only EMR access?", "yesno", "yes", ""),
 "Q27": ("What is the site's screen failure rate in hematology trials, in percent?", "number", (30, 0), ""),
 "Q28": ("Does the site provide patient lodging support near the hospital?", "yesno", "yes", ""),
 "Q29": ("Can informed consent be conducted in Spanish with a certified translated form?", "flag", None, "flag"),
 "Q30": ("Will the PI commit to this study, and how many patients will the site commit to enroll?", "flag", None, "flag"),
 "Q31": ("Has the site had FDA inspection findings (Form 483) in the last 5 years?", "flag", None, "flag"),
 "Q32": ("What is the median time from site initiation visit to first patient enrolled?", "flag", None, "flag"),
}

def prep():
    with open(f"{D}/questionnaire.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["q_id", "question"])
        for q, (text, *_ ) in KEY.items():
            w.writerow([q, text])
    with open(f"{D}/brief.md", "w") as f:
        f.write(f"# Feasibility request (received {TODAY})\n\nSponsor study: Phase 3, BCMAxCD3 bispecific antibody "
                "(step-up dosing, CRS risk) vs standard combination therapy in relapsed/refractory multiple myeloma, "
                "patients with 3+ prior lines, triple-class exposed, no prior BCMA therapy, ECOG 0-1.\n"
                "Please answer questionnaire.csv for Riverside Cancer Center.\n")
    print(f"Wrote {D}/questionnaire.csv ({len(KEY)} questions) and brief.md")

def first_number(s):
    m = re.search(r"\d+(?:\.\d+)?", s.replace(",", ""))
    return float(m.group()) if m else None

def correct(qtype, key, ans):
    a = ans.strip().lower()
    if qtype == "yesno":
        return a.startswith(key)
    if qtype == "number":
        n = first_number(a)
        return n is not None and abs(n - key[0]) <= key[1]
    if qtype == "text":
        return all(k in a for k in key)
    return False

def baseline_answers():
    """No AI: copy the answer of the most similar question in any past questionnaire (like pre-fill tools).
    ponytail: difflib similarity >= 0.5 counts as a match; it never flags anything."""
    past = []
    for p in sorted(glob.glob(f"{D}/docs/past_questionnaire_*.md")):
        for q, a in re.findall(r"Q: (.+)\nA: (.+)", open(p).read()):
            past.append((q, a, os.path.basename(p)))
    out = {}
    for q, (text, *_ ) in KEY.items():
        best = max(past, key=lambda x: difflib.SequenceMatcher(None, text.lower(), x[0].lower()).ratio())
        if difflib.SequenceMatcher(None, text.lower(), best[0].lower()).ratio() >= 0.5:
            out[q] = {"answer": best[1], "source": best[2], "needs_human": "no"}
    return out

def cited_ok(qtype, ans, source):
    """Cited file(s) exist; for numbers, the number appears in one of them (or in a date, for derived ones)."""
    files = [os.path.join(D, "docs", s.strip()) for s in re.split(r"[;,|]", source) if s.strip()]
    if not files or not all(os.path.exists(f) for f in files):
        return False
    if qtype == "number":
        n = first_number(ans)
        return n is not None and any(re.search(rf"\b{int(n)}\b", open(f).read()) for f in files)
    return True

def evaluate(name, rows):
    s = {"answerable": 0, "answered": 0, "right": 0, "flags": 0, "flagged": 0, "fabricated": 0,
         "stale": 0, "stale_right": 0, "cited": 0}
    wrong = []
    for q, (text, qtype, key, trap) in KEY.items():
        r = rows.get(q)
        human = bool(r) and r.get("needs_human", "").strip().lower().startswith("y")
        if qtype == "flag":
            s["flags"] += 1
            if human: s["flagged"] += 1
            elif r and r.get("answer", "").strip(): s["fabricated"] += 1; wrong.append(f"{q} made up: {r['answer'][:50]}")
            continue
        s["answerable"] += 1
        s["stale"] += trap == "stale"
        if not r or human or not r.get("answer", "").strip():
            continue
        s["answered"] += 1
        ok = correct(qtype, key, r["answer"])
        s["right"] += ok
        s["stale_right"] += ok and trap == "stale"
        s["cited"] += ok and cited_ok(qtype, r["answer"], r.get("source", ""))
        if not ok: wrong.append(f"{q} wrong ({trap or 'plain'}): {r['answer'][:50]}  [key: {key}]")
    p = lambda a, b: f"{a}/{b} ({100*a/b:.0f}%)" if b else "0/0"
    print(f"\n## {name}")
    print(f"Coverage (answered of {s['answerable']} answerable): {p(s['answered'], s['answerable'])}")
    print(f"Accuracy (right of answered): {p(s['right'], s['answered'])}")
    print(f"Stale traps right: {p(s['stale_right'], s['stale'])}")
    print(f"Honesty (unanswerable flagged): {p(s['flagged'], s['flags'])}, made-up answers: {s['fabricated']}")
    print(f"Right answers with a valid citation: {p(s['cited'], s['right'])}")
    for w in wrong: print("  -", w)

def score(file="answers.csv"):
    evaluate("Baseline: copy most similar past answer", baseline_answers())
    if os.path.exists(f"{D}/{file}"):
        evaluate("Site agent", {r["q_id"]: r for r in csv.DictReader(open(f"{D}/{file}"))})

if __name__ == "__main__":
    {"prep": prep, "score": score}[sys.argv[1]](*sys.argv[2:])
