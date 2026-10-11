import re,collections
def site(s):
    f=s.split(' (')[0]
    if re.search('wake forest|navicent|middletown|dayton|children',f,re.I): return False
    return bool(re.search(r'levine cancer|LCI-|carolinas medical center|carolinas healthcare system|atrium health|atrium levine',f,re.I))
rows=[]
for l in open('mm.txt'):
    p=l.rstrip('\n').split(' | ')
    hits=[s for s in p[9].split('; ') if site(s)]
    if hits and p[4]=='INTERVENTIONAL' and p[3]!='WITHDRAWN': rows.append(p+[hits])
print('L1',len(rows))
print('L2',sum(r[1]>='2021-10-11' for r in rows))
rec=[r for r in rows if r[3]=='RECRUITING']; print('L3',len(rec))
pis=collections.Counter()
for r in rec:
    for h in r[10]:
        for m in re.findall(r'\[PI: (.*?)\]',h): 
            for n in m.split(', '): pis[n]+=1
print(pis)
ind=collections.Counter(r[5] for r in rows); print(ind.most_common(15))
print(collections.Counter(r[3] for r in rows))
for r in rows: print(r[0],r[1],r[3],r[5],'|',r[6][:80],'|',r[8][:150])
tce=r'teclistamab|talquetamab|linvoseltamab|elranatamab|etentamig|TNB-383B|ABBV-383|JNJ-79635322|AMG 701|LAVA-051|cevostamab|alnuctamab|bispecific'
t=[r for r in rows if re.search(tce,r[8]+r[6],re.I)]
print('TCE',len(t),[ (r[0],r[1]) for r in t])
car=[r for r in rows if re.search(r'cilta|JNJ-68284528|bb2121|ide-cel|idecabtagene|anitocabtagene|CB-011|BMS-986393|BCMA CAR',r[8]+r[6],re.I)]
print('CAR',[(r[0],r[6][:50]) for r in car])
for r in rec: print(r[0],r[10])
