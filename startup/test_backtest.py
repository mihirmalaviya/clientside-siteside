"""Run: python3 test_backtest.py  (no network)"""
from datetime import date
import backtest as b

def study(nct, start, facilities, cond=b.CONDITION):
    return {"protocolSection": {
        "identificationModule": {"nctId": nct},
        "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE3"]},
        "conditionsModule": {"conditions": [cond]},
        "statusModule": {"startDateStruct": {"date": start}, "overallStatus": "COMPLETED"},
        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "X", "class": "INDUSTRY"}},
        "contactsLocationsModule": {"locations": [
            {"facility": f, "city": "Boston", "state": "MA", "country": "United States"}
            for f in facilities]}}}

trials = b.parse([
    study("A", "2015-01", ["Brigham & Women's Hospital", "Research Site", "GSK Investigational Site"]),
    study("B", "2016-01", ["Brigham and Women's Hospital"]),
    study("C", "2014-01", ["Mass General"], cond="Eosinophilic Esophagitis"),
])
assert [t["nct"] for t in trials] == ["A", "B"]                       # non-asthma dropped
assert trials[0]["sites"] == trials[1]["sites"] == {("brigham and women s hospital", "boston", "ma")}  # placeholders dropped, names match
assert [t["nct"] for t in b.history_before(trials, trials[0])] == []   # no peeking at later trials
assert [t["nct"] for t in b.history_before(trials, trials[1])] == ["A"]
# AI similarity: a past trial sharing tags with the target outweighs one that doesn't
D = study("D", "2017-01", ["Mayo Clinic"])
E = study("E", "2017-01", ["Cleveland Clinic"])
T = study("T", "2018-01", ["Mayo Clinic"])
hist, tgt = b.parse([D, E]), b.parse([T])[0]
bio = {"pop": "adult", "severity": "severe", "drug": "biologic", "eos": "yes"}
tags = {"D": bio, "T": bio, "E": {"pop": "peds", "severity": "unspecified", "drug": "other", "eos": "no"}}
s = b.rank_ours(hist, tgt, False, tags)
assert s[("mayo clinic", "boston", "ma")] == 5 * s[("cleveland clinic", "boston", "ma")]  # 1+4 shared vs 1+0
# fuzzy matching for free-text agent picks: same city+state and a similar name
import agent_test as a
truth = {("university of texas md anderson cancer center", "houston", "texas"), ("baylor college of medicine", "houston", "texas")}
assert a.fuzzy_hits([("MD Anderson", "Houston", "Texas"), ("Houston Methodist", "Houston", "Texas")], truth) == 1
assert a.fuzzy_hits([("Mayo Clinic in Florida", "Jacksonville", "Florida")],
                    {("cancer specialists of north florida", "jacksonville", "florida")}) == 0   # state word isn't a match
# "University of <city/state>" names match their cancer center; city/state words alone still don't
assert a.fuzzy_hits([("University of Michigan", "Ann Arbor", "Michigan")], {("university of michigan rogel cancer center", "ann arbor", "michigan")}) == 1
assert a.fuzzy_hits([("Sylvester Comprehensive Cancer Center (University of Miami)", "Miami", "Florida")], {("university of miami hospital and clinics", "miami", "florida")}) == 1
assert a.fuzzy_hits([("University of Texas MD Anderson Cancer Center", "Houston", "Texas")], {("university of texas health science center houston", "houston", "texas")}) == 0
print("ok")
