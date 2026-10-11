#!/usr/bin/env python3
"""Robustness check for the demo page: python3 test_run.py [app/runs/linker-mm3.json]
- run.json has the fields each stage view reads
- every stage shown passed its gate
- the page code holds no data of its own (no NCT IDs, no people)
- every PI on screen appears in the agent's stage-2 output; every decision site exists in stage 3
"""
import json, re, sys

run = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "app/runs/linker-mm3.json"))
need = {"stage1": {"sites": ["rank", "facility", "city", "state", "score", "reason", "past_trials", "lat", "lon", "real"]},
        "stage2": {"contacts": ["rank", "facility", "pi", "alts", "route", "confidence", "evidence", "criteria", "bmis_latest", "bmis_active"]},
        "stage3": {"questionnaire": ["id", "question", "format"], "sites": ["key", "name", "kind"]},
        "stage4": {"decisions": ["site_key", "site", "decision", "reasons", "follow_ups", "cites", "status"]}}
gate_of = {"stage1": ["1"], "stage2": ["2"], "stage3": ["3a", "3b"], "stage4": ["4"]}
for st, lists in need.items():
    if st not in run:
        print(f"{st}: not run (page shows 'not run')"); continue
    for g in gate_of[st]:
        assert run["gates"][g]["passed"], f"{st} shown but gate {g} did not pass"
    for lst, fields in lists.items():
        rows = run[st][lst]
        assert rows, f"{st}.{lst} empty"
        for r in rows:
            miss = [f for f in fields if f not in r]
            assert not miss, f"{st}.{lst} row missing {miss}: {str(r)[:80]}"
    print(f"{st}: ok")
if "stage3" in run:
    keys = {s["key"] for s in run["stage3"]["sites"]}
    assert all(k in run["stage3"]["answers"] for k in keys), "a stage-3 site has no answers"
    if "stage4" in run:
        assert all(d["site_key"] in keys for d in run["stage4"]["decisions"]), "decision for unknown site"
        assert all(d["status"] == "pending_approval" for d in run["stage4"]["decisions"]), "something marked sent"
code = open("app/app.js").read()
assert not re.search(r"NCT\d{8}", code), "app.js contains a trial ID"
if "stage2" in run:
    for c in run["stage2"]["contacts"]:
        assert c["pi"].split()[-1] not in code, f"app.js mentions {c['pi']}"
print("all checks passed")
