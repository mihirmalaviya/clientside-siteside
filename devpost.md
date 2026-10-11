## Inspiration

Before a new medicine can be tested, the drug company has to sign up hospitals to run the trial. That step alone takes months.
- Sponsors pick sites from spreadsheets and gut feel. A commonly cited figure is that about 1 in 10 sites never enrolls a single patient.
- Then they have to find the right doctor, and contact info is often stale.
- Then every site gets a long feasibility questionnaire, mostly the same questions it has answered many times before.

Regeneron's mentors told us the real bottleneck is that sites run out of people and time. So we built an agent for each side: one that does the sponsor's legwork, and one that does the hospital's.

## What it does

**Sponsorside** (for the drug company) works through four steps:
- **Ranking:** scores about 300 US hospitals by who has run similar trials before, and shortlists the top 50.
- **Contacts:** names the right doctor at each site. The doctor must have filed an FDA Form 1572 there recently and have led this drug or drug class. Picks with only seniority behind them are routed to the research office first.
- **Questionnaires:** turns the protocol into 16 questions, asking only what public data can't answer.
- **Recommendations:** gives a call per site with a draft follow-up. Nothing is sent until a person approves.

**Clientside** (for the hospital):
- **Answers a sponsor's questionnaire in about 1.5 minutes** from the hospital's own files.
- **Every answer is grounded.** Click it to see the exact lines it came from, highlighted in the source file.
- **Proprietary data is shown in red** and public data in lavender.
- **It flags anything it can't answer** instead of guessing, and follows the hospital's disclosure policy.
- **It keeps a Q&A log** of past answers so the site stops re-answering the same things.
- **It works today with any sponsor's form.** The output is a normal email reply.

**The handshake.** When both sides run an agent, the questionnaire goes from weeks of email to minutes, with a person approving on each side.

## How we built it

- **A staged pipeline** (`e2e.py`). Each stage is an LLM agent (Claude) given one prompt and one folder it can't leave.
- **Public data:** ClinicalTrials.gov, FDA BMIS (Form 1572 filings), CMS Open Payments and the NPI Registry.
- **Script gates after every stage** check the agent's work against the raw data, not against its own claims. For example, a script re-looks-up every picked doctor in BMIS and checks every quote against its file. We fixed the pass bars before the run.
- **A synthetic hospital,** Riverside Cancer Center: 16 hand-written files with traps like stale numbers and date-window edges, plus a hidden answer key the agent never sees.
- **A static web app** (plain HTML/JS with a d3 map) that replays one recorded run. No build step, nothing to install, and it's MIT licensed.

## Challenges we ran into

- **Stale contacts.** Doctors move, and records lag behind; one doctor's NPI listing still showed his old city. We made "still filing at this site" a hard filter instead of a score.
- **Agents grading themselves.** We stopped trusting the agents' own summaries and wrote scripts that re-check everything.
- **Coverage.** Our first questionnaire draft missed requirements: it covered 11 of 14 must-cover items. A generic coverage checklist fixed it, bringing it to 13 of 14.
- **Trust.** Hospitals won't send an answer they can't verify, so every answer had to point to a real line in a real file.
- **Honest baselines.** Our scoring formula alone barely beat "pick the sites with the most past trials" (17.2% vs 16.0%), so the real gains had to come from the agent's reasoning.

## Accomplishments that we're proud of

- **On a real Regeneron trial** (LINKER-MM3), with the real site list hidden, the agent's top 50 included **5 of 10** actual sites, vs 4 for the "most past trials" baseline.
- **Right doctor named as the top pick: 6 of 17,** vs 2 of 17 for the most recent listed PI. The right doctor was in the top 3 for 13 of 17.
- **The site agent got 13 of 16 answers exactly right** against a hidden key. **All 91 of its quoted evidence lines** appear word for word in the files, and no confidential data leaked.
- **The whole pipeline took about 25 minutes of agent time,** end to end.

## What we learned

- Check the work against raw data, not against what the agent says it did.
- "Is this person still there?" is a filter, not a score.
- Hospitals care as much about *what not to share* as about answering fast.
- Showing the source makes people trust an answer more than the answer itself does.

## What's next for Sponsorside + Clientside

- Run the asthma backtest and more live trials, and time real coordinators doing the questionnaire by hand.
- Pilot Clientside with a real hospital research office on its own past questionnaires.
- Build the handshake, so the two agents can talk to each other directly.
- Reuse answers from the Q&A log automatically, so repeat questions come out pre-filled.

## Built with

python, javascript, html5, css3, d3.js, topojson, us-atlas, claude, anthropic, claude-code, large-language-models, ai-agents, clinicaltrials.gov-api, fda-bmis, cms-open-payments, npi-registry, json, csv, markdown, node.js, headless-chromium, chrome-devtools-protocol, git, github, wsl
