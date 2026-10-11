import csv,re,collections
def parse(fn):
    out=[]
    for line in open(fn):
        p=line.rstrip('\n').split(' | ')
        if len(p)<6: continue
        nct,start,ph,sp=p[:4]; sites=p[-1]
        locs=[]
        for s in sites.split('; '):
            m=re.match(r'(.*?)\s*\(([^,]*), ([^)]*)\)$',s.strip())
            if m: locs.append((m[1].strip().lower(),m[2].strip().lower(),m[3].strip().lower()))
        out.append((nct,start,ph,sp,locs))
    return out
W={'jnj_mm.txt':3,'dara_all.txt':2,'mm_asct.txt':1.5,'mm_maint.txt':1.5,'mm_mrd.txt':1.5}
trials={}
for fn,w in W.items():
    for t in parse(fn):
        k=t[0]; w2=w*(1.5 if 'Janssen' in t[3] else 1)
        trials[k]=max(trials.get(k,(0,None))[0],w2),t
# history
h=collections.defaultdict(list)
for r in csv.DictReader(open('history.csv')):
    h[r['nct']].append((r['facility'],r['city'],r['state'],r['start'],r['sponsor']))
for nct,rows in h.items():
    if nct not in trials:
        trials[nct]=(1,(nct,rows[0][3],'',rows[0][4],[(a,b,c) for a,b,c,_,_ in rows]))
fac=collections.Counter(); city=collections.Counter(); n=collections.Counter()
for nct,(w,t) in trials.items():
    y=int(t[1][:4]) if t[1][:4].isdigit() else 2000
    rec=1.0 if y>=2015 else 0.6 if y>=2010 else 0.25
    for f,c,s in set(t[4]):
        if f: fac[(f,c,s)]+=w*rec; n[(f,c,s)]+=1
        else: city[(c,s)]+=w*rec
import json
json.dump({'fac':[[*k,v,n[k]] for k,v in fac.most_common(400)],'city':[[*k,v] for k,v in city.most_common(60)]},open('scores.json','w'))
for k,v in fac.most_common(150): print(round(v,1),n[k],k)
print('---blank city');[print(round(v,1),k) for k,v in city.most_common(40)]
