"""New physical identities over frozen payloads; original transport, no retries."""
import argparse,copy,getpass,hashlib,importlib.util,json,os,pathlib,sys,warnings
from datetime import datetime,timezone
from zoneinfo import ZoneInfo

R=pathlib.Path(__file__).resolve().parent; REPO=R.parents[1]
sys.path.insert(0,str(REPO/'research/llm-core'))
spec=importlib.util.spec_from_file_location('final_frozen_net',REPO/'research/llm-core/run.py')
net=importlib.util.module_from_spec(spec);spec.loader.exec_module(net)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def check(runtime=False):
 seal=read(R/'seal.json')
 selected=seal['runtime'] if runtime else seal['inputs']
 for n,h in selected.items():
  assert hashlib.sha256((REPO/n).read_bytes()).hexdigest()==h,'Frozen input changed: '+n
def totals(manifest,observed):
 result=dict(manifest['historicalConservativeCny'])
 for x in observed:
  result[x['provider']]+=x.get('estimatedCostCny') if x.get('estimatedCostCny') is not None else manifest['unknownUsageReserveCny']
 return result
def stage_guard(suite):
 previous=suite['guardAfterFinishedSuite']
 if not previous:return None
 summary=read(R/'results'/previous/'summary.json')
 assert summary['stop'] is None and summary['requests']==summary['plannedRequests'],'Earlier stage incomplete'
 now=datetime.now(timezone.utc);done=datetime.fromisoformat(summary['finishedAt']);seconds=(now-done).total_seconds()
 assert seconds>=suite['minimumGapSeconds'],'WAIT_24H'
 assert now.astimezone(ZoneInfo('Asia/Shanghai')).date()>done.astimezone(ZoneInfo('Asia/Shanghai')).date(),'WAIT_SHANGHAI_DATE'
 return dict(predecessor=previous,finishedAt=summary['finishedAt'],observedAt=now.isoformat(),gapSeconds=seconds)

def main():
 sys.stdout.reconfigure(encoding='utf-8');p=argparse.ArgumentParser();p.add_argument('suite');a=p.parse_args()
 check();manifest=read(R/'matrix.json');suite=next(x for x in manifest['suites'] if x['id']==a.suite)
 out=R/'results'/a.suite
 if out.exists():raise SystemExit('Candidate already attempted; no implicit resubmission')
 gap=stage_guard(suite)
 jobs=[x for x in rows(R/'jobs.jsonl') if x['suite']==a.suite]
 retained=[x for path in sorted((R/'results').glob('*/calls.jsonl')) for x in rows(path)]
 history={x['callId']:x for x in retained};assert len(history)==len(retained)
 for path in (R/'results').glob('*/request-journal.jsonl'):
  assert all(x['callId'] in history for x in rows(path)),'UNKNOWN attempts prohibit continuation'
 if suite['kind']=='pool_review':
  source='query-day1' if a.suite.endswith('day1') else 'query-day0'
  predecessor=read(R/'results'/source/'summary.json')
  assert predecessor['stop'] is None and predecessor['requests']==234
  pool=R/'results'/source/'calls.jsonl'
  write(R/'review-pools'/f'{a.suite}.json',dict(source=source,sha256=hashlib.sha256(pool.read_bytes()).hexdigest(),requests=234,sealedAt=datetime.now(timezone.utc).isoformat()))
 if not sys.stdin.isatty():raise SystemExit('Non-echo console required')
 warnings.simplefilter('error',getpass.GetPassWarning);keys=json.loads(getpass.getpass('CREDENTIAL_INPUT: '));assert set(keys)=={'deepseek','qwen'}
 out.mkdir(parents=True);start=datetime.now(timezone.utc).isoformat();done=[];stop=None
 try:
  for job in jobs:
   check(runtime=True)
   if suite['guardAfterFinishedSuite']:stage_guard(suite)
   cumulative=totals(manifest,retained)
   if cumulative[job['provider']]+manifest['reserveBeforeEachRequestCny']>manifest['hardCumulativePerProviderCny']:raise RuntimeError('BUDGET_BOUNDARY')
   if sum(x.get('estimatedCostCny') is None for x in done)>=manifest['maximumMissingUsageBeforeStop']:raise RuntimeError('USAGE_UNAVAILABLE')
   if sum(x['transport']!='SUCCESS' for x in done)>=max(manifest['transportStopMinimum'],int(len(done)*manifest['transportStopFraction'])):raise RuntimeError('TRANSPORT_BOUNDARY')
   body=copy.deepcopy(job['request']);candidate=None
   if job['candidateDependency']:
    source=history[job['candidateDependency']];candidate=source['rawContent']
    content=json.loads(body['messages'][-1]['content']);content['candidate']=candidate
    body['messages'][-1]['content']=json.dumps(content,ensure_ascii=False)
   payload_hash=net.digest(body);cid=job['callId']
   net.append(out/'request-journal.jsonl',dict(callId=cid,requestHash=payload_hash,state='STARTED',startedAt=datetime.now(timezone.utc).isoformat(),candidateDependency=job['candidateDependency'],candidateSha256=hashlib.sha256(candidate.encode()).hexdigest() if candidate is not None else None,cumulativeBefore=cumulative))
   observed=net.request(job['providerSpec']['url'],keys[job['provider']],body,job['deadlineMs'])
   choices=observed.get('response',{}).get('choices',[])
   record=dict(callId=cid,legacyCallId=job['legacyCallId'],suite=a.suite,role=job['role'],caseId=job['caseId'],system=job['system'],provider=job['provider'],requestedModel=body['model'],request=body,requestHash=payload_hash,sourceRequestHash=job['sourceRequestHash'],candidateDependency=job['candidateDependency'],observedAt=datetime.now(timezone.utc).isoformat(),rawContent=choices[0].get('message',{}).get('content','') if choices else '',complete=bool(choices) and choices[0].get('finish_reason')=='stop' and observed.get('transport')=='SUCCESS',sourceMetadata=job['sourceMetadata'],**observed)
   record['estimatedCostCny']=net.estimate_cost(record,job['providerSpec'])
   net.append(out/'calls.jsonl',record);done.append(record);retained.append(record);history[cid]=record
   if record.get('httpStatus') in manifest['authenticationStopStatuses']:raise RuntimeError('AUTHENTICATION_BLOCK')
   if len(done)%24==0 or len(done)==len(jobs):print(json.dumps({'suite':a.suite,'requests':len(done),'planned':len(jobs),'allFreshRequests':len(retained),'globalConservativeCny':totals(manifest,retained)},ensure_ascii=False),flush=True)
 except (AssertionError,RuntimeError,KeyError) as e:stop=str(e);print('STOP='+stop,flush=True)
 except KeyboardInterrupt:stop='INTERRUPTED';raise
 finally:
  keys.clear();summary=dict(suite=a.suite,startedAt=start,finishedAt=datetime.now(timezone.utc).isoformat(),requests=len(done),plannedRequests=len(jobs),stop=stop,gap=gap,globalConservativeCny=totals(manifest,retained),actualCash='NOT_VERIFIED')
  write(out/'summary.json',summary);print('COLLECTION_EXIT='+json.dumps(summary),flush=True)
 if stop:raise SystemExit(2)

if __name__=='__main__':main()
