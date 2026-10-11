# Sources

## ClinicalTrials.gov (via ctg.py only)
- `ctg.py '{"query.term":"mezigdomide OR CC-92480"}' --pi --max 2000` -> mezi.txt
- `ctg.py '{"query.term":"iberdomide OR CC-220"}' --pi --max 2000` -> iber.txt
- Reused from earlier run in this folder: mm.txt (all myeloma, --pi), nwms.txt, musc.txt
- Trials cited: NCT07032714, NCT06465316, NCT06375044, NCT05896228, NCT07075185, NCT05722418, NCT04068597, NCT06785415, NCT04566328 (https://clinicaltrials.gov/study/<NCT>)

## CMS Open Payments (research payments datastore API)
- https://openpaymentsdata.cms.gov/api/1/metastore/schemas/dataset/items
- https://openpaymentsdata.cms.gov/api/1/datastore/query/{2023,2024,2025 research datasets}/0 with name_of_study LIKE %92480% (mezigdomide) -> op23_s.json, op24_s.json, op25_s.json
- Same endpoint, 2024 dataset, principal_investigator_1_city in {Charleston, Tacoma, Dallas, Philadelphia, San Francisco, New York} and name_of_study LIKE %myeloma% / %RRMM% -> opc_2024_*.json
  (K36 Therapeutics / KTX-1001 payments were deliberately not queried, per rule 2.)

## NPI Registry
- https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1972926871 (Landgren)
- https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1487762118 (Lonial)
- https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1477606309 (Costa, ruled out)
- Earlier-run NPI lookups in npi.txt (name+state queries)

## Web searches (WebSearch) and pages used
- https://cancer.ucsf.edu/HDFCCC_Activation_Policy_for_Industry_Trials.pdf (search result)
- https://investigator.ucsf.edu/node/21 -> https://investigator.ucsf.edu/about-us
- https://www.mayo.edu/research/centers-programs/center-clinical-translational-science/offices/office-of-clinical-trials/sponsor-engagement
- https://www.mayo.edu/research/centers-programs/cancer-research/cancer-clinical-trials/cancer-clinical-trials-office
- https://www.xr.miami.edu/community/sponsor/index.html
- https://whsc.emory.edu/research/wisc/wisc.html
- https://research.massgeneralbrigham.org/en/institutes-centers/cancer-institute-research
- https://www.dana-farber.org/research/our-researchers/administration
- https://www.hackensackmeridianhealth.org/en/services/cancer-care/our-cancer-research
- https://www.mskcc.org/departments/division-solid-tumor-oncology/early-drug-development-service-phase-clinical-trials/contact-us
- https://atriumhealth.org/research-clinical-trials -> https://beinvolved.atriumhealth.org/
- https://medschool.duke.edu/partner-duke-clinical-research
- https://my.clevelandclinic.org/departments/cancer/clinical-trials
- https://www.med.upenn.edu/ocr/ -> https://www.med.upenn.edu/clinicalresearch/
- https://research.musc.edu/resources/ocr -> https://research.musc.edu/about/clinical-research
- https://tnoncology.com/research/
- https://ajmc.com/view/ian-flinn-md-phd-to-serve-as-chief-scientific-officer-for-greco-hainsworth-tennessee-oncology-centers-for-research
- https://www.utsouthwestern.edu/research/clinical-research/
- https://www.nwmedicalspecialties.com/research/for-sponsors/
- https://swog.org/node/1038362 (NWMS SWOG affiliate listing)
- Earlier-run pages (see prior notes): https://profiles.ucsf.edu/ajai.chari, https://www.mskcc.org/cancer-care/doctors/hamza-hashmi, https://www.getcare.muschealth.org/providers/anthony-dominick-1477963676, https://my.clevelandclinic.org/staff/23810-faiz-anwer, https://www.nwmedicalspecialties.com/about-us/

## URL checks (curl/WebFetch) that failed and were replaced
- 404: cancer.ucsf.edu/research/crso, hackensackmeridianhealth.org/.../cancer-care/clinical-trials, atriumhealth.org/medical-services/prevention-wellness/clinical-trials, utsouthwestern.edu/departments/simmons-cancer-center/clinical-trials/, winshipcancer.emory.edu/research/clinical-trials-office
- 403 (bot block, could not open): all mayo.edu pages; tnoncology.com/clinical-trials/ (Cloudflare to curl; tnoncology.com/research/ opened via WebFetch)
