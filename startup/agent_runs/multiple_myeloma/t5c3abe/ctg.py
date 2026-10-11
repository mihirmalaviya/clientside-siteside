#!/usr/bin/env python3
"""ClinicalTrials.gov search for the site-selection agent, limited to what was known before the new trial.

  python3 ctg.py '{"query.cond": "lymphoma", "query.spons": "Janssen"}'   # any API v2 query.* params
  python3 ctg.py '{"query.term": "daratumumab"}' --max 3000                 # default --max 1000 studies

Prints one line per trial: nct | start | phase | sponsor | title | US sites as facility (city, state); ...
Trials that started on or after the cutoff in ctg_config.json are never returned; neither is the new trial.
"""
import hashlib, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "ctg_config.json")))   # {"cutoff": "YYYY-MM-DD", "hidden": sha256 of NCT}
FIELDS = "NCTId,BriefTitle,LeadSponsorName,StartDate,Phase,LocationFacility,LocationCity,LocationState,LocationCountry"

def main():
    params = {k: v for k, v in json.loads(sys.argv[1]).items() if k.startswith("query.")}
    limit = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 1000
    params.update({"fields": FIELDS, "pageSize": 1000, "format": "json",
                   "filter.advanced": f"AREA[StartDate]RANGE[MIN,{CFG['cutoff']}]"})
    seen, token = 0, None
    while seen < limit:
        if token:
            params["pageToken"] = token
        url = "https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(params)
        page = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "site-agent"}), timeout=60))
        for s in page.get("studies", []):
            ps = s["protocolSection"]
            nct = ps["identificationModule"]["nctId"]
            start = ps.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
            # RANGE is inclusive; month-only dates in the cutoff month are excluded too
            if hashlib.sha256(nct.encode()).hexdigest() == CFG["hidden"] or not start or start >= CFG["cutoff"][:len(start)]:
                continue
            us = [f'{l.get("facility", "")} ({l.get("city", "")}, {l.get("state", "")})'
                  for l in ps.get("contactsLocationsModule", {}).get("locations", []) if l.get("country") == "United States"]
            print(f'{nct} | {start} | {",".join(ps.get("designModule", {}).get("phases", []))} | '
                  f'{ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")} | '
                  f'{ps["identificationModule"].get("briefTitle", "")} | {"; ".join(us)}')
            seen += 1
        token = page.get("nextPageToken")
        if not token:
            break

if __name__ == "__main__":
    main()
