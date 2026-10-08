"""Prespecified endpoints, retaining protocol/semantic/execution distinctions."""
import csv,json,statistics,sys
from collections import defaultdict,Counter
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'llm-core'));sys.path.insert(0,str(R.parent/'llm-counterexamples-20261008'))
from core import parse_plan,score_plan,canonical,decisions,review
from stats import joint,conditioned,conditional_permutation,family_bootstrap,entropy
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def identifiable(cc,families):
 varied={k for k,v in cc.items() if len(v)>=6 and len({x[0] for x in v})>1 and len({x[1] for x in v})>1}
 return len(varied)>=4 and len({families[k] for k in varied})>=2
def csvout(path,rows):
 if not rows:return
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def write(path,x):path.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def main():
 out=R/'output';out.mkdir(exist_ok=True);cases={c['id']:c for c in json.loads((R/'cases.json').read_text())+json.loads((R/'external-cases.json').read_text())}
 allraw=[c for path in (R/'results').glob('*/calls.jsonl') for c in lines(path)];assert len({c['phase']+'/'+c['callId'] for c in allraw})==len(allraw)
 native={n['callId']:n for s in ('qingye','library') for n in lines(R/f'results/native-all/native-{s}.jsonl')}
 detail=[]
 for c in allraw:
  if c['role']!='proposal':continue
  p,fmt=parse_plan(c['system'],c['rawContent']);p=p if c['complete'] else None;n=native[c['phase']+'/'+c['callId']];case=cases[c['caseId']]
  detail.append(dict(phase=c['phase'],callId=c['callId'],caseId=c['caseId'],family=case['family'],stratum=case['stratum'],slot=c['modelSlot'],provider=c['provider'],requestedModel=c['requestedModel'],responseModel=c.get('response',{}).get('model'),transport=c['transport'],format=fmt,valid=p is not None,plan=p,match=p is not None and score_plan(p,case['oracle'])['proposal_correct'],nativeQualified=n['nativeQualified'],entryReachable=n['nativePlannerCalled'],status=n['response']['status'],answer=n['response'].get('answer'),latency=c['elapsedMs'],cost=c['estimatedCostCny']))
 by={(d['phase'],d['callId']):d for d in detail};rawby={(r['phase'],r['callId']):r for r in allraw};rows=[];pairs=[];nets=[];sampling=[]
 for metadata in lines(R/'results/formal/blocks.jsonl'):
  block=metadata['block'];case=cases[metadata['caseId']];pools={};rr={}
  for m in ('a','b'):
   dd=[by['formal',f'{block}/p/{m}/{i}'] for i in range(4)];pools[m]=[d['plan'] if d['nativeQualified'] and d['entryReachable'] else None for d in dd]
   sampling.append(dict(block=block,caseId=case['id'],family=case['family'],model=m,errorBits=[not d['match'] for d in dd],planEntropy=entropy([canonical(d['plan']) if d['valid'] else 'UNAVAILABLE' for d in dd])))
  for rev,prop in (('a','a'),('b','b'),('a','b'),('b','a')):
   c=rawby['formal',f'{block}/r/{rev}/{prop}'];rr[f'{rev}:{prop}']=review(c['rawContent']) if c['complete'] else 'UNAVAILABLE'
  selected=decisions(pools['a'][0],pools['b'][0],rr,pools);lookup={canonical(d['plan']):d for d in detail if d['phase']=='formal' and d['callId'].startswith(block+'/p/') and d['valid'] and d['nativeQualified']}
  for group,p in selected.items():
   d=lookup.get(canonical(p));status=d['status'] if d else 'POLICY_ABSTENTION';match=p is not None and score_plan(p,case['oracle'])['proposal_correct']
   rows.append(dict(block=block,caseId=case['id'],family=case['family'],system=case['system'],group=group,selectedPlan=p,match=match,status=status,queryOrScope=status in ('QUERY','CONFIRM_SCOPE'),wrongQueryable=not match and status in ('QUERY','CONFIRM_SCOPE'),wrongPublicPlan=not match and status=='QUERY'))
  a=by['formal',f'{block}/p/a/0'];b=by['formal',f'{block}/p/b/0'];eq=a['valid'] and b['valid'] and canonical(a['plan'])==canonical(b['plan'])
  pairs.append(dict(block=block,caseId=case['id'],family=case['family'],aCorrect=a['match'],bCorrect=b['match'],aValid=a['valid'] and a['entryReachable'],bValid=b['valid'] and b['entryReachable'],agreement=eq,qualifiedAgreement=selected['B'] is not None))
  bp=selected['B'];bc=bp is not None and score_plan(bp,case['oracle'])['proposal_correct'];query=bp is not None and bp['action']=='QUERY'
  for group,revkeys in [('C:a',['b:a']),('C:b',['a:b']),('D',['b:a','a:b'])]:
   removed=bp is not None and selected[group] is None;explicit=any(rr[k] in ('CLARIFY','REJECT') for k in revkeys);unavailable=any(rr[k] in ('UNAVAILABLE','INVALID_REVIEW') for k in revkeys)
   nets.append(dict(block=block,caseId=case['id'],family=case['family'],group=group,bWrongQueryableOpportunity=bool(bp is not None and not bc and query),explicitNewErrorCatch=bool(removed and not bc and query and explicit),onlyUnavailableDrop=bool(removed and not bc and query and unavailable and not explicit),correctQueryBlocked=bool(removed and bc and query and explicit),correctClarifyRejudged=bool(removed and bc and not query and explicit),additionalAbstention=removed,reviewReasons={k:rawby['formal',f'{block}/r/{k.replace(":","/")}']['rawContent'] for k in revkeys}))
 cc=defaultdict(list)
 for p in pairs:
  if p['aValid'] and p['bValid']:cc[p['caseId']].append((not p['aCorrect'],not p['bCorrect']))
 fam={k:cases[k]['family'] for k in cc};varied=[k for k,v in cc.items() if len(v)>=6 and len({x[0] for x in v})>1 and len({x[1] for x in v})>1]
 dep=dict(status='EXPLORATORY_IDENTIFIABLE' if identifiable(cc,fam) else 'NOT_IDENTIFIABLE',minimumRule='>=4 questions in >=2 families, >=6 valid repeats and both models have within-case 0/1 variation',variableCases=varied,caseRates={k:joint(v) for k,v in cc.items()},caseConditionedExcess=conditioned(cc),permutation=conditional_permutation(cc),familyBootstrap=family_bootstrap(cc,fam),note='Null/constant data never proves error independence; repeats are clustered observations')
 agree=[p for p in pairs if p['agreement']];risk=dict(blocks=len(pairs),questions=len({p['caseId'] for p in pairs}),families=len({p['family'] for p in pairs}),agreement=len(agree),agreementBothMatch=sum(p['aCorrect'] and p['bCorrect'] for p in agree),agreementBothWrong=sum(not p['aCorrect'] and not p['bCorrect'] for p in agree),bothMatch=sum(p['aCorrect'] and p['bCorrect'] for p in pairs),aOnly=sum(p['aCorrect'] and not p['bCorrect'] for p in pairs),bOnly=sum(not p['aCorrect'] and p['bCorrect'] for p in pairs),bothWrong=sum(not p['aCorrect'] and not p['bCorrect'] for p in pairs))
 summary=[]
 for phase in sorted({d['phase'] for d in detail}):
  for stratum in sorted({d['stratum'] for d in detail if d['phase']==phase}):
   for slot in sorted({d['slot'] for d in detail if d['phase']==phase and d['stratum']==stratum}):
    dd=[d for d in detail if d['phase']==phase and d['stratum']==stratum and d['slot']==slot]
    summary.append(dict(phase=phase,stratum=stratum,slot=slot,n=len(dd),questions=len({d['caseId'] for d in dd}),match=sum(d['match'] for d in dd),valid=sum(d['valid'] for d in dd),public=sum(d['status']=='QUERY' for d in dd),wrongPublicPlan=sum(d['status']=='QUERY' and not d['match'] for d in dd),scope=sum(d['status']=='CONFIRM_SCOPE' for d in dd),entryBlocked=sum(not d['entryReachable'] for d in dd),medianLatencyMs=statistics.median(d['latency'] for d in dd),estimatedCny=sum(d['cost'] or 0 for d in dd)))
 groups=[]
 for g in sorted({r['group'] for r in rows}):
  dd=[r for r in rows if r['group']==g];groups.append(dict(group=g,n=len(dd),match=sum(d['match'] for d in dd),publicCorrect=sum(d['match'] and d['status']=='QUERY' for d in dd),wrongPublicPlan=sum(d['wrongPublicPlan'] for d in dd),scope=sum(d['status']=='CONFIRM_SCOPE' for d in dd),abstain=sum(d['status']=='POLICY_ABSTENTION' for d in dd)))
 reviewnet=[]
 for group in ('C:a','C:b','D'):
  dd=[d for d in nets if d['group']==group];fields=['bWrongQueryableOpportunity','explicitNewErrorCatch','onlyUnavailableDrop','correctQueryBlocked','correctClarifyRejudged','additionalAbstention'];reviewnet.append(dict(group=group,**{f:sum(d[f] for d in dd) for f in fields},status='OBSERVED_OPPORTUNITIES' if any(d['bWrongQueryableOpportunity'] for d in dd) else 'NOT_IDENTIFIABLE_ON_THIS_DISTRIBUTION'))
 plan=json.loads((R/'plan.json').read_text());costs=[]
 for provider in ('deepseek','qwen'):
  dd=[r for r in allraw if r['provider']==provider];known=sum(r.get('estimatedCostCny') or 0 for r in dd);unknown=sum(r.get('estimatedCostCny') is None for r in dd);costs.append(dict(provider=provider,requestIdentities=len(dd),knownEstimate=known,unknown=unknown,reserve=unknown*plan['unknownReserveCny'],cumulativeConservative=plan['priorConservativeCny'][provider]+known+unknown*plan['unknownReserveCny'],ceiling=20,actualBilling='NOT_VERIFIED'))
 write(out/'metrics.json',dict(risk=risk,dependence=dep,reviewNet=reviewnet,groups=groups,summary=summary,costs=costs,unrun=['cross-day day1','independent blind labels','real human confirmation'],human='PENDING_HUMAN_STUDY',source='Frozen strict plans and Java/H2 component witnesses. No product edits.'))
 write(out/'proposal-ledger.json',detail);write(out/'decision-ledger.json',rows);write(out/'review-net-ledger.json',nets);write(out/'sampling-ledger.json',sampling);csvout(out/'summary.csv',summary);csvout(out/'pairs.csv',pairs);csvout(out/'review-net.csv',reviewnet);csvout(out/'groups.csv',groups);csvout(out/'costs.csv',costs)
 print('Measured',len(allraw),'request identities;',len(pairs),'formal blocks; dependency',dep['status'])
if __name__=='__main__':main()
