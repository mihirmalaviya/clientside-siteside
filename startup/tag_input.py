"""Print what the tagger is allowed to see for each trial: no sites, no enrollment.
Tags in trial_tags.json were made by Claude reading this output:
  pop: adult|peds|both   severity: severe|mild_moderate|unspecified
  drug: biologic|inhaled|oral|other   eos: yes|no (eosinophilic / type-2 focus)
"""
import backtest as b

studies = b.download()
raw = {s["protocolSection"]["identificationModule"]["nctId"]: s["protocolSection"] for s in studies}
for t in sorted(b.parse(studies), key=lambda t: t["nct"]):
    ps = raw[t["nct"]]
    conds = ps.get("conditionsModule", {}).get("conditions", [])
    ivs = [f'{i.get("type","")}:{i.get("name","")}' for i in ps.get("armsInterventionsModule", {}).get("interventions", [])]
    ages = ",".join(ps.get("eligibilityModule", {}).get("stdAges", []))
    print(f'{t["nct"]} | {t["phase"]} | {ages} | {t["title"]} | {"; ".join(conds)} | {"; ".join(ivs)}')
