import json,urllib.request,sys,collections
IDS={"2023":"ec9521bf-9d97-4603-814c-f4132d34bc4f","2024":"2f15cb85-8887-4dcc-a318-1f8ec1d815b3","2025":"f0d1de67-6852-4093-a036-c9328c256a05"}
N=["SCHILLER","YOUNG","ALSINA","BLUE","SHAIN","USMANI","LESOKHIN","HULTCRANTZ","ORLOWSKI","YE","KAZANDJIAN","LANDGREN","STEVENS","AFROUGH","KAPOOR","KUMAR","MALY","HOFFMAN"]
out=[]
for y,i in IDS.items():
    off=0
    while True:
        body={"conditions":[{"property":"principal_investigator_1_last_name","value":N,"operator":"in"}],"limit":500,"offset":off,
              "properties":["clinicaltrials_gov_identifier","name_of_study","applicable_manufacturer_or_applicable_gpo_making_payment_name","teaching_hospital_name","principal_investigator_1_first_name","principal_investigator_1_last_name","principal_investigator_1_city","name_of_drug_or_biological_or_device_or_medical_supply_1","total_amount_of_payment_usdollars"]}
        r=json.load(urllib.request.urlopen(urllib.request.Request(f"https://openpaymentsdata.cms.gov/api/1/datastore/query/{i}/0",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"}),timeout=300))
        res=r.get("results",[]); [x.update(year=y) for x in res]; out+=res
        print(y,off,len(res),r.get("count"),file=sys.stderr)
        if len(res)<500: break
        off+=500
json.dump(out,open("names.json","w"))
