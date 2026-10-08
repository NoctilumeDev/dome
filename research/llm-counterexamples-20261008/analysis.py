"""Prospective measurement. No scoring rule chosen from new model outcomes."""
import csv,json,statistics,sys,math
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'llm-core'))
from core import parse_plan,score_plan,canonical,review
from stats import joint,conditioned,conditional_permutation,family_bootstrap,entropy
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def write(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def csvout(p,rows):
 if not rows:return
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ratio(n,d):return n/d if d else None
def signature(p,oracle):
 if p is None:return 'PROTOCOL_OR_TRANSPORT'
 if score_plan(p,oracle)['proposal_correct']:return 'MATCH'
 expected=oracle['allowed'][0]
 if p['action']!=expected['action']:return 'ACTION:'+expected['action']+'->'+p['action']
 return 'FIELDS:'+','.join(k for k,v in expected.items() if p.get(k)!=v)
def ids(d):
 b=d['block'];g=d['group']
 if g.startswith('A:'):return [f'{b}/p/{g[-1]}/0']
 if g=='B':return [f'{b}/p/a/0',f'{b}/p/b/0']
 if g.startswith('C:'):return [f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/{"b/a" if g.endswith("a") else "a/b"}']
 if g=='D':return [f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/a/b',f'{b}/r/b/a']
 if g.startswith('E:'):return [f'{b}/p/{g[-1]}/0',f'{b}/r/{g[-1]}/{g[-1]}']
 return [f'{b}/p/{g[-1]}/{i}' for i in range(int(g[1]))]
def main():
 out=R/'output';out.mkdir(exist_ok=True)
 cases={c['id']:c for c in json.loads((R/'cases.json').read_text(encoding='utf-8'))}
 raw=lines(R/'results/core/calls.jsonl');calls={c['callId']:c for c in raw};assert len(raw)==1536
 blocks=lines(R/'results/core/blocks.jsonl');assert len(blocks)==128
 native={n['callId']:n for s in ('qingye','library') for n in lines(R/f'results/core/native-v2/native-{s}.jsonl')}
 decisions=json.loads((R/'results/core/evaluation-v2/decisions.json').read_text(encoding='utf-8'));by={(d['block'],d['group']):d for d in decisions}
 pairs=[];sample_rows=[]
 for block in blocks:
  case=cases[block['caseId']];b=block['block'];pp={};qual={};valid={};correct={};sig={}
  for m in ('a','b'):
   pool=[];labels=[];bits=[]
   for i in range(4):
    c=calls[f'{b}/p/{m}/{i}'];p,fmt=parse_plan(case['system'],c['rawContent']);p=p if c['complete'] else None
    good=p is not None and score_plan(p,case['oracle'])['proposal_correct'];s=signature(p,case['oracle']);pool.append(canonical(p) if p is not None else 'UNAVAILABLE');labels.append(s);bits.append(good)
    if i==0:pp[m]=p;valid[m]=p is not None;qual[m]=p is not None and native[c['callId']]['nativeQualified'];correct[m]=good;sig[m]=s
   for n in (1,2,3,4):
    group='A:'+m if n==1 else f'F{n}:'+m;d=by[(b,group)]
    sample_rows.append(dict(caseId=case['id'],block=b,stratum=case['stratum'],family=case['family'],model=m,samples=n,planEntropy=entropy(pool[:n]),errorLabelEntropy=entropy(labels[:n]),wrongSamples=sum(not x for x in bits[:n]),modalErrorLabel=Counter(labels[:n]).most_common(1)[0][0],semanticPlanCorrect=d['semanticPlanCorrect'],handlingCorrect=d['handlingCorrect'],publicCompletedCorrect=d['publicCompletedCorrect'],wrongAutomaticExecution=d['wrongAutomaticExecution'],actualStatus=d['actualStatus']))
  eq=pp['a'] is not None and pp['b'] is not None and canonical(pp['a'])==canonical(pp['b'])
  pairs.append(dict(caseId=case['id'],block=b,stratum=case['stratum'],family=case['family'],aCorrect=correct['a'],bCorrect=correct['b'],aValid=valid['a'],bValid=valid['b'],structuralAgreement=eq,qualifiedAgreement=eq and qual['a'] and qual['b'],sameWrongLabel=not correct['a'] and not correct['b'] and sig['a']==sig['b'],sharedOmissionProxy=not correct['a'] and not correct['b'] and sig['a']==sig['b']=='ACTION:CLARIFY->QUERY',aSignature=sig['a'],bSignature=sig['b']))
 risk=[];dependence=[];groups=[];review_net=[]
 strata=list(dict.fromkeys(c['stratum'] for c in cases.values()))
 for stratum in strata:
  part=[p for p in pairs if p['stratum']==stratum];agree=[p for p in part if p['structuralAgreement']];disagree=[p for p in part if not p['structuralAgreement']]
  risk.append(dict(stratum=stratum,n=len(part),bothCorrect=sum(p['aCorrect'] and p['bCorrect'] for p in part),aOnlyCorrect=sum(p['aCorrect'] and not p['bCorrect'] for p in part),bOnlyCorrect=sum(not p['aCorrect'] and p['bCorrect'] for p in part),bothWrong=sum(not p['aCorrect'] and not p['bCorrect'] for p in part),agreementN=len(agree),pCorrectGivenAgreement=ratio(sum(p['aCorrect'] and p['bCorrect'] for p in agree),len(agree)),pWrongGivenAgreement=ratio(sum(not p['aCorrect'] for p in agree),len(agree)),pSharedOmissionProxyGivenAgreement=ratio(sum(p['sharedOmissionProxy'] for p in agree),len(agree)),disagreementN=len(disagree),pACorrectGivenDisagreement=ratio(sum(p['aCorrect'] for p in disagree),len(disagree)),pBCorrectGivenDisagreement=ratio(sum(p['bCorrect'] for p in disagree),len(disagree)),pEitherCorrectGivenDisagreement=ratio(sum(p['aCorrect'] or p['bCorrect'] for p in disagree),len(disagree))))
  for endpoint in ('all_plan_errors','semantic_errors_among_valid_pairs'):
   subset=part if endpoint=='all_plan_errors' else [p for p in part if p['aValid'] and p['bValid']]
   cc=defaultdict(list)
   for p in subset:cc[p['caseId']].append((not p['aCorrect'],not p['bCorrect']))
   if cc:dependence.append(dict(stratum=stratum,endpoint=endpoint,pooled=joint(sum(cc.values(),[])),caseConditionedExcess=conditioned(cc),permutation=conditional_permutation(cc),familyInterval=family_bootstrap(cc,{k:cases[k]['family'] for k in cc}),cases=len(cc),validRepeatsPerCase={k:len(v) for k,v in cc.items()}))
  ds=[d for d in decisions if cases[d['caseId']]['stratum']==stratum]
  for g in dict.fromkeys(d['group'] for d in ds):
   dd=[d for d in ds if d['group']==g];tt=[];cost=[]
   for d in dd:
    callset=[calls[k] for k in ids(d)]
    if all(c['elapsedMs'] is not None for c in callset):tt.append(sum(c['elapsedMs'] for c in callset))
    if all(c['estimatedCostCny'] is not None for c in callset):cost.append(sum(c['estimatedCostCny'] for c in callset))
   groups.append(dict(stratum=stratum,group=g,n=len(dd),expectedQueries=sum(d['expectedQuery'] for d in dd),handlingCorrect=sum(d['handlingCorrect'] for d in dd),semanticPlanCorrect=sum(d['semanticPlanCorrect'] for d in dd),correctQueryOrScope=sum(d['handlingCorrect'] and d['expectedQuery'] for d in dd),correctPublic=sum(d['publicCompletedCorrect'] for d in dd),pendingScope=sum(d['pendingScope'] for d in dd),wrongAutomatic=sum(d['wrongAutomaticExecution'] for d in dd),abstentions=sum(d['actualStatus']=='POLICY_ABSTENTION' for d in dd),meanLogicalCost=statistics.mean(cost) if cost else None,medianLogicalSerialMs=statistics.median(tt) if tt else None))
  for g in ('C:a','C:b','D'):
   added=[]
   for p in part:
    b=by[(p['block'],'B')];d=by[(p['block'],g)]
    if b['selectedPlan'] is not None and d['selectedPlan'] is None:added.append((b,d))
   wrong=sum(not b['semanticPlanCorrect'] and b['selectedPlan']['action']=='QUERY' and b['actualStatus'] in ('QUERY','CONFIRM_SCOPE') for b,d in added)
   right=sum(b['semanticPlanCorrect'] and b['selectedPlan']['action']=='QUERY' and b['actualStatus'] in ('QUERY','CONFIRM_SCOPE') for b,d in added)
   review_net.append(dict(stratum=stratum,group=g,newWrongQueryablePlansVetoed=wrong,newCorrectQueriesBlocked=right,netCountUnweighted=wrong-right,correctClarifyRejudged=sum(b['semanticPlanCorrect'] and b['selectedPlan']['action']=='CLARIFY' for b,d in added),newAbstentions=len(added),wrongAutomaticAvoided=sum(b['wrongAutomaticExecution'] and not d['wrongAutomaticExecution'] for b,d in added)))
 challenge=[];challenges={c['id']:c for c in json.loads((R/'challenge-plans.json').read_text())};cr=lines(R/'results/challenge/calls.jsonl');assert len(cr)==96
 for provider in ('deepseek','qwen'):
  for label in ('correct','wrong'):
   rows=[c for c in cr if c['provider']==provider and challenges[c['challengeId']]['injectedLabel']==label]
   vv=[review(c['rawContent']) if c['complete'] else 'UNAVAILABLE' for c in rows]
   nativeq=[c for c in rows if native['CHALLENGE/'+c['challengeId']]['nativeQualified']]
   challenge.append(dict(provider=provider,label=label,n=len(rows),nativeQualifiedCandidates=len(nativeq),accept=vv.count('ACCEPT'),clarify=vv.count('CLARIFY'),reject=vv.count('REJECT'),unavailable=sum(v not in ('ACCEPT','CLARIFY','REJECT') for v in vv),correctQueryBlocked=sum(label=='correct' and challenges[c['challengeId']]['candidate']['action']=='QUERY' and c['complete'] and review(c['rawContent']) in ('CLARIFY','REJECT') for c in rows)))
 costs=[];plan=json.loads((R/'plan.json').read_text())
 for provider in ('deepseek','qwen'):
  cc=[c for c in raw+cr if c['provider']==provider];value=sum(c.get('estimatedCostCny') or 0 for c in cc)
  costs.append(dict(provider=provider,newCalls=len(cc),newEstimatedCny=value,cumulativeEstimatedCny=plan['priorEstimatedCny'][provider]+value,unknownNew=sum(c.get('estimatedCostCny') is None for c in cc),actualBilling='NOT_VERIFIED',ceiling=20))
 data=dict(risk=risk,dependence=dependence,groups=groups,reviewNet=review_net,challenge=challenge,costs=costs,human='PENDING_HUMAN_STUDY',independentBlindLabels='NOT_RUN',claims='Descriptive/exploratory within frozen distribution, not universal error dependence; synthetic challenge separate from natural error rates')
 write(out/'metrics.json',data);csvout(out/'pair-ledger.csv',pairs);csvout(out/'sampling-ledger.csv',sample_rows);csvout(out/'risk-table.csv',risk);csvout(out/'group-table.csv',groups);csvout(out/'review-net.csv',review_net);csvout(out/'challenge-table.csv',challenge);csvout(out/'cost-table.csv',costs)
 print('Prospective analysis complete:',len(pairs),'paired blocks; no pooled natural/injected denominators')
if __name__=='__main__':main()
