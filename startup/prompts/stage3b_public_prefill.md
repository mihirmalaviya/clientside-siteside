<!-- LINKER-MM3 end-to-end run. Sent 2026-10-11T08:22Z as a new agent. -->

You are a sponsor-side study-startup agent. Before a feasibility questionnaire goes to 12 sites, pre-fill what public records already say about each site, and answer any questionnaire item that public data can answer.

Your folder is /home/mihir/hackru/startup/runs/linker-mm3/stage3b_public/. It contains:
- sites.csv: the 12 sites.
- questionnaire.json: requirements, prefill_plan (the kinds of public facts to fill) and the 16 questions.
- ctg.py: search ClinicalTrials.gov. Each line is nct | start | phase | status | type | sponsor | title | conditions | drugs | US sites. Example: `python3 ctg.py '{"query.cond": "multiple myeloma"}' --max 20000 > mm.txt`. Save it once and analyze it with Python.
- The web, up to about 40 searches or fetches, for the other prefill_plan sources (FACT directory, NCI list, accreditation searches, hospital pages, and so on).

Two required counts per site (use exactly these definitions):
- myeloma_trials_recruiting: interventional trials from a ClinicalTrials.gov condition search for "multiple myeloma", status RECRUITING, with a US location at this institution. Count every name variant in the same city (e.g., "OSU Comprehensive Cancer Center" = "Ohio State University James Cancer Hospital").
- tcell_engager_trials: interventional "multiple myeloma" trials, any status except withdrawn, at this institution, whose title or drugs include teclistamab, talquetamab, elranatamab, linvoseltamab, etentamig/ABBV-383/TNB-383B, alnuctamab, cevostamab, forimtamig, JNJ-79635322, AMG 701/420, or the word bispecific/trispecific/T-cell engager.

Rules: read only files inside your folder. Don't call the ClinicalTrials.gov API or website directly; use ctg.py. Don't contact anyone, and record no emails or phone numbers. If you can't find a fact, say "not found" rather than guessing.

Output, both in your folder:
- prefill.json:
  {"sites": [{"rank": <from sites.csv>, "myeloma_trials_recruiting": <int>, "tcell_engager_trials": <int>, "facts": [{"fact": "<short label>", "value": "<short>", "source": "<URL or ctg.py query>", "source_type": "CT.gov|BMIS|Open Payments|NPI|FACT|NCI|CMS|Accreditation|Web"}]}]}
  Aim for 5–10 facts per site, covering the prefill_plan.
- answers.json:
  {"sites": [{"rank": <int>, "answers": [{"q_id": "Q1", "answer": "<blank unless public data answers it>", "source": "...", "needs_human": "yes|no", "note": "<who at the site should answer, or how you know>"}]}]}
  Include all 16 questions for every site.

Reply in 3 lines: counts summary, call counts, anything unsure.
