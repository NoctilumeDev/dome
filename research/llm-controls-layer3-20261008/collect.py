"""New request identities, immutable measurements, per-request stop and cumulative budget."""
import argparse,getpass,hashlib,importlib.util,json,random,sys,time,warnings
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core'
sys.path.insert(0,str(OLD))
from core import digest
spec=importlib.util.spec_from_file_location('frozen_transport',OLD/'run.py');net=importlib.util.module_from_spec(spec);spec.loader.exec_module(net)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def write(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def check():
 seal=read(R/'seal.json')
 for n,h in seal['research'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,'Frozen research changed: '+n
 for n,h in seal['product'].items():assert hashlib.sha256((R.parents[1]/n).read_bytes()).hexdigest()==h,'Frozen product changed: '+n
 for n,h in seal['immutableImportedTools'].items():assert hashlib.sha256((R.parents[1]/n).read_bytes()).hexdigest()==h,'Frozen imported tool changed: '+n
def schedule(phase,plan,cases):
 selected=[c for c in cases if c['stage']==('formal' if phase in ('formal','tier','day0','day1') else phase)]
 if phase in ('tier','day0','day1'):selected=[c for c in selected if c['variant']==1]
 blocks=[(r,c) for r in range(plan['repetitions'][phase]) for c in selected];rng=random.Random(plan['seed']+sum(map(ord,phase if phase!='day1' else 'day0')));rng.shuffle(blocks)
 for r,c in blocks:
  models=['a','b','ds_pro','q_flash'] if phase=='tier' else ['a','b'];rng.shuffle(models)
  reviews=[('a','a'),('b','b'),('a','b'),('b','a')];rng.shuffle(reviews)
  yield r,c,models,reviews
def main():
 sys.stdout.reconfigure(encoding='utf-8');p=argparse.ArgumentParser();p.add_argument('phase',choices=['pilot','formal','external','tier','day0','day1']);p.add_argument('--keys-stdin',action='store_true',required=True);a=p.parse_args();check()
 plan=read(R/'plan.json');cases=read(R/'cases.json')+(read(R/'external-cases.json') if (R/'external-cases.json').exists() else [])
 out=R/f'results/{a.phase}';out.mkdir(parents=True,exist_ok=True)
 calls=lines(out/'calls.jsonl');existing={r['callId']:r for r in calls};assert len(existing)==len(calls)
 assert not any(r['callId'] not in existing for r in lines(out/'request-journal.jsonl')),'UNKNOWN request: no resubmission'
 done={r['block'] for r in lines(out/'blocks.jsonl')}
 if (out/'summary.json').exists() and read(out/'summary.json').get('stop'):raise SystemExit('Stopped window requires explicit new recovery coordinate, not implicit resume')
 if a.phase=='day1':
  first=read(R/'results/day0/summary.json');elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(first['finishedAt'])).total_seconds()
  assert elapsed>=86400,'Real cross-day window needs >=24h after day0 finish'
 if not sys.stdin.isatty():raise SystemExit('Non-echo credential console required')
 warnings.simplefilter('error',getpass.GetPassWarning);keys=json.loads(getpass.getpass('CREDENTIAL_INPUT: '));assert set(keys)=={'deepseek','qwen'}
 started=datetime.now(timezone.utc).isoformat();stop=None;sch=list(schedule(a.phase,plan,cases));hash_self=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 def totals():
  rr=[r for path in (R/'results').glob('*/calls.jsonl') for r in lines(path)];result={}
  for provider in ('deepseek','qwen'):
   pp=[r for r in rr if r['provider']==provider];value=sum(r.get('estimatedCostCny') or 0 for r in pp)+plan['unknownReserveCny']*sum(r.get('estimatedCostCny') is None for r in pp);result[provider]=value
  return result
 def invoke(cid,role,model,case,body):
  if cid in existing:assert existing[cid]['requestHash']==digest(body);return existing[cid]
  check();tt=totals()
  if sum(tt.values())+.10>plan['newBudgetCny'] or tt[plan['providers'][model]['name']]+plan['priorConservativeCny'][plan['providers'][model]['name']]+.10>20:raise RuntimeError('BUDGET_BOUNDARY')
  prior=lines(out/'calls.jsonl')
  if sum(r.get('estimatedCostCny') is None for r in prior)>=3:raise RuntimeError('USAGE_UNAVAILABLE')
  if sum(r['transport']!='SUCCESS' for r in prior)>=max(5,len(prior)//5):raise RuntimeError('TRANSPORT_BOUNDARY')
  net.append(out/'request-journal.jsonl',dict(callId=cid,state='STARTED',requestHash=digest(body),startedAt=datetime.now(timezone.utc).isoformat()))
  provider=plan['providers'][model];observed=net.request(provider['url'],keys[provider['name']],body,plan['deadlineMs'])
  record=dict(callId=cid,phase=a.phase,role=role,caseId=case['id'],system=case['system'],provider=provider['name'],modelSlot=model,requestedModel=provider['model'],collectorSha256=hash_self,requestHash=digest(body),request=body,observedAt=datetime.now(timezone.utc).isoformat(),**observed)
  record['estimatedCostCny']=net.estimate_cost(record,provider);choices=record.get('response',{}).get('choices',[]);record['rawContent']=choices[0].get('message',{}).get('content','') if choices else '';record['complete']=bool(choices) and choices[0].get('finish_reason')=='stop' and record['transport']=='SUCCESS'
  net.append(out/'calls.jsonl',record);existing[cid]=record
  if record.get('httpStatus') in (401,403):raise RuntimeError('AUTHENTICATION_BLOCK')
  return record
 try:
  for r,c,models,reviews in sch:
   block=f'{c["id"]}-r{r}'
   if block in done:continue
   prompt=(R/f'prompts/{c["system"]}.txt').read_text(encoding='utf-8');pools={}
   for model in models:
    pools[model]=[]
    for i in range(4 if a.phase=='formal' else 1):
     body=net.payload(plan['providers'][model],prompt,c['question'],plan['maxTokens'][c['system']]);pools[model].append(invoke(f'{block}/p/{model}/{i}','proposal',model,c,body))
   if a.phase=='formal':
    review_prompt=(R/'prompts/review.txt').read_text(encoding='utf-8')+'\n被审系统协议与公开目录：\n'+prompt
    for rev,prop in reviews:
     text=json.dumps({'question':c['question'],'candidate':pools[prop][0]['rawContent']},ensure_ascii=False)
     invoke(f'{block}/r/{rev}/{prop}','review',rev,c,net.payload(plan['providers'][rev],review_prompt,text,250))
   net.append(out/'blocks.jsonl',dict(block=block,caseId=c['id'],repeat=r,completed=True));done.add(block)
   print(json.dumps(dict(phase=a.phase,blocks=len(done),planned=len(sch),calls=len(existing),estimatedNew=totals()),ensure_ascii=False),flush=True)
 except (RuntimeError,AssertionError) as e:stop=str(e);print('STOP='+stop,flush=True)
 except KeyboardInterrupt:stop='INTERRUPTED';raise
 finally:
  keys.clear();summary=dict(phase=a.phase,startedAt=started,finishedAt=datetime.now(timezone.utc).isoformat(),completedBlocks=len(done),plannedBlocks=len(sch),requestIdentities=len(existing),stop=stop,estimatedAllNew=totals(),actualBilling='NOT_VERIFIED');write(out/'summary.json',summary)
 print('COLLECTION_EXIT='+json.dumps(summary),flush=True)
if __name__=='__main__':main()
