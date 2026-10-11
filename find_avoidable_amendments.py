#!/usr/bin/env python3
"""
find_avoidable_amendments.py

Builds a candidate test set of REAL, AVOIDABLE protocol amendments from public
ClinicalTrials.gov data, for backtesting a protocol checker ("Protocol Pre-Flight").

Method (Tufts CSDD definition of avoidable = design flaws, errors/inconsistencies,
recruitment difficulty; unavoidable = new safety info, regulator requests,
standard-of-care or strategy changes):

  1. Search the public API v2 for completed, industry-sponsored Phase 2/3 trials
     that posted a protocol document.
  2. List every posted protocol document per trial. Trials with 2+ protocol
     documents may have a BEFORE and AFTER version posted -> blind-test pairs.
  3. Pull the registry version history (same internal endpoints the `cthist`
     R package uses) and flag eligibility / primary-outcome text that changed
     AFTER the study start date (likely amendments).
  4. Download the protocol PDFs, find the amendment / summary-of-changes text,
     and count rationale phrases that look AVOIDABLE (typo, inconsistency,
     correction, missing, alignment) vs UNAVOIDABLE (safety, regulator, IB,
     COVID, strategy).
  5. Write a ranked CSV plus per-trial evidence snippets for human review.

Every candidate still needs a human to read the change table and confirm it.
The script narrows thousands of trials down to a short list worth reading.

Usage:
  pip install requests pypdf
  python find_avoidable_amendments.py --max-studies 200 --out ctg_out
  python find_avoidable_amendments.py --nct NCT05048719 NCT05136404 --out ctg_out

Be polite to the API: requests are throttled (default ~1 per second).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

API_V2 = "https://clinicaltrials.gov/api/v2/studies"
API_INT = "https://clinicaltrials.gov/api/int/studies"  # history endpoints (used by cthist)
CDN = "https://cdn.clinicaltrials.gov/large-docs"

HEADERS = {"User-Agent": "protocol-preflight-research/0.1 (hackathon; contact via GitHub)"}

# --- Rationale classifiers (tuned for sponsor "Summary of Changes" tables) ---
AVOIDABLE_RE = re.compile(
    r"typographical|typo\b|inconsisten|discrepan|correct(?:ion|ed|s)?\b|\berror|errors\b|"
    r"missing|omitted|omission|oversight|for accuracy|to align with section|"
    r"align(?:ed|ment)? with (?:section|the (?:text|soa|schedule|synopsis|protocol))|"
    r"conflicting|contradict",
    re.I,
)
UNAVOIDABLE_RE = re.compile(
    r"safety (?:data|information|signal|finding)|new safety|investigator'?s brochure|\bIB\b|"
    r"health authority|regulatory (?:agency|authority|request|feedback)|agency (?:request|comment)|"
    r"\bFDA\b|\bEMA\b|\bMHRA\b|\bPMDA\b|EU[- ]CTR|COVID|pandemic|standard of care|"
    r"sponsor decision|strategic|business decision|terminat",
    re.I,
)
# Phrases that mark where amendment/change-log text lives inside a protocol PDF
CHANGE_SECTION_RE = re.compile(
    r"summary of changes|overall rationale for (?:the )?amendment|protocol amendment history|"
    r"document history|amendment rationale|primary reason for (?:this )?amendment|"
    r"rationale for (?:the )?amendment|list of changes",
    re.I,
)


@dataclass
class Candidate:
    nct: str
    title: str = ""
    phases: str = ""
    sponsor: str = ""
    sponsor_class: str = ""
    start_date: str = ""
    has_results: bool = False
    protocol_docs: list[dict] = field(default_factory=list)
    registry_versions: int = 0
    elig_changed_after_start: int = 0
    outcome_changed_after_start: int = 0
    registry_change_dates: list[str] = field(default_factory=list)
    avoidable_hits: int = 0
    unavoidable_hits: int = 0
    evidence: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def n_protocol_docs(self) -> int:
        return len(self.protocol_docs)

    def score(self) -> float:
        # Favour: real avoidable language, before/after pairs, registry evidence;
        # penalise amendments dominated by safety/regulatory drivers.
        s = 2.0 * self.avoidable_hits - 1.0 * self.unavoidable_hits
        s += 5.0 if self.n_protocol_docs >= 2 else 0.0
        s += 1.5 * min(self.elig_changed_after_start + self.outcome_changed_after_start, 4)
        return s


class Client:
    def __init__(self, delay: float = 1.1, retries: int = 4):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.delay = delay
        self.retries = retries
        self._last = 0.0

    def get(self, url: str, params: dict | None = None, stream: bool = False) -> requests.Response:
        for attempt in range(self.retries):
            wait = self.delay - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = self.s.get(url, params=params, timeout=60, stream=stream)
            except requests.RequestException as e:
                if attempt == self.retries - 1:
                    raise
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** (attempt + 1))
                continue
            return r
        return r


# ---------------------------------------------------------------- 1. search

def _g(d, *path, default=None):
    for p in path:
        if not isinstance(d, dict):
            return default
        d = d.get(p)
    return d if d is not None else default


def study_to_candidate(st: dict) -> Candidate:
    ps = st.get("protocolSection", {})
    docs = _g(st, "documentSection", "largeDocumentModule", "largeDocs", default=[]) or []
    prot_docs = [d for d in docs if d.get("hasProtocol")]
    return Candidate(
        nct=_g(ps, "identificationModule", "nctId", default=""),
        title=_g(ps, "identificationModule", "briefTitle", default=""),
        phases=",".join(_g(ps, "designModule", "phases", default=[]) or []),
        sponsor=_g(ps, "sponsorCollaboratorsModule", "leadSponsor", "name", default=""),
        sponsor_class=_g(ps, "sponsorCollaboratorsModule", "leadSponsor", "class", default=""),
        start_date=_g(ps, "statusModule", "startDateStruct", "date", default=""),
        has_results=bool(st.get("hasResults")),
        protocol_docs=[
            {
                "filename": d.get("filename", ""),
                "label": d.get("label", ""),
                "date": d.get("date", ""),
                "uploadDate": d.get("uploadDate", ""),
                "typeAbbrev": d.get("typeAbbrev", ""),
                "size": d.get("size", 0),
            }
            for d in prot_docs
        ],
    )


def passes_filters(c: Candidate, phases: set[str], industry_only: bool) -> bool:
    if not c.protocol_docs:
        return False
    if phases and not (set(c.phases.split(",")) & phases):
        return False
    if industry_only and c.sponsor_class != "INDUSTRY":
        return False
    return True


def search(client: Client, max_studies: int, phases: set[str], industry_only: bool,
           condition: str | None) -> list[Candidate]:
    """Page through API v2. Tries server-side aggFilters first; if the API rejects
    them, falls back to plain paging with client-side filtering."""
    agg = ["status:com", "results:with", "docs:prot"]
    if phases:
        agg.append("phase:" + " ".join(p.replace("PHASE", "") for p in sorted(phases)))
    if industry_only:
        agg.append("funderType:industry")

    base = {"pageSize": 100, "format": "json", "filter.overallStatus": "COMPLETED"}
    if condition:
        base["query.cond"] = condition

    out: list[Candidate] = []
    for use_agg in (True, False):
        params = dict(base)
        if use_agg:
            params["aggFilters"] = ",".join(agg)
        token = None
        out.clear()
        scanned = 0
        ok = True
        while len(out) < max_studies:
            if token:
                params["pageToken"] = token
            r = client.get(API_V2, params=params)
            if r.status_code != 200:
                print(f"[search] API returned {r.status_code} (aggFilters={'on' if use_agg else 'off'}): "
                      f"{r.text[:200]}", file=sys.stderr)
                ok = False
                break
            data = r.json()
            for st in data.get("studies", []):
                scanned += 1
                c = study_to_candidate(st)
                if c.has_results and passes_filters(c, phases, industry_only):
                    out.append(c)
                    if len(out) >= max_studies:
                        break
            token = data.get("nextPageToken")
            print(f"[search] scanned {scanned}, kept {len(out)}", file=sys.stderr)
            if not token:
                break
            if not use_agg and scanned > max_studies * 60:
                print("[search] client-side filtering is slow; stopping early", file=sys.stderr)
                break
        if ok and out:
            return out
        if ok and not out and use_agg:
            print("[search] no results with aggFilters; retrying with client-side filters", file=sys.stderr)
    return out


def fetch_one(client: Client, nct: str) -> Candidate | None:
    r = client.get(f"{API_V2}/{nct}", params={"format": "json"})
    if r.status_code != 200:
        print(f"[{nct}] study fetch failed: {r.status_code}", file=sys.stderr)
        return None
    return study_to_candidate(r.json())


# ---------------------------------------------------------------- 3. registry history

def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def registry_history(client: Client, c: Candidate, max_versions: int) -> None:
    r = client.get(f"{API_INT}/{c.nct}", params={"history": "true"})
    if r.status_code != 200:
        c.notes.append(f"history index HTTP {r.status_code}")
        return
    changes = _g(r.json(), "history", "changes", default=[]) or []
    c.registry_versions = len(changes)
    start = (c.start_date or "")[:10]
    # versions dated on/after the start date, plus the last pre-start version as baseline
    after = [ch for ch in changes if start and str(ch.get("date", ""))[:10] >= start]
    before = [ch for ch in changes if not start or str(ch.get("date", ""))[:10] < start]
    seq = ([before[-1]] if before else []) + after
    if len(seq) > max_versions:  # keep baseline + evenly spaced sample + latest
        step = max(1, len(seq) // max_versions)
        seq = seq[:1] + seq[1:-1:step][: max_versions - 2] + seq[-1:]

    prev_elig = prev_out = None
    for i, ch in enumerate(seq):
        v = ch.get("version")
        rv = client.get(f"{API_INT}/{c.nct}/history/{v}")
        if rv.status_code != 200:
            continue
        ps = _g(rv.json(), "study", "protocolSection", default={})
        elig = _norm(_g(ps, "eligibilityModule", "eligibilityCriteria"))
        prim = _norm(json.dumps(_g(ps, "outcomesModule", "primaryOutcomes", default=[]), sort_keys=True))
        if i > 0:
            date = str(ch.get("date", ""))[:10]
            if prev_elig is not None and elig != prev_elig:
                c.elig_changed_after_start += 1
                c.registry_change_dates.append(f"{date}:eligibility")
            if prev_out is not None and prim != prev_out:
                c.outcome_changed_after_start += 1
                c.registry_change_dates.append(f"{date}:primary_outcome")
        prev_elig, prev_out = elig, prim


# ---------------------------------------------------------------- 4. protocol PDFs

def pdf_url(nct: str, filename: str) -> str:
    return f"{CDN}/{nct[-2:]}/{nct}/{filename}"


def download_pdf(client: Client, nct: str, doc: dict, folder: Path) -> Path | None:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{nct}_{doc['filename']}"
    if path.exists() and path.stat().st_size > 0:
        return path
    r = client.get(pdf_url(nct, doc["filename"]))
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return None
    path.write_bytes(r.content)
    return path


def pdf_pages(path: Path) -> list[str]:
    from pypdf import PdfReader  # imported lazily so --skip-pdfs works without it
    try:
        reader = PdfReader(str(path))
    except Exception as e:  # noqa: BLE001
        print(f"[pdf] cannot open {path.name}: {e}", file=sys.stderr)
        return []
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:  # noqa: BLE001
            pages.append("")
    return pages


def change_log_pages(pages: list[str], window: int = 6) -> list[int]:
    """Pages that contain amendment / summary-of-changes text, plus a few after
    each hit (change tables often run over several pages)."""
    idx: set[int] = set()
    for i, t in enumerate(pages):
        if CHANGE_SECTION_RE.search(t):
            idx.update(range(i, min(len(pages), i + window)))
    return sorted(idx)


def mine_rationales(c: Candidate, path: Path, label: str) -> None:
    pages = pdf_pages(path)
    if not pages:
        c.notes.append(f"{path.name}: no extractable text (scanned?)")
        return
    hits = change_log_pages(pages)
    if not hits:
        c.notes.append(f"{path.name}: no change-log section found")
        return
    for pi in hits:
        for line in pages[pi].splitlines():
            line = line.strip()
            if len(line) < 6:
                continue
            a = AVOIDABLE_RE.search(line)
            u = UNAVOIDABLE_RE.search(line)
            if a:
                c.avoidable_hits += 1
                c.evidence.append(f"[AVOIDABLE?] {path.name} p{pi + 1} ({label}): {line[:220]}")
            if u:
                c.unavoidable_hits += 1
                c.evidence.append(f"[UNAVOIDABLE?] {path.name} p{pi + 1} ({label}): {line[:220]}")


# ---------------------------------------------------------------- 5. output

def write_outputs(cands: list[Candidate], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cands = sorted(cands, key=lambda c: c.score(), reverse=True)
    with open(out / "candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "rank", "score", "nct", "title", "phases", "sponsor", "start_date",
            "n_protocol_docs", "before_after_pair_possible", "protocol_docs (label|date|url)",
            "registry_versions", "elig_changed_after_start", "primary_outcome_changed_after_start",
            "registry_change_dates", "avoidable_hits", "unavoidable_hits", "notes",
        ])
        for i, c in enumerate(cands, 1):
            docs = " ; ".join(
                f"{d['label'] or d['typeAbbrev']}|{d['date']}|{pdf_url(c.nct, d['filename'])}"
                for d in c.protocol_docs
            )
            w.writerow([
                i, round(c.score(), 1), c.nct, c.title, c.phases, c.sponsor, c.start_date,
                c.n_protocol_docs, "yes" if c.n_protocol_docs >= 2 else "no", docs,
                c.registry_versions, c.elig_changed_after_start, c.outcome_changed_after_start,
                " ".join(c.registry_change_dates), c.avoidable_hits, c.unavoidable_hits,
                " | ".join(c.notes),
            ])
    ev_dir = out / "evidence"
    ev_dir.mkdir(exist_ok=True)
    for c in cands:
        if c.evidence or c.registry_change_dates:
            (ev_dir / f"{c.nct}.txt").write_text(
                f"{c.nct} — {c.title}\nSponsor: {c.sponsor}  Phases: {c.phases}  Start: {c.start_date}\n"
                f"Protocol docs: {json.dumps(c.protocol_docs, indent=1)}\n"
                f"Registry changes after start: {c.registry_change_dates}\n\n"
                + "\n".join(c.evidence),
                encoding="utf-8",
            )
    print(f"\nWrote {out / 'candidates.csv'} ({len(cands)} trials) and evidence/ snippets.")
    print("Next: open the top-ranked trials' evidence files, read each change table, and keep only\n"
          "changes whose stated rationale is an error, inconsistency, missing item, or alignment fix.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="ctg_out", help="output folder")
    ap.add_argument("--max-studies", type=int, default=150, help="how many matching trials to collect")
    ap.add_argument("--nct", nargs="*", help="skip search; analyse these NCT IDs")
    ap.add_argument("--condition", help="optional condition filter, e.g. 'atopic dermatitis'")
    ap.add_argument("--phases", nargs="*", default=["PHASE2", "PHASE3"])
    ap.add_argument("--all-sponsors", action="store_true", help="include non-industry sponsors")
    ap.add_argument("--skip-history", action="store_true", help="skip registry version history")
    ap.add_argument("--skip-pdfs", action="store_true", help="skip PDF download/mining")
    ap.add_argument("--max-versions", type=int, default=12, help="registry versions to diff per trial")
    ap.add_argument("--delay", type=float, default=1.1, help="seconds between requests")
    args = ap.parse_args()

    client = Client(delay=args.delay)
    out = Path(args.out)

    if args.nct:
        cands = [c for c in (fetch_one(client, n.strip()) for n in args.nct) if c]
    else:
        cands = search(client, args.max_studies, set(args.phases), not args.all_sponsors, args.condition)
    print(f"[main] {len(cands)} trials to analyse", file=sys.stderr)

    for i, c in enumerate(cands, 1):
        print(f"[{i}/{len(cands)}] {c.nct} ({c.n_protocol_docs} protocol docs)", file=sys.stderr)
        if not args.skip_history:
            try:
                registry_history(client, c, args.max_versions)
            except Exception as e:  # noqa: BLE001
                c.notes.append(f"history error: {e}")
        if not args.skip_pdfs:
            for d in c.protocol_docs:
                try:
                    p = download_pdf(client, c.nct, d, out / "pdfs")
                    if p:
                        mine_rationales(c, p, d.get("label") or d.get("typeAbbrev", ""))
                    else:
                        c.notes.append(f"download failed: {d['filename']}")
                except Exception as e:  # noqa: BLE001
                    c.notes.append(f"pdf error {d.get('filename')}: {e}")
        # write as we go so a long run can be interrupted safely
        if i % 10 == 0:
            write_outputs(cands[:i], out)

    write_outputs(cands, out)


if __name__ == "__main__":
    main()
