#!/usr/bin/env python3
"""FDA BMIS lookup (US clinical investigators, Form 1572s received 2018-2026).
  python3 bmis.py Lonial            # all filings for that last name
  python3 bmis.py Lonial Sagar      # narrow by first name
  python3 bmis.py --city Atlanta GA # everyone with filings in a city since 2024
Prints: last | first | degree | site | city | state | received"""
import csv, os, sys
rows = csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmis_ci_us.tsv")), delimiter="\t")
a = sys.argv[1:]
if a[:1] == ["--city"]:
    city, st = " ".join(a[1:-1]).upper(), a[-1].upper()
    hits = [r for r in rows if r["city"].upper() == city and r["state"] == st and r["received"] >= "2024"]
else:
    hits = [r for r in rows if r["last"].upper() == a[0].upper() and (len(a) < 2 or r["first"].upper().startswith(a[1].upper()))]
for r in sorted(hits, key=lambda r: r["received"]):
    print(" | ".join(r[k] for k in ("last", "first", "degree", "site", "city", "state", "received")))
