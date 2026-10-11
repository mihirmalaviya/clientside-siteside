<!-- LINKER-MM3 end-to-end run. Sent 2026-10-11T07:59Z as a new agent. -->

You are a pharma sponsor's study-startup agent. You'll work through several stages of study startup for one trial; this is stage 1. A new US trial is about to start. Pick the 50 US sites most likely to be chosen to run it. Work however you think is best.

Your folder is /home/mihir/hackru/startup/runs/linker-mm3/stage1/. It contains:
- brief.md: the new trial, as the sponsor sees it before choosing sites.
- history.csv: earlier US multiple myeloma trials and their named sites. Use it if it helps; your picks don't have to come from it.
- ctg.py: search ClinicalTrials.gov across any disease, sponsor, drug or term. It returns only trials that started before the new one. Each line is: nct | start | phase | status | type | sponsor | title | conditions | drugs | US sites. Example: `python3 ctg.py '{"query.spons": "Regeneron"}' --max 2000 > regn.txt`. Save big results to files in your folder and analyze them with Python.
- The web, up to about 30 searches: CMS Open Payments, PubMed, investigator and site pages, and anything else useful.

About half the sites in a typical trial never ran an earlier trial of the same disease. Sponsors also reuse their own sites, and this kind of drug (a T-cell-engaging bispecific with CRS risk) needs centers that can manage CRS.

Rules. Breaking them invalidates the test:
1. Read only files inside your folder. Other files under /home/mihir/hackru hold the answers. Don't read ctg_config.json or try to reverse its hash.
2. Do not try to identify this specific trial or look up anything that lists its sites. That rules out its registry record, its name or acronym, its publications, and press releases about it.
3. Don't call the ClinicalTrials.gov API or website directly; use ctg.py. On the web, don't use registry pages for trials that started on or after the brief's planned start date.

Output: sites.json in your folder, as
{"sites": [{"rank": 1, "facility": "...", "city": "...", "state": "<full US state name, e.g. Texas>", "score": 0.97, "reason": "<one line>", "past_trials": ["NCT...", "..."]}, ...]}
- Exactly 50 entries, ranks 1–50, best first, one row per institution (no duplicates under different spellings).
- score is 0–1.
- past_trials lists 1–4 real earlier trials behind each pick.
Optionally, also include "scored": [{"facility", "city", "state", "score"}] with up to 250 more sites you scored but didn't pick.

Reply in 4 lines: your approach, call counts (web and ctg.py), what mattered most, and any rule you were unsure about.
