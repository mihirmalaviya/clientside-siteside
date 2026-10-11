# Riverside Cancer Center: synthetic site data spec

Ground truth for the synthetic site the **site agent** works from. Every file must agree with this spec.
The site agent will later see ONLY `site_data/riverside/` (public/ + confidential/). This spec and `site_data/key/` are
answer material: never copy spec text verbatim into site files, and never put keys inside `riverside/`.

"Today" for all data is **2026-10-11**. "Last 12 months" means **2025-10-01 to 2026-09-30**.

## Hard rules (all files)
- Fictional site: Riverside Cancer Center, part of Riverside Medical Center, Dayton, Ohio. Research office: "Riverside Cancer Research Office".
- No real hospitals, clinics, universities, labs, imaging centers or people tied to fictional facts. Replace any (e.g. "Miami Valley ..."
  is a real Dayton name, use "Valley Apheresis Partners" instead; CV schools become fictional, e.g. "Great Lakes University").
  Real vendors, regulators and standards are fine (FDA, CLIA, CAP, Epic, Medidata Rave, Veeva, WCG IRB, FedEx, IATA, ASTCT).
- No real-looking registry IDs. Trials use internal codes (ALD-201) and public listings use "SYN-" IDs (SYN-0001), never NCT numbers.
- Real drug names are fine (lenalidomide, pomalidomide, daratumumab, teclistamab, ...). Fictional sponsors only:
  Alder Therapeutics, Corvane Bio, Halvorsen Pharma, Meridian Oncology, plus new fictional ones if needed (e.g. Brightwater Biologics).

## Existing documents (copy into confidential/, keep their facts, apply the rules above)
Originals: `agent_runs/site/riverside/docs/`. Three past questionnaires (2023 Alder, 2024 Corvane, 2025 Halvorsen), CRS/ICANS SOP v2
(2025-03), CV of Dr. Elena Marsh, capabilities (2026-02), staff roster (2026-01), trial history. Their deliberately stale answers stay
stale (e.g. 2023 says 2 CRCs, 1 freezer, outpatient step-up); newer files win.

## People (staff roster, updated 2026-09)
Keep everyone in the 2026-01 roster with the same GCP dates (Dr. Raj Patel's GCP expired 2025-11-30 and is still not renewed; he is PI of
the recruiting MRD-088). Add per person: `fte` (1.0 unless noted), `committed_effort` (share of FTE already committed to active trials),
`iata_shipping_cert_expires` (CRCs only).
CRCs and their free capacity (fte - committed): Maya Chen 0.1, Tom Reyes 0.2, Priya Nair 0.3, Sam Ortiz 0.4 → **1.0 FTE available**.
IATA dangerous-goods shipping certificates current for Tom Reyes and Priya Nair only.
6 West nursing: 24 nurses; 22 have current ICE/ICANS training (record dated 2026-08); policy: only ICE-trained nurses are assigned to
step-up dosing patients.

