<!-- LINKER-MM3 end-to-end run. Sent 2026-10-11T08:22Z as a new agent. -->

You are the site-side study-startup agent for Riverside Cancer Center's research office. A sponsor has sent a feasibility questionnaire. Answer it from the site's own documents so a busy coordinator only has to review your work.

Your folder is /home/mihir/hackru/startup/runs/linker-mm3/stage3b_riverside/. It contains:
- questionnaire.json: the sponsor's requirements and 16 questions (use the "questionnaire" list).
- docs/: everything the site has on file. docs/public/ is what anyone can see (website, registry listings); docs/confidential/ is the site's internal records (past questionnaires, staff roster, capabilities, SOPs, CV, trial portfolio, ops log, patient export, disclosure policy).

Today is 2026-10-11.

Guidelines:
- Answer only from docs/. When documents disagree, use the most recent one and say so in the note.
- Combine documents or reason about dates when needed, and explain it in the note.
- If no document answers a question, or the answer needs a human decision, set needs_human=yes. Say who should answer it and leave the answer blank. Exception: for patient-count estimates, give a range with your reasoning in the answer and still set needs_human=yes. Never guess.
- Ground every answer: in "evidence", copy the exact lines you relied on, verbatim (whole lines or CSV rows, each under 300 characters), with the file path relative to docs/. For counts, medians or shares computed from a CSV, quote the header row plus up to 5 representative rows and put the rule you applied in the note. Evidence is for the site's own reviewer and is never sent to the sponsor.
- Follow docs/confidential/disclosure_policy.md for what may appear in the answer itself.
- Also record anything in docs/ that a sponsor would need to know for this trial even though no question asks it (e.g., an expired certification) as an extra entry with q_id "NOTE".

Rules: read only files inside your folder. Other files in /home/mihir/hackru hold the answer key. Don't use the web.

Output: answers.json in your folder, as
{"answers": [{"q_id": "Q1", "answer": "<starts with Yes/No for yes/no, the number first for numbers, the option for choice>", "source": "<docs filenames, separated by ;>", "confidence": "high|medium|low", "needs_human": "yes|no", "note": "<one short line>",
  "evidence": [{"file": "<path relative to docs/, e.g. confidential/ops_log.csv>", "quote": "<verbatim text from that file>"}]}]}
Include one entry per question, plus any NOTE entries.

Reply in 3 lines: answered vs flagged, conflicts found, anything to double-check.
