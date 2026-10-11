<!-- LINKER-MM3 end-to-end run. Sent 2026-10-11T08:48Z as a follow-up message to the stage-1 sponsor agent. -->

Stages 3a and 3b are done. Now stage 4, the last one: review what came back and draft a decision for each site. A human approves every decision before anything is sent.

You now work in /home/mihir/hackru/startup/runs/linker-mm3/stage4/ (read only files in this folder). It contains:
- questionnaire.json: your requirements and questions.
- public_prefill.json and public_answers.json: the sponsor-side public pre-fill for your 12 sites (by rank). Their questionnaires aren't back yet, so every question is open.
- riverside_answers.json: a completed questionnaire from Riverside Cancer Center (Dayton, OH), a 13th site that responded (site_key "riverside"). Its NOTE entries are things the site flagged itself.

For each of the 13 sites, decide one of:
- select: meets everything known, nothing blocking;
- conditional: selectable once specific fixable items are resolved;
- clarify: can't judge yet because key answers are open;
- reject: a requirement it can't meet.
Base every decision only on the answers and pre-fill. Give reasons citing the question or fact behind each one. Draft short follow-up questions for open or concerning items. Mark nothing as sent.

Output: decisions.json in this folder, as
{"decisions": [{"site_key": "<rank as a string, or 'riverside'>", "site": "<name>", "decision": "select|conditional|clarify|reject", "reasons": ["..."], "follow_ups": ["..."], "cites": ["Q6", "prefill: FACT accreditation", "NOTE: ..."], "status": "pending_approval"}]}
- Include 13 entries.

Reply in 3 lines: the decision counts, the hardest call, and anything unsure.
