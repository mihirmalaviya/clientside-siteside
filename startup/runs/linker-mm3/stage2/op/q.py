import json,urllib.request,sys
IDS={"2020":"9c248e7e-7c7f-478b-ab84-ce0919d72c1c","2021":"ce1d28dd-0094-5060-a036-580329439600","2022":"fdc3c773-018a-412c-8a81-d7b8a13a037b","2023":"ec9521bf-9d97-4603-814c-f4132d34bc4f","2024":"2f15cb85-8887-4dcc-a318-1f8ec1d815b3","2025":"f0d1de67-6852-4093-a036-c9328c256a05"}
NCT=["NCT03761108","NCT04083534","NCT05137054","NCT05828511","NCT06140524","NCT06292780","NCT05955508","NCT06669247","NCT07222761","NCT07393282"]
out=[]
for y,i in IDS.items():
    off=0
    while True:
        body={"conditions":[{"property":"clinicaltrials_gov_identifier","value":NCT,"operator":"in"}],"limit":500,"offset":off,
              "properties":["clinicaltrials_gov_identifier","teaching_hospital_name","noncovered_recipient_entity_name","principal_investigator_1_first_name","principal_investigator_1_last_name","principal_investigator_1_city","principal_investigator_1_state","principal_investigator_2_first_name","principal_investigator_2_last_name","total_amount_of_payment_usdollars","date_of_payment","recipient_city","recipient_state"]}
        r=json.load(urllib.request.urlopen(urllib.request.Request(f"https://openpaymentsdata.cms.gov/api/1/datastore/query/{i}/0",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"}),timeout=120))
        res=r.get("results",[]); [x.update(year=y) for x in res]; out+=res
        print(y,off,len(res),r.get("count"),file=sys.stderr)
        if len(res)<500: break
        off+=500
json.dump(out,open("regn.json","w"))
