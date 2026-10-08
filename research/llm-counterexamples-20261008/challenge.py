"""Blind review of predeclared correct/error plans, separate from natural agreement."""
import getpass,hashlib,json,random,sys,warnings
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'llm-core'))
from run import request,payload,estimate_cost,append
from core import digest
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 if not sys.stdin.isatty():raise SystemExit('Non-echo console required')
 warnings.simplefilter('error',getpass.GetPassWarning)
 frozen=json.loads((R/'frozen-core-v2.json').read_text())
 for n,h in frozen['research'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 plan=json.loads((R/'plan.json').read_text());tests=json.loads((R/'challenge-plans.json').read_text())
 natural=json.loads((R/'results/core/collection-summary.json').read_text())
 assert natural['stop'] is None and natural['completedBlocks']==128
 out=R/'results/challenge';out.mkdir(parents=True,exist_ok=True)
 if (out/'calls.jsonl').exists():raise SystemExit('Challenge already attempted; no implicit replay')
 keys=json.loads(getpass.getpass('CREDENTIAL_INPUT: '));jobs=[(rep,c,m) for rep in range(3) for c in tests for m in ('a','b')];random.Random(2026100803).shuffle(jobs)
 spent=0.;unknown=0;count=0;stop=None
 try:
  for rep,c,m in jobs:
   if spent+unknown*.01+.05>1:stop='BUDGET_BOUNDARY';break
   provider=plan['providers'][m];prompt=(R/'prompts/review.txt').read_text()+'\n被审系统协议与公开目录：\n'+(R/f"prompts/{c['system']}.txt").read_text(encoding='utf-8')
   body=payload(provider,prompt,json.dumps({'question':c['question'],'candidate':json.dumps(c['candidate'],ensure_ascii=False)},ensure_ascii=False),plan['reviewMaxTokens'])
   cid=f"{c['id']}-r{rep}/review/{m}";append(out/'request-journal.jsonl',{'callId':cid,'requestHash':digest(body),'state':'STARTED','startedAt':datetime.now(timezone.utc).isoformat()})
   result=request(provider['url'],keys[provider['name']],body,plan['deadlineMs']);cost=estimate_cost(result,provider)
   if cost is None:unknown+=1
   else:spent+=cost
   choices=result.get('response',{}).get('choices',[])
   record=dict(callId=cid,caseId=c['caseId'],challengeId=c['id'],repeat=rep,system=c['system'],provider=provider['name'],request=body,requestHash=digest(body),estimatedCostCny=cost,rawContent=choices[0].get('message',{}).get('content','') if choices else '',complete=bool(choices) and choices[0].get('finish_reason')=='stop' and result['transport']=='SUCCESS',observedAt=datetime.now(timezone.utc).isoformat(),**result)
   append(out/'calls.jsonl',record);count+=1
   if count%16==0:print(json.dumps({'challengeCalls':count,'planned':96,'estimatedCostCny':round(spent,6)}),flush=True)
   if unknown>=3:stop='USAGE_UNAVAILABLE';break
 finally:
  keys.clear();summary=dict(calls=count,planned=96,estimatedCostCny=spent,unknownCostCalls=unknown,stop=stop,actualBilling='NOT_VERIFIED')
  (out/'summary.json').write_bytes(json.dumps(summary,indent=2).encode());print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
