# Site requirements: NCT05730036 (LINKER-MM3), linvoseltamab vs EPd in RRMM

Each item names the protocol line or public source it comes from. "protocol.md" means the sponsor synopsis in this folder. "Label" means the LYNOZYFIC (linvoseltamab-gcpt) US Prescribing Information (regeneron.com/downloads/lynozyfic_fpi.pdf). The label covers commercial use; the protocol may differ, so treat label-derived items as expected trial practice.

## Patient population and enrollment
- R1. Enough patients with RRMM after 1-4 prior lines, including lenalidomide and a PI, with progression on or after the last line (len-refractory if only 1 line). Source: protocol.md, Inclusion 3.
- R2. Patients must not have had elotuzumab, pomalidomide or BCMA-directed immunotherapy (BCMA ADCs are allowed). This shrinks the pool at a CAR-T and bispecific-heavy center. Source: protocol.md, Exclusions 2 and 6.
- R3. Patients must have ECOG <=1, measurable disease (IMWG 2016), life expectancy >=6 months, EF >=40%, no known CNS myeloma, and no PML or neurocognitive or movement disorder. Source: protocol.md, Inclusions 2, 4 and 6; Exclusions 3, 7 and 9/10.
- R4. The site must manage enrollment against competing trials for the same patients (RRMM, len-exposed). Source: protocol.md population; ctg.py site search.
- R5. The site must handle 1:1 randomization to an open-label control arm, so patients and investigators have to accept EPd. Source: protocol.md header ("randomized 1:1").

## Linvoseltamab arm (T-cell engager)
- R6. IV infusion with step-up dosing: 5 mg on D1, 25 mg on D8, 200 mg on D15. Then 200 mg weekly through week 13, every 2 weeks from week 14, and every 4 weeks from week 24 if VGPR or better. Source: Label sections 2.2 and 6.1; LINKER-MM1 (OncLive, Aetna CPB 1089).
- R7. Inpatient admission for 24 h after step-up dose 1 and 24 h after step-up dose 2. This needs available inpatient beds. Source: Label section 2.1.
- R8. Immediate access to emergency equipment and staff able to manage CRS, IRR and ICANS, including tocilizumab, ICU and neurology. Source: Label section 2.1 and boxed warning; CRS peaks 6-8 h after the first step-up dose (Pharmacy Times, 2026).
- R9. Premedication before doses, and re-step-up dosing (restart at 5 mg or 25 mg) after dose delays. The site needs scheduling flexibility for re-admissions. Source: Label sections 2.3 and 2.4.
- R10. Infection monitoring and prophylaxis: IgG monitoring, IVIG or SCIG, PJP and herpesvirus prophylaxis, and vaccines. Serious infections occurred in 42% of patients, and 2 PML cases were seen. Source: Label section 5.4.
- R11. Counsel patients not to drive for 48 h after each step-up dose, and hand out the patient wallet card. Source: Label sections 5.2 and 5.3.
- R12. Commercial LYNOZYFIC REMS certification of prescribers, pharmacy and healthcare setting. This is not needed for investigational supply, but it shows readiness. Source: Label section 5.3.
- R13. Investigational pharmacy that can store vials at 2-8 C, dilute in 0.9% NaCl and use compatible IV tubing. Diluted drug must be used within 8 h at room temperature or 48 h refrigerated. Source: Label section 2.6.

## EPd comparator arm
- R14. Elotuzumab IV at 10 mg/kg weekly in cycles 1-2, then 20 mg/kg every 4 weeks, with premedication (dexamethasone IV, H1, H2, acetaminophen). This needs infusion-chair capacity. Source: Empliciti USPI and SmPC.
- R15. Pomalidomide 4 mg on D1-21 of each 28-day cycle. Prescribers and pharmacy must be certified in PS-Pomalidomide REMS, with pregnancy testing and contraception counseling. Source: Pomalyst USPI (PS-PomalidomideREMS.com).
- R16. Weight-based dexamethasone dosing (by age, 75 or under vs over 75). Source: Empliciti label.

## Assessments and data
- R17. Local labs (hematology, hepatic, renal, calcium) within 7 days before randomization, plus cardiac function (EF). Source: protocol.md, Inclusion 5 and Exclusion 10.
- R18. IMWG response assessments with central Independent Review Committee (IRC) review. Requires timely M-protein, free light chain, bone marrow and imaging submission. Source: protocol.md Outcomes (PFS/OR by IRC).
- R19. Bone marrow sampling for MRD and shipping to a central lab. Source: protocol.md Outcomes (MRD negativity, duration).
- R20. Serum PK, ADA and NAb sampling, which needs a centrifuge, a -70/-80 C freezer and shipping. Source: protocol.md Outcomes (concentration, ADA, NAb).
- R21. PRO collection: BPI-SF item 3, EORTC QLQ-C30, QLQ-MY20, PGIS, PGIC and EQ-5D-5L. Source: protocol.md Outcomes.
- R22. Long-term follow-up for OS, and SAE/AESI reporting. Source: protocol.md Outcomes.

## Regulatory and operations
- R23. Ability to work with an IRB of record (central or local) and to execute the contract and budget quickly. Source: Atrium IRB pages (Advarra, Chesapeake, Copernicus, WFUHS IRB history).
- R24. A qualified PI and sub-investigators with myeloma and T-cell-engager experience, plus a coordinator. Source: ICH E6 investigator qualification; protocol complexity above.
