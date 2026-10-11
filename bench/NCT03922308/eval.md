# Blind test 1 — NCT03922308 (Shire SHP655-201), 10 Oct 2026

Reviewer: Opus subagent, given only the BEFORE PDF (Amendment 2.1) + its text extraction; no web, no answer key.
Run: ~4 min, 10 tool calls, ~153K tokens. Brief: see handoff §8 (missing pieces + contradictions only).

## Recall vs answer key (answer_key.md)

| Key | Caught? | Finding |
|---|---|---|
| K1 ECG in App. 2.1, not in SoA | YES (high) | #10 |
| K2 schistocyte smear in incl. 3b, not at screening | NO | — (it did check eligibility vs screening: flagged CD4 in #23, but missed this one; note 3b is "LDH >2-fold **or** schistocytes", so LDH alone satisfies it) |
| K3 prior-treatment 14 vs 30 days | YES (high) | #8 — also named §6.8's 30-day window, the exact inconsistency the sponsor fixed |
| K4 pregnancy test urine vs serum | YES (medium) | #12 |
| K5 (soft) final-visit timing | PARTIAL | #3 (end-visit timing in 3 places; SoA footnote "1 month ± 7 days" changed in Amd 3), #21 |

**Core recall: 3/4 (75%)**, plus partial on K5.

## The other flags (checked by grepping each quote in Amd 2 / 3 / 4 text)

| Bucket | Findings | Meaning |
|---|---|---|
| Matches an Amd-3 change outside the key | #7 (central vs local lab for ADAMTS-13 eligibility; Amd 3 "Clarified that local ADAMTS13 could be used to determine eligibility") | Hit the sponsor labelled as feasibility, not error |
| Text gone/rewritten by Amd 4 (not listed in its change table) | #6 candidate-genes text, #11 ≥ vs > / evaluable cap, #13 screening-before-PEX order, #14 exacerbation def., #20 §6.2.6 post-remission IP, #21 4-month follow-up, #24 "see 5.3.1" bad cross-ref | Likely real; silently fixed or swept up in Amd 4's redesign — can't attribute |
| Quote verified in Amd 2, still present through Amd 4 | #1 as-treated vs as-randomized, #2 analysis sets, #4, #5 contraception 16 vs 30 days, #9, #15, #19, #22, #23 | Real-looking contradictions never amended (useful, unverified as errors) |
| Generic M11/SPIRIT "missing" items | #16 blinding firewall, #17 randomization method, #18 estimands, #25 data sharing/PPI | Plausible, not checkable against amendments |

No fabricated quotes found among those checked.

### Noise audit (read each flag's context in Amd 2 text; judged by us, not a clinical expert)
- Key hits (3): #8, #10, #12
- Real, conflict confirmed in context (7): #1, #2, #3, #7, #9, #19, #22 (troponin appears only in background text, never scheduled)
- Plausible, text later removed/rewritten (7): #6, #11, #13, #14, #20, #21, #24 — not read in depth
- Noise (2): #5 compares different populations/conditions (women "duration of study" vs men 16 d vs conditional 30 d; only App. 4 mistitle is real); #23 template SAE boilerplate + CD4 can be historical
- Borderline (2): #4 (scales stop once normal, by design), #15 (inclusion 4 does mention antibody testing)
- Generic M11/SPIRIT gaps, not verifiable (4): #16, #17, #18, #25
- **False-alarm rate: 2–4 / 25 (8–16%); 6–8 / 25 (24–32%) if generic gaps count as noise.**

## Takeaways
- Contradiction-finding is strong: every core miss/hit was a cross-section check; high-confidence flags were 2/2 on key items.
- Precision vs the key is low (3/25) but most "extras" are verifiable text conflicts, not noise — the answer key (sponsor's change table) undercounts real errors.
- Gap: eligibility-criterion → screening-procedure mapping (K2). Make this an explicit structured check, not a free-text instruction.
- n=1. Not a benchmark.

## Raw findings (condensed)
1. Analysis by treatment received (§9.5) vs FAS as-randomized (§9.4) — high
2. Synopsis analysis sets ≠ §9.4/§9.8.2 sets — high
3. End/early-termination visit timing: 30±5 d (synopsis) vs ≤1 wk (§7.3) vs 1 mo±7 d (SoA fn c) — high
4. Neurocognitive "normalized within 90 days" endpoint but MoCA only to weekly FU wk 4 — high
5. Contraception: duration of study vs 16 d vs 30 d; method strength differs; App. 4 mistitled — high
6. App. 3 pharmacogenetic research vs §8.2.4.3 "not used for exploratory research" — high
7. ADAMTS-13 eligibility: central lab vs local vs bioanalytic lab — high
8. Prior meds: 30 d (§6.8) vs 14 d (§6.8.1) — high
9. AE follow-up: 30 d (§8.1.3) vs to closure (App. 2.2) — high
10. ECG in App. 2.1 but not in SoA — high
11. Platelet cap ≥50,000 enrolled vs >50,000 evaluable — high
12. Pregnancy test serum (SoA) vs urine and/or serum (§5.2.1) vs urine (§8.2.3.5); none at EoS — medium
13. Screening before vs after first SoC PEX — medium
14. Exacerbation def. from PEX stop vs from remission; relapse undefined — medium
15. Antibody confirmation criterion not in I/E; inhibitory vs binding unclear — medium
16. Blinding firewall for local ADAMTS-13 >150% rule missing — medium
17. Randomization method/strata/cap handling missing — medium
18. Co-primary PK/PD analysis, timepoints, estimands missing — medium
19. Trough >10% endpoint missing from Table 4; antibody endpoints classified inconsistently — medium
20. §6.2.6 implies Arm 1 gets no post-remission IP — medium
21. Recurrence follow-up 4 mo vs 3-mo follow-up — medium
22. "Cardiac" end-organ endpoint but no cardiac marker scheduled — medium
23. CD4 exclusion and seroconversion SAE with no matching tests — low
24. Wrong cross-refs (Table 2 fn A, 5.3.1) and PEX numbering — medium
25. No data-sharing, PPI, missing-data approach, bleeding-score source — medium
