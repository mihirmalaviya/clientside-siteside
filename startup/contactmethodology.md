# Contact methodology: who the sponsor should reach at each site

Stage 2 of the pipeline. The sponsor agent has picked the sites (stage 1). Now it works out who to contact at each one.
Agents draft and humans send: nothing here contacts anyone.

## The problem (Henry's points)

- Contact info goes stale: doctors move or retire, and emails bounce.
- Each site needs two contacts: the doctor, who has to care about the science, and the admin office, which handles budgets and contracts.
- Cold outreach is mostly ignored.

## Two contacts per site

1. **The doctor (investigator)**: the person most likely to say yes **and enroll patients**. This is not the most senior person.
2. **The research office**: the site's sponsor-facing clinical trials office or industry/feasibility intake page. It is an office, not a named person, because offices don't retire. If the site runs industry trials through a research network, the sponsor goes through the network.

## How the doctor is chosen, in order

| # | Criterion | Rule | Public source |
|---|---|---|---|
| 1 | **Still there** | Filed an FDA Form 1572 at this site in the last 18 months, and the NPI Registry / faculty page don't contradict it. **Fail = out**, however strong otherwise. | FDA BMIS (every 1572 filed by US investigators, 2018–2026), NPI Registry, faculty pages |
| 2 | **Same drug or class** | Led this sponsor's earlier trials of this drug or its relatives at this site, or trials of similar drugs (here: other T-cell-engaging bispecifics in myeloma). | CMS Open Payments research payments (name the PI even on finished trials), ClinicalTrials.gov PI lists |
| 3 | **Same kind of trial** | Led trials in the same disease at this phase or earlier at this site, or is lead/senior author on such results. | ClinicalTrials.gov, PubMed |
| 4 | **Has room** | Number of recruiting trials in the disease they lead at this site now. Many = a mild minus, used only to separate close candidates. | ClinicalTrials.gov |
| — | Seniority | Program chief etc. Only breaks remaining ties. | Faculty pages |

**Routing rule:** if the pick meets neither criterion 2 nor 3 (i.e. it rests on seniority alone), route = `office`: the sponsor goes to the
research office first and lets the site name the investigator. Same if the site works through a research network.

**Why this order:** the strongest predictor that someone will take the trial and enroll is that they already ran the same drug at the same
site. Being still there is a filter, not a score: a perfect record is useless if the person left. Why 18 months: BMIS is updated
quarterly and 1572s are filed per trial, so an active investigator can go a year without a new filing; 12 months would wrongly drop
active people.

## What a human gets per site

- One doctor, 2 backups, a confidence score, and one line of evidence.
- Each of the 4 criteria marked yes / no / unknown, with its finding and source.
- The route (doctor or office first) and the research office URL (checked that it loads).
- No emails or phone numbers. A human decides and sends.

## How it's checked (stage 2 gate, fixed before the run in `runs/linker-mm3/gates.json`)

Scripts check the agent's work against the raw data, not against the agent's own claims:

- **Still there**: the gate looks the pick up in BMIS itself (name + city + state). At least 10 of 12 must have a 1572 since 2025-04-11.
- **All 4 criteria reported** for every site.
- **Routing**: every seniority-only pick must be routed to the office.
- **Has room**: the agent's competing-trial count must be within 2 of a script count (recruiting myeloma trials listing that person as PI in that city), for at least 10 of 12.
- **Office URL loads** (no 404/5xx), and **no emails or phone numbers** anywhere in the output.

## Evidence it picks the right person (backtest)

Earlier test (`contact_test.py`, `agent_runs/contacts/t67ec4f`), run with an earlier, less explicit version of these criteria. The agent was given the 17 US sites of a real, finished myeloma trial (K36 Therapeutics), with the trial's own records off limits, and had to name each site's PI. It was scored against the PIs actually listed.

| | Right PI as top pick | Right PI in top 3 |
|---|---|---|
| Baseline: most recent PI listed on ClinicalTrials.gov at that site | 2 of 17 | 7 of 17 |
| Agent | 6 of 17 | 13 of 17 |

The research office's email domain matched the real site coordinator's domain at 13 of 16 sites.

## Results on LINKER-MM3 (Regeneron, linvoseltamab), 12 sites

Stage 2 v2 (this methodology), one agent, 11.9 min, 133K tokens. Gate: **passed, 7 of 7 checks**.

| Check | Result |
|---|---|
| Doctor still there (1572 in that city since 2025-04-11, looked up by the gate itself) | 12 of 12 |
| All 4 criteria reported | 12 of 12 |
| Seniority-only picks routed to the office | 1 (UCLA), correctly routed |
| Competing-trial count matches script count (±2) | 12 of 12 (11 exact) |
| Office URL loads; no emails or phones | pass |

**What the criteria changed vs v1** (v1 = same stage, criteria only hinted): 5 of 12 picks.

| Site | v1 pick | v2 pick | Why |
|---|---|---|---|
| UT Southwestern | Afrough | Larry Anderson | Led REGN5459 (Regeneron) there; fewer competing trials |
| MD Anderson | Orlowski | Jing Christine Ye | Earlier linvoseltamab PI (Hans Lee) left; Ye now carries the linvoseltamab and REGN5459 payments at MD Anderson |
| UCLA | Larson | Gary Schiller, **route: office** | Larson ran linvoseltamab but has no 1572 since 2024-10, so she is out; the next pick rests on seniority, so go to the office |
| Moffitt | Baz | Melissa Alsina | Baz's last 1572 is 2024-11; Alsina leads a BCMAxCD3 (elranatamab) trial there |
| MSK | Usmani (0.4) | Usmani (0.7) | Same person, now backed by T-cell-engager (teclistamab) work, not seniority alone |

Under the v2 rule, the v1 picks would have scored 10 of 12 still there. v2 scores 12 of 12.

**Leak note (disclosed, not rerun):** one Open Payments query by candidate surname also returned payment rows for LINKER-MM3 itself,
naming Maly and Ye. The agent never cited them, and both picks stand on other evidence (Maly: earlier linvoseltamab trial 2023–25;
Ye: 2025 linvoseltamab/REGN5459 payments at MD Anderson). Next run: strip target-trial rows from Open Payments before the agent sees them.
Logged in `runs/linker-mm3/gates.json`.

**Open items the agent flagged:** the Mayo and Moffitt office pages block scripts (403), so the agent saw them only in search results.
UCLA's and Sylvester's links are general research pages, not sponsor-intake pages. Mayo (Kumar vs Kapoor) and UTSW (Anderson vs Afrough)
were close calls.

## Limits (say these out loud)

- We never check whether an email works. We give the office page and domain, and a human sends.
- BMIS shows who is active, but not who will say yes. Almost every senior myeloma doctor files 1572s, so criterion 1 filters but doesn't rank.
- Open Payments only covers industry-paid research, and only with a lag.
- Single-trial pilots: the backtest is 17 sites on one trial, and the live run is 12 sites on one trial.
- Reply rates are untested. Our bet is that the ask gets smaller (the site agent pre-fills the questionnaire), not that cold outreach gets answered more.

## Files

- Prompt: `prompts/stage2_contacts.md` (v1, before these criteria: `runs/linker-mm3/attempts/stage2_v1/`)
- Agent output: `runs/linker-mm3/stage2/contacts.json`. Gate report: `runs/linker-mm3/gate2.json`
- Gate code: `e2e.py` (`gate2`, `bmis_latest`, `competing`)
