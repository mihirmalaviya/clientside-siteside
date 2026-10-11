# Sponsorside + Clientside

**Two AI agents that take the busywork out of clinical trial site startup: one works for the drug company, one works for the hospital.**

Before a new medicine can be tested, the sponsor has to find hospitals (sites) to run the trial, reach the right people there, and collect a long feasibility questionnaire from each one. That takes months, and much of it is the same work repeated. Sponsorside picks better sites, finds who to contact, and asks only what public data can't answer. Clientside answers a sponsor's questionnaire from the hospital's own records in about a minute and a half, shows the exact line each answer came from, and flags what it doesn't know instead of guessing.

Built for the Regeneron challenge at HackRU: *make clinical trials and new medicines development faster and better.*

---

## For the judges: rubric at a glance

| Criterion | What we have | Where |
|---|---|---|
| **Utility & relevance** | Targets site selection and feasibility, a startup phase that takes months and stalls trials. Tested on a real Regeneron myeloma trial (LINKER-MM3, linvoseltamab, NCT05730036) and on 34 past myeloma trials. | [The problem](#the-problem) · [Results](#how-we-show-it-works) |
| **Readiness: functional** | The app runs from one command with no installs. Every screen shows output recorded from a real agent run, not mock data. | [Quick start](#quick-start-30-seconds) |
| **Readiness: replicable** | The pipeline runs stage by stage with pass/fail gates fixed *before* the run. It uses the Python standard library only, plus public data (ClinicalTrials.gov, FDA BMIS, CMS Open Payments, NPI Registry). | [Reproduce the run](#reproduce-the-run) |
| **Readiness: deployable** | A static web app (HTML + JS, no build step) you can host anywhere. Data comes from one JSON file per run. | [How it's built](#how-its-built) |
| **Open source** | GitHub repo, MIT license. | [License](#license) |
| **Design & packaging** | A demo video (~3 min), a slide deck (~10 slides), an intuitive two-sided UI, and this documentation. | [Demo & deck](#demo-video-and-slides) |

---

## Quick start (30 seconds)

Requirements: Python 3.9+ and a browser. Nothing to install.

```bash
git clone https://github.com/mihirmalaviya/protocolcopilot.git
cd protocolcopilot/startup/app
python3 -m http.server 8765
```

Open **http://localhost:8765** and then:

1. Press **Space**. The demo trial ID (NCT05730036) types itself. Press **Space** again to run the search.
2. Watch **Ranking** score 300 candidate hospitals and pin the top 50 on the map. Press **Space** to move to the next phase: **Contacts**, then **Questionnaires**, then **Recommendations**.
3. Click any row to see why it was picked, who to contact, what's already known, and the draft follow-up.
4. On the **Questionnaires** tab, click **Answer** on *Riverside Cancer Center*. The view slides over to **Clientside**, the hospital's agent, which drafts its reply.
5. Click any drafted answer to see the exact lines in the hospital's files it came from. Red highlights are proprietary data and lavender is public. Check the **Q&A log** tabs for what the hospital has answered before.
6. Click **Send**. The reply is copied to your clipboard and you're taken back to the sponsor's view.

The **Clientside →** button in the top-right corner jumps straight to the hospital's side at any time.

---

## The problem

Before a drug trial can test a new medicine, the drug company (the **sponsor**) has to sign up hospitals (**sites**) to run it. Getting those sites chosen and ready takes months, and every day of delay is expensive.

**What goes wrong today:**

- **Picking the wrong hospitals.** Sponsors choose sites from spreadsheets and gut feel. A commonly cited figure is that about 1 in 10 selected sites never enrolls a single patient.
- **Finding the right person to contact.** Even once you know the hospital, you need the right doctor and the right admin office. Contact info is often stale or not public. Mentors called this the *bootstrapping problem*.
- **The same questions, asked over and over.** Every sponsor sends a long feasibility questionnaire (commonly cited at around 4 hours each), and most of it repeats what the site has answered before.
- **Hospitals don't have the people.** Research staff are overloaded. The real bottleneck is sites running out of people and time.
- **Slow back-and-forth.** Questions, answers, follow-ups and waiting on email turn into weeks.

---

## What we built

### Sponsorside: the sponsor's agent

A four-phase pipeline. Each phase is a tab in the app, and each one is checked by a script before the next phase starts.

1. **Ranking.** Scores ~300 candidate US hospitals using public records of who has run similar trials before: same drug or drug class, same disease, same phase, same sponsor. Every pick cites real past trials, and the agent never sees which sites actually ran the target trial.
2. **Contacts.** For each top site it names **one doctor plus two backups**, and the site's **research office**. The doctor is chosen in this order:
   1. **Still there:** filed an FDA Form 1572 at this site in the last 18 months. This one is a filter: fail means out.
   2. **Same drug or class:** led this drug or its relatives at this site.
   3. **Same kind of trial:** led trials in this disease at this phase or earlier.
   4. **Has room:** few competing recruiting trials.

   If a pick rests on seniority alone, the agent routes the sponsor to the **research office first**. Offices don't retire. No emails or phone numbers are recorded, so a person always sends. Full method: [`startup/contactmethodology.md`](startup/contactmethodology.md).
3. **Questionnaires.** Reads the protocol and drug label, turns them into site requirements, and asks only what public data can't already answer: 20 requirements become 16 questions. It prefills what's already public for each site, and you can copy each questionnaire as a ready-to-send email.
4. **Recommendations.** Combines everything into a per-site recommendation with reasons and a draft follow-up that asks only what's still open. **Nothing is sent until a person approves it.**

### Clientside: the hospital's agent

- **Fills out any sponsor's questionnaire in about a minute and a half** from the hospital's own files: past questionnaires, staff roster, capabilities sheet, SOPs, operations log, patient export and contracts.
- **Grounded answers.** Every answer carries the verbatim lines it was based on. Click an answer and the source file opens with those lines highlighted. The app checks each quote against the real file and flags any that don't match.
- **Proprietary vs. public, at a glance.** Answers from the hospital's confidential records are highlighted red. Answers from public material (website, registry listings) are lavender.
- **Flags instead of guessing.** Anything the files can't answer, or that needs a human decision, is marked "Needs a human", with who should answer it.
- **Respects the disclosure policy.** It follows the hospital's own rules: no patient-level data, no confidential pipeline trial names, no other sponsors' terms.
- **Remembers past answers.** A public and a confidential **Q&A write-ahead log** record every answer the site has given before, so it stops re-answering the same things.
- **Works today on its own,** without the sponsor changing anything. The output is a normal email reply.

### The future: the handshake

When both sides have an agent, they talk to each other directly. The sponsor agent sends only the questions public data can't answer, and the site agent replies in minutes from its own records. The questionnaire step goes from weeks of email to minutes, with a person approving on each side. The demo shows this hand-off: the sponsor's view slides over to the site's view and back.

---

## How we show it works

Everything below comes from recorded runs in this repo. Pass/fail bars were written down in [`runs/linker-mm3/gates.json`](startup/runs/linker-mm3/gates.json) **before** the run.

### 1. Site selection

**Live run on a real Regeneron trial (LINKER-MM3, linvoseltamab, 10 real US sites).** We hid which hospitals actually ran it and asked the agent to rank sites using only data from before the trial started.

| Ranker | Real sites in its top 50 |
|---|---|
| **Sponsorside agent** | **5 of 10** |
| Pick the sites with the most past trials | 4 of 10 |
| Our scoring formula alone | 2 of 10 |
| Formula + same sponsor | 3 of 10 |

**Formula backtest across 34 past multiple myeloma trials** (758 real sites, top 50 picks each, history before each trial's start only):

| Ranker | Real sites found |
|---|---|
| Random pick | 3 (0.4%) |
| Most past trials | 121 (16.0%) |
| Our formula | 130 (17.2%) |
| Formula + same sponsor | 131 (17.3%) |

Only 48% of real sites had run an earlier myeloma trial at all, so that's the ceiling for any history-based ranker. The formula alone is only slightly better than "most past trials". The agent's advantage on LINKER-MM3 comes from reasoning about drug class and sponsor history, and that's a single trial. See the limits below.

### 2. Contacts

- **Backtest:** 17 US sites of a real, finished myeloma trial, with the trial's own records off limits.

  | | Right doctor as the top pick | Right doctor in the top 3 |
  |---|---|---|
  | Most recent PI listed on ClinicalTrials.gov at that site | 2 of 17 | 7 of 17 |
  | **Sponsorside agent** | **6 of 17** | **13 of 17** |

  The research office's email domain matched the real coordinator's domain at 13 of 16 sites.
- **LINKER-MM3:**
  - all 12 picked doctors filed an FDA 1572 at their site since 2025-04-11, checked by a script against FDA's BMIS data rather than taken from the agent
  - 11 sites are doctor-first and 1 is office-first
  - all research-office links load
  - no emails or phone numbers anywhere in the output

### 3. Site agent (Clientside)

We built a synthetic hospital, Riverside Cancer Center, with 16 hand-written files (public and confidential) and a hidden answer key it never sees. The agent then answered the 16-question LINKER-MM3 questionnaire:

- **13 of 16** answers match the hidden key exactly. The other three (patient counts and percentages) are off by one patient, because the agent read "last 12 months" as ending today rather than at the end of last month.
- **91 of 91** quoted evidence lines appear word for word in the cited files.
- **0** confidential details leaked into the answers: no patient IDs, no confidential pipeline trial names.
- It caught the stale data planted in the files: old freezer and staff counts, an outdated overhead rate, and a public website listing 16 chairs instead of 18.
- It took **about 1.5 minutes** of agent time. We have not yet timed a person doing the same questionnaire by hand.

The whole LINKER-MM3 pipeline, from ranking through recommendations, took about **25 minutes of agent time**.

---

## What we don't claim

- We don't speed up contracts, budgets or ethics (IRB) approval: only finding sites, contacting them, and the questionnaire step.
- We don't make startup "instant". We remove the repetitive part, and people still approve every send.
- The evidence is a pilot:
  - one live trial: 10 real sites, 12 contacts
  - one 17-site contact backtest
  - one synthetic hospital
  - the asthma backtest is set up in `agent_runs/asthma/` but not yet run
- FDA BMIS shows who is active, not who will say yes. Open Payments only covers industry-paid research, and with a lag.
- We never check whether an email address works. We give the office page and domain, and a person sends.
- Reply rates are untested. Our bet is that the ask gets smaller (shorter questionnaires, pre-filled answers), not that cold outreach suddenly gets answered.
- Riverside Cancer Center is fictional. Real hospitals' internal records will be messier.

---

## How it's built

```
public data ──▶ Sponsorside pipeline (startup/e2e.py) ──▶ runs/linker-mm3/stageN/  ──▶ gates (script checks)
                 agents work only inside their stage folder        │
site files  ──▶ Clientside agent (stage 3b, Riverside)             ▼
                                                    app/runs/linker-mm3.json ──▶ static web app (app/)
```

- **Agents:** each stage is an LLM agent given one prompt (`startup/prompts/`) and one folder. It can read only that folder: answer keys and gate reports live outside it.
- **Gates:** after each stage a Python script checks the agent's work against the raw data, not against the agent's own claims. Examples: re-querying BMIS for every picked doctor, re-counting competing trials, checking every link loads, scanning for emails and phone numbers, and checking every quote against its file. A failed gate stops the run.
- **Data:**
  - ClinicalTrials.gov: trial history, sites and PIs
  - FDA BMIS: Form 1572 filings by investigator
  - CMS Open Payments: industry research payments naming PIs
  - NPI Registry
  - The site agent works from `startup/site_data/riverside/`, split into `public/` and `confidential/`. Its answer key is in `startup/site_data/key.md`.
- **App:** plain HTML, CSS and JS in `startup/app/` (d3 + topojson are vendored for the map). The build step writes one JSON file per run, and the app renders it. The replay timing is simulated so a 25-minute agent run can be demoed in a couple of minutes. Every number and name shown comes from the run file.

---

## Reproduce the run

From `startup/`, each stage is a `prep` step that sets up the agent's folder. Then run the agent with its prompt from `prompts/`, then the `gate` step:

```bash
python3 e2e.py prep1   # then run prompts/stage1_sites.md        → python3 e2e.py gate1
python3 e2e.py prep2   # then run prompts/stage2_contacts.md     → python3 e2e.py gate2
python3 e2e.py prep3a  # then run prompts/stage3a_questionnaire.md → python3 e2e.py gate3a
python3 e2e.py prep3b  # then run prompts/stage3b_public_prefill.md and stage3b_riverside.md → python3 e2e.py gate3b
python3 e2e.py prep4   # then run prompts/stage4_decisions.md    → python3 e2e.py gate4
python3 e2e.py build   # writes app/runs/linker-mm3.json for the web app
```

- **Agents:** we ran each agent with Claude (model and timing per stage are in `runs/linker-mm3/timeline.json`). Any agent that can read and write files in a folder will work.
- **Formula backtest:** `python3 backtest.py`, with results in `startup/results_summary.md`. Contact backtest: `contact_test.py`.

---

## Repo layout

```
startup/
  app/                  the web app (Sponsorside + Clientside); serve this folder
  e2e.py                end-to-end pipeline: prep, gate and build per stage
  prompts/              the exact prompt each agent got
  runs/linker-mm3/      every stage's inputs, agent outputs, gate reports, timeline
  site_data/riverside/  synthetic hospital files (public/ + confidential/); key.md is the hidden answer key
  contactmethodology.md how contacts are chosen and checked
  backtest.py, contact_test.py, results_summary.md   offline backtests
```

---

## Demo video and slides

- **Demo video (~3 min):** _link to be added_
- **Slide deck (~10 slides):** _link to be added_

---

## License

MIT. See [`LICENSE`](LICENSE).
