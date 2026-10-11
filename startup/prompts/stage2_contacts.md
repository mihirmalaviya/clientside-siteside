<!-- LINKER-MM3 end-to-end run. Stage 2 rerun (v2) with explicit contact criteria; sent as a new agent. v1 prompt: runs/linker-mm3/attempts/stage2_v1/prompt.md -->

You are a pharma sponsor's study-startup agent. The sponsor has picked 12 US sites for a new trial (brief.md). For each site, find who the sponsor should contact: the best investigator to lead this trial there, and the site's sponsor-facing research office. Work however you think is best.

Your folder is /home/mihir/hackru/startup/runs/linker-mm3/stage2/. It contains:
- sites.csv: the 12 sites (rank, facility, city, state).
- brief.md: the trial, as the sponsor sees it.
- ctg.py: search ClinicalTrials.gov, current to today. Each line is nct | start | phase | status | type | sponsor | title | conditions | drugs | US sites. Add `--pi` to see each site's listed PI (only recruiting trials list them). Example: `python3 ctg.py '{"query.cond": "multiple myeloma"}' --pi --max 20000 > mm.txt`. Save big results to files in your folder and analyze them with Python.
- bmis.py: FDA BMIS, every Form 1572 filed by US clinical investigators, 2018–2026. `python3 bmis.py Lastname [First]`, or `python3 bmis.py --city Atlanta GA` for everyone who filed in a city since 2024.
- The web, up to about 50 searches or fetches: CMS Open Payments (openpaymentsdata.cms.gov datastore API; research payments name the PI of industry-paid trials, including finished ones), the NPI Registry (https://npiregistry.cms.hhs.gov/api/?version=2.1&...), PubMed, and faculty and research-office pages.

How to choose the investigator. The best contact is the person most likely to say yes and enroll patients, not the most senior one. Judge candidates on these criteria, in this order:
1. Still there. They filed a 1572 at this site in the last 18 months (bmis.py), and the NPI Registry or faculty page doesn't contradict it. Anyone who fails this is out, however strong otherwise.
2. Same drug or class. They led this sponsor's earlier trials of this drug or its relatives (linvoseltamab, REGN5459, odronextamab) at this site, or trials of other T-cell-engaging bispecifics in myeloma. Open Payments and ctg.py --pi show this.
3. Same kind of trial. They have led relapsed/refractory myeloma trials of this phase or earlier at this site, or are lead or senior author on such results (PubMed).
4. Has room. Count the recruiting myeloma trials they are PI on at this site now (ctg.py --pi). Many competing trials is a mild minus; use it to separate close candidates.
Seniority (program chief) only breaks remaining ties. If your pick meets neither criterion 2 nor 3, set route to "office": the sponsor should go to the research office first and let it name the investigator. If the site runs industry trials through a research network, also route to "office" and name the network in the note.

The office contact is the site's sponsor-facing clinical trials office or industry/feasibility intake page, not the patient-facing trial search and not a named person. Open every URL you report and make sure it loads and is the right kind of page.

Rules. Breaking them invalidates the test:
1. Read only files inside your folder. Other files under /home/mihir/hackru hold the answers. Don't read ctg_config.json or try to reverse its hash.
2. Do not try to identify this specific trial or look up anything that lists its sites or investigators. That rules out its registry record, its name or acronym, its publications, and press releases about it.
3. Don't call the ClinicalTrials.gov API or website directly; use ctg.py.
4. Never contact anyone and draft no messages. Record no email addresses or phone numbers; names, offices and public page URLs only.

Output: contacts.json in your folder, as
{"contacts": [{"rank": <from sites.csv>, "facility": "...", "short": "<short name, e.g. MSK>", "city": "...", "state": "<full state name>",
  "pi": "<full name>", "alts": ["<2nd choice>", "<3rd choice>"], "route": "pi|office", "confidence": 0.0-1.0,
  "evidence": "<one line: why this person>", "note": "<optional: moved, network, handover, etc.>",
  "criteria": {
    "still_there": {"met": "yes|no|unknown", "finding": "<short, e.g. 1572 at this site 2026-08>", "source": "BMIS|NPI|Web"},
    "same_drug":   {"met": "yes|no|unknown", "finding": "<short>", "source": "Open Payments|CT.gov|Web"},
    "same_kind":   {"met": "yes|no|unknown", "finding": "<short>", "source": "CT.gov|PubMed|Web"},
    "has_room":    {"met": "yes|no|unknown", "competing": <int>, "finding": "<short>", "source": "CT.gov"}},
  "contact_url": "<research office page>", "contact_domain": "<e.g. mskcc.org>"}]}
- Include one entry per site, 12 total.

Reply in 3 lines: your approach, call counts (web and ctg.py), and anything unsure.
