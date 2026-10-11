<!-- LINKER-MM3 end-to-end run. Sent 2026-10-11T08:03Z as a follow-up message to the stage-1 sponsor agent. -->

Stage 1 passed. Now stage 2: the sponsor has picked your top 12 sites. For each one, find the right person to contact: the principal investigator most likely to lead this trial there, plus the site's sponsor-facing research office.

You now work in /home/mihir/hackru/startup/runs/linker-mm3/stage2/ (read only files in this folder from now on). It contains:
- sites.csv: your top 12.
- brief.md: the trial.
- ctg.py: now current up to today. Add `--pi` to see site PIs; only recruiting trials list them.
- bmis.py: FDA BMIS (Form 1572 filings, 2018–2026). `python3 bmis.py Lastname [First]`, or `python3 bmis.py --city Atlanta GA` for everyone who filed in a city since 2024.
- The web, up to about 50 searches or fetches: CMS Open Payments (openpaymentsdata.cms.gov datastore API; research payments name PIs of finished industry trials), the NPI Registry (https://npiregistry.cms.hhs.gov/api/?version=2.1&...), PubMed, and faculty and research-office pages.

Things likely to matter: who led Regeneron's earlier linvoseltamab, REGN5459 and odronextamab work at each site; who leads bispecific and early-phase myeloma trials; who has moved; and whether the site goes through a research network.

Rules:
- The same rules as before apply. Never contact anyone, and record no emails or phone numbers.
- Open every contact URL you report and make sure it loads and is a sponsor-facing or research-office page.

Output: contacts.json in this folder, as
{"contacts": [{"rank": <from sites.csv>, "facility": "...", "short": "<short name, e.g. MSK>", "city": "...", "state": "<full state name>", "pi": "<full name>", "alts": ["...", "..."], "confidence": 0.0-1.0, "evidence": "<one line, main evidence>", "note": "<optional, e.g. 'Moved from X in 2025'>", "checks": [{"source": "CT.gov|Open Payments|NPI|BMIS|Web", "status": "confirms|changed|none", "finding": "<short>"}], "contact_url": "...", "contact_domain": "..."}]}
- Include one entry per site, 12 total.
- checks must have exactly one entry for each of the 5 sources.

Reply in 3 lines: your approach, call counts, and anything unsure.
