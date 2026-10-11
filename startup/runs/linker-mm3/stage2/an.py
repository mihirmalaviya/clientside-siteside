import re,collections
SITES={1:r"Memorial Sloan|MSK",2:r"Ohio State|James Cancer",3:r"Weill|Cornell",4:r"University of Michigan|Michigan Medicine|Rogel",5:r"UT Southwestern|Southwestern|Simmons",6:r"Mayo Clinic.*\(Rochester",7:r"M\.? ?D\.? Anderson.*\(Houston",8:r"Norton",9:r"Dana[- ]Farber",10:r"UCLA|University of California,? Los Angeles|Ronald Reagan",11:r"Miami|Sylvester",12:r"Moffitt"}
BIS=r"linvoseltamab|REGN5458|REGN5459|odronextamab|teclistamab|elranatamab|talquetamab|cevostamab|ABBV-383|etentamig|alnuctamab|forimtamig|REGN|TNB-383|bispecific|JNJ-|AMG 701|pavurutamab|linvo"
pis=collections.defaultdict(lambda: collections.defaultdict(lambda: {"bis":[],"rr":[],"rec":0,"regn":[]}))
for line in open("mm.txt"):
    f=line.rstrip("\n").split(" | ")
    if len(f)<10: continue
    nct,start,ph,st,typ,sp,title,cond,drugs,us=f[:10]
    text=title+" "+drugs
    for loc in us.split("; "):
        m=re.search(r"\[PI: (.*)\]",loc)
        if not m: continue
        for k,pat in SITES.items():
            if re.search(pat,loc,re.I) and (k!=11 or "Miami" in loc) :
                for p in m.group(1).split(", "):
                    if not p or p in ("MD","PhD","M.D.","MBBS"): continue
                    d=pis[k][p]
                    if st=="RECRUITING": d["rec"]+=1
                    if "Regeneron" in sp: d["regn"].append(nct)
                    elif re.search(BIS,text,re.I): d["bis"].append(nct)
                    if re.search(r"relapse|refractory",title+cond,re.I) and ph and "3" not in ph or "PHASE1" in ph: d["rr"].append(nct)
for k in sorted(pis):
    print("== ",k)
    for p,d in sorted(pis[k].items(),key=lambda x:-(len(x[1]["regn"])*5+len(x[1]["bis"])*2+x[1]["rec"])) [:10]:
        print(f'  {p}: rec={d["rec"]} regn={d["regn"]} bis={len(d["bis"])} rr={len(d["rr"])}')