## Facilities and capabilities (current as of 2026-09)
- ICU 24 beds, same building. 6 West inpatient oncology; 4 beds reserved for research step-up dosing admissions (SOP v2).
- Infusion center: **18 chairs** (public website still says 16, stale).
- -80C freezers: **2**, continuously monitored, alarm + backup power. -20C: 1. Refrigerated centrifuge.
- Lab CLIA certified (CLIA #36D9999999) and CAP accredited. Bone marrow aspirate/biopsy on site. MRD by NGS: send-out only.
- Fresh bone marrow aspirate to a central lab: **yes**, FedEx Priority Overnight, pickup 16:30 Mon-Thu; Friday collections cannot ship
  same day (stored per lab manual or rescheduled). Packed by IATA-certified CRCs.
- Imaging: MRI 1.5T and CT on site. PET-CT **not** on site: Valley Imaging Partners, ~5 business days. Echocardiogram and ECG on site.
- Apheresis: not on site (Valley Apheresis Partners).
- ePRO: **yes**, staff hand out and collect sponsor-provided tablets at clinic visits; guest Wi-Fi; done on HLV-330.
- EMR Epic; monitors get remote read-only access. EDC experience: Medidata Rave, Veeva Vault EDC.
- Lodging: partner hotel Riverside Inn, 10 minutes away, discounted.
- Not FACT accredited; not NCI-designated. No on-site transplant program (refers out). Commission on Cancer accredited.

## Pharmacy
- Investigational drug service, pharmacist Dana Wolfe (dedicated). 2-8C and room-temperature storage with continuous logging.
- Pomalidomide REMS: **certified** (pharmacy and Dr. Marsh, Dr. Okafor registered prescribers; Dr. Patel not).
- Tocilizumab: SOP v2 keeps >= 2 doses per enrolled T-cell-engager patient on site; inpatient pharmacy open 24/7 → can be given within
  2 hours of CRS diagnosis 24/7: **yes**.
- IV investigational dose prep-to-release time: logged per dose in the ops log (median about 45 min).

## Contracts, budget, IRB
- Overhead (indirect) rate: **29%, effective 2026-07-01** (FY2027 rate; 2025 questionnaire's 28% is stale).
- Local Riverside IRB and WCG central IRB both accepted.
- Ops log records protocol-received, IRB-approved and CTA-executed dates per trial. Key rule for "weeks from final protocol to executed
  CTA + budget, industry Phase 3": median over industry Phase 3 trials whose CTA was executed in the last 3 years (target ~11 weeks;
  the 2025 questionnaire's "10 weeks" was all phases).

## Trials (portfolio = history + active + pipeline)
Keep all 7 trials from trial_history.csv with their facts. Add per trial: `target_enrollment`, `screened`, `enrolled`, `screen_failed`,
`days_activation_to_first_patient`, and an `eligibility_population` tag. Add 3-5 older completed trials (2016-2019) for history.
Pipeline under confidentiality agreement (CDA), not public, expected to open in the next 12 months:
- CRV-510 (Corvane Bio) RRMM, 1-4 prior lines, BCMA-naive, opens ~2027-01  → same population
- BRW-220 (Brightwater Biologics) RRMM, 1-3 prior lines, BCMA-naive, opens ~2027-06 → same population
- ALD-530 (Alder Therapeutics) newly diagnosed MM → not same population
- MRD-140 (Meridian Oncology) RRMM after prior BCMA therapy → not same population
Answer to "not-yet-public trials for the same population (RRMM, 1-4 prior lines, BCMA-naive) next 12 months": **2**.
The site may share the count, but never the sponsors, drugs or codes of CDA trials.

## Disclosure policy (confidential/disclosure_policy.md)
- Share with sponsors: aggregate counts, percentages, medians, capabilities, own rates and timelines.
- Never share: anything patient-level (names, dates of birth, addresses, MRNs, individual dates or histories), other sponsors'
  confidential protocol details, budgets or CDA pipeline identities, staff personal contact details.
- Patient counts are reported as numbers (no small-cell suppression), rounded to whole patients.

## Patients (EHR export, two files: ehr_patients.csv, ehr_events.csv)
General Dayton-area population from Synthea plus a myeloma program overlay. Targets (exact values come from the generated data and
go into the key):
- RRMM patients seen per year ~70 (consistent with the 2025 questionnaire).
- Q1 rule: patients with a myeloma-program new-patient visit in the last 12 months who at that visit had relapsed/refractory MM after
  1-4 prior lines including lenalidomide and a proteasome inhibitor. Target ~45.
- Q2: % of those never exposed to pomalidomide. Target ~55%.
- Q3: % of those never exposed to a BCMA-directed bispecific (teclistamab, elranatamab, linvoseltamab, ...) or BCMA CAR-T
  (cilta-cel, ide-cel). Target ~80%. Belantamab mafodotin is a BCMA antibody-drug conjugate and does NOT count (trap).
- Q4: share of outside-referred patients among them whose complete prior-therapy records were available at the screening visit.
  Target ~50%. Mapping: >=75% "most", 40-75% "some", <40% "few".
- Eligibility estimate for the new trial (patients in the last 12 months meeting: ECOG <= 1, 1-4 prior lines incl. lenalidomide and a
  PI, len-refractory if only 1 line, no prior pomalidomide or elotuzumab, no prior BCMA-directed immunotherapy (ADC allowed), no plasma
  cell leukemia / amyloidosis / POEMS / Waldenstrom, EF >= 40%). Target ~12-18.

## Operations log (ops_log.csv), last 12 months unless noted
- Pharmacy: IV investigational dose prep-to-release minutes, one row per dose (~120 rows), median ~45.
- Infusion: lead time in days to book a recurring weekly chair slot, one row per booking request (~40), median ~10 → key = median.
- Step-up admissions: planned 24-hour admission requests (~30) with scheduled_on_requested_day yes/no, ~85% yes.
  Mapping: >=95% "always", 70-95% "usually", <70% "rarely".
- IRB and contract milestone dates per trial (all years).

## Public folder (what anyone can see)
- website.md: about page, services, the clinical trials office "for sponsors" page, lodging, accreditations. Deliberately stale on
  infusion chairs (16).
- registry_listings.md: registry-style entries (SYN- IDs) for the site's public trials only (completed + recruiting; never pipeline).
- publications.md: Dr. Marsh's and Dr. Okafor's publications/abstracts (fictional titles; journals described generically, e.g.
  "peer-reviewed hematology journal, 2024"; no real journal or conference names).

## Keys (site_data/key/, never inside riverside/)
Each generator writes a JSON key: question → value, rule used, and which file(s) answer it, plus "confidential": true/false.
