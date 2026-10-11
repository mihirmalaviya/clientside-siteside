# Blind test 2 — NCT02584959 (Shire SHP616-300), 10 Oct 2026: prompt A vs prompt B

Both: Opus subagent, effort medium, given only the BEFORE PDF (Original v1.0) + text extraction; no web, no key.
- A = original free-form brief (same as test 1). ~3.0 min, 143K tokens, 25 findings.
- B = "list first, then compare": build inventories (numbers, procedures, eligibility→screening, endpoint→timepoint/population/analysis), then cross-check; generic M11/SPIRIT gaps last. ~2.8 min, 163K tokens, 23 findings.
- A first draft of B leaked the key (its examples described K1/K2); it was stopped before reporting and replaced with neutral wording.

## Recall vs answer key

| Key | A | B |
|---|---|---|
| K1 196-day AAS vs 14-week period | YES #1 high | YES #5 high |
| K2 placebo comparison over FAS incl. A/A sequence | PARTIAL #19 medium (buried in a generic missing-data item) | YES #3 high ("Sequence 3 (A/A) has no placebo period… yet FAS includes them") |
| K3 AE collection period (§8.1) | YES #3 high | YES #1 high |

Confirmed by text diff: "196-day" gone in Amd 1; one of three "until the defined follow-up period stated in Section 7.1.5" removed in Amd 1.

## Flags fixed by a later amendment but outside the key (both caught all three)
- Antibody follow-up "be requested to participate in longitudinal follow-up" (A13/B14) — removed in Amd 1 (sponsor listed it as a design change)
- Inclusion needs functional C1 INH <50% with no screening test (A4/B8, high) — Amd 3 added a screening C1 INH sample
- "Screening Visit (Visit 1a)" ambiguity (A9/B11) — gone in Amd 2

## Noise check (quotes grepped in Original and Amd 1–4)
- All checked quotes exist in the Original except A15 ("prior to starting prophylactic therapy with C1 INH or androgens" — not in v1.0; A itself flagged possible garbling).
- Persisting through Amd 4 (real-looking, never amended): synopsis "Visits 1a to 24a", ECG "by treatment and visit", 1-month "safety assessments", β-hCG "Visit 1a (predose) only", male contraception, HRUA with no endpoint, PPS "6 study weeks", Chi-square vs normal approx, investigator preference survey, "complete a total of 28 doses", H0 ">0", "stable dose of attenuated androgens".
- Generic M11/SPIRIT items: A ~7 mixed in throughout; B 3, all at the end.

## Verdict
B ≥ A: same K1/K3, B caught K2 cleanly at high confidence where A only grazed it; same bonus hits; similar noise; generics tiered as asked. One-item difference on one trial — directional, not significant.
