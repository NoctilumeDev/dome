"""Serial, resumable provider collection. Reads keys from stdin, never from a file."""
import argparse
import getpass
import hashlib
import http.client
import json
import os
import random
import ssl
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import clean_response, digest, parse_plan, review

ROOT=Path(__file__).resolve().parent

def append(path,value):
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())

def request(url,key,payload,deadline_ms):
    parsed=urlparse(url);connection=http.client.HTTPSConnection(parsed.hostname,parsed.port or 443,timeout=deadline_ms/1000,context=ssl.create_default_context())
    started=time.monotonic();result={}
    try:
        connection.request('POST',parsed.path or '/',body=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        remaining=deadline_ms/1000-(time.monotonic()-started)
        if remaining<=0:raise TimeoutError()
        connection.sock.settimeout(remaining)
        response=connection.getresponse(); chunks=[]; total=0
        while True:
            remaining=deadline_ms/1000-(time.monotonic()-started)
            if remaining<=0:raise TimeoutError()
            # read1 returns available bytes and does not keep extending a trickle deadline.
            if connection.sock is not None:connection.sock.settimeout(remaining)
            chunk=response.read1(8192)
            if not chunk:break
            total+=len(chunk)
            if total>262144:raise ValueError('RESPONSE_TOO_LARGE')
            chunks.append(chunk)
        result={'httpStatus':response.status,'providerRequestId':response.getheader('x-request-id') or response.getheader('request-id')}
        body=json.loads(b''.join(chunks).decode('utf-8'))
        if 200<=response.status<300:
            result['response']=clean_response(body);result['transport']='SUCCESS'
        else:
            # Keep machine error code, not credential-bearing free-form messages.
            result['transport']='HTTP_ERROR';result['errorCode']=str(body.get('error',{}).get('code','UNKNOWN'))
    except TimeoutError:result={'transport':'TIMEOUT'}
    except Exception as e:result={'transport':'ENVIRONMENT_ERROR','errorClass':type(e).__name__}
    finally:connection.close()
    result['elapsedMs']=round((time.monotonic()-started)*1000,3)
    if result['elapsedMs']>deadline_ms and result.get('transport')=='SUCCESS':result['transport']='DEADLINE_EXCEEDED'
    return result

def payload(provider,system_prompt,user,max_tokens):
    p=dict(model=provider['model'],temperature=0,max_tokens=max_tokens,messages=[{'role':'system','content':system_prompt},{'role':'user','content':user}])
    if provider['name']=='deepseek':p['thinking']={'type':'disabled'}
    else:p['enable_thinking']=False
    return p

def estimate_cost(record,provider):
    usage=record.get('response',{}).get('usage',{})
    if 'prompt_tokens' not in usage or 'completion_tokens' not in usage:return None
    # Conservative: charge all input at cache-miss and peak price.
    return (usage['prompt_tokens']*provider['inputCnyPerMillion']+usage['completion_tokens']*provider['outputCnyPerMillion'])/1e6

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['pilot','core']);parser.add_argument('--keys-stdin',action='store_true',required=True);parser.add_argument('--budget-cny',type=float,required=True);parser.add_argument('--manifest',default='frozen-core-v2.json',choices=['frozen-core.json','frozen-core-v2.json']);args=parser.parse_args()
    if args.budget_cny<=0:raise SystemExit('Positive budget required')
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    for file,expected in plan['inputHashes'].items():
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=expected:raise SystemExit('Frozen input changed: '+file)
    if args.phase=='core':
        frozen=json.loads((ROOT/args.manifest).read_text(encoding='utf-8'))
        for name,expected in frozen['research'].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise SystemExit('Frozen research changed: '+name)
        for name,expected in frozen['production'].items():
            if hashlib.sha256((ROOT.parents[2]/name).read_bytes()).hexdigest()!=expected:raise SystemExit('Frozen product changed: '+name)
    # Windows PTY uses console input without echo. Never fall back to echoed input.
    if not sys.stdin.isatty():raise SystemExit('Credential input requires an interactive non-echo console')
    warnings.simplefilter('error',getpass.GetPassWarning)
    keys=json.loads(getpass.getpass('CREDENTIAL_INPUT: '));assert set(keys)=={'deepseek','qwen'}
    cases=json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))
    if args.phase=='pilot':cases=[c for c in cases if c['family'] in plan['pilotFamilies'] and c['variant']==plan['pilotVariant']]
    blocks=[(r,c) for r in range(1 if args.phase=='pilot' else plan['repetitions']) for c in cases]
    rng=random.Random(plan['seed']+(0 if args.phase=='pilot' else 1));rng.shuffle(blocks)
    out=ROOT/'results'/args.phase;out.mkdir(parents=True,exist_ok=True)
    raw_path=out/'calls.jsonl';existing={}
    if raw_path.exists():
        for line in raw_path.read_text(encoding='utf-8').splitlines():
            r=json.loads(line)
            if r['callId'] in existing:raise SystemExit('Duplicate retained call identity')
            existing[r['callId']]=r
    request_journal=out/'request-journal.jsonl'
    if request_journal.exists():
        pending=[json.loads(line)['callId'] for line in request_journal.read_text(encoding='utf-8').splitlines() if json.loads(line)['callId'] not in existing]
        if pending:raise SystemExit('UNKNOWN provider attempts retained; no automatic resubmission: '+','.join(pending))
    spent=sum(r.get('estimatedCostCny') or 0 for r in existing.values());unknown_cost=sum(r.get('estimatedCostCny') is None for r in existing.values())
    unknown_reserve=0.01*unknown_cost
    started=datetime.now(timezone.utc).isoformat(); completed=[]
    collector_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def invoke(call_id,role,model,case,body):
        nonlocal spent,unknown_cost,unknown_reserve
        request_hash=digest(body)
        if call_id in existing:
            r=existing[call_id]
            if r['requestHash']!=request_hash:raise RuntimeError('Resume request differs')
            return r
        provider=plan['providers'][model]
        if args.phase=='core' and hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=collector_hash:
            raise RuntimeError('Collector changed during frozen batch')
        append(request_journal,{'callId':call_id,'requestHash':request_hash,'state':'STARTED','startedAt':datetime.now(timezone.utc).isoformat()})
        observed=request(provider['url'],keys[provider['name']],body,plan['deadlineMs'])
        r=dict(callId=call_id,role=role,caseId=case['id'],system=case['system'],provider=provider['name'],requestedModel=provider['model'],collectorSha256=collector_hash,requestHash=request_hash,request=body,observedAt=datetime.now(timezone.utc).isoformat(),**observed)
        r['estimatedCostCny']=estimate_cost(r,provider)
        if r['estimatedCostCny'] is None:unknown_cost+=1;unknown_reserve+=0.01
        else:spent+=r['estimatedCostCny']
        response=r.get('response',{});choices=response.get('choices',[])
        r['rawContent']=choices[0].get('message',{}).get('content','') if choices else ''
        r['complete']=bool(choices) and choices[0].get('finish_reason')=='stop' and r['transport']=='SUCCESS'
        append(raw_path,r);existing[call_id]=r
        return r
    stop=None
    completed_prior=set()
    if (out/'blocks.jsonl').exists():
        completed_prior={json.loads(line)['block'] for line in (out/'blocks.jsonl').read_text(encoding='utf-8').splitlines()}
    try:
        for repeat,case in blocks:
            block=f"{case['id']}-r{repeat}"
            # Advance the exact same schedule even for cached completed blocks.
            models=['a','b'];rng.shuffle(models)
            review_jobs=[('a','a'),('b','b'),('a','b'),('b','a')];rng.shuffle(review_jobs)
            if block in completed_prior:completed.append(block);continue
            # Complete paired blocks; a small reserved bound prevents overshoot.
            if spent+unknown_reserve+0.15>args.budget_cny:stop='BUDGET_PAIR_BOUNDARY';break
            system=case['system'];prompt=(ROOT.parent/f'prompts/{system}.txt').read_text(encoding='utf-8')
            pools={}
            for model in models:
                pools[model]=[]
                for index in range(4):
                    pools[model].append(invoke(f'{block}/p/{model}/{index}','proposal',model,case,payload(plan['providers'][model],prompt,case['question'],plan['maxTokens'][system])))
            review_instruction=(ROOT.parent/'prompts/review.txt').read_text(encoding='utf-8')+'\n被审系统协议与公开目录：\n'+prompt
            for reviewer,proposer in review_jobs:
                first=pools[proposer][0]
                review_input=json.dumps({'question':case['question'],'candidate':first['rawContent']},ensure_ascii=False)
                invoke(f'{block}/r/{reviewer}/{proposer}','review',reviewer,case,payload(plan['providers'][reviewer],review_instruction,review_input,plan['reviewMaxTokens']))
            append(out/'blocks.jsonl',{'block':block,'caseId':case['id'],'repeat':repeat,'completed':True})
            completed.append(block)
            print(json.dumps({'phase':args.phase,'completedBlocks':len(completed),'plannedBlocks':len(blocks),'callsRetained':len(existing),'estimatedCostCny':round(spent,6),'unknownCostCalls':unknown_cost},ensure_ascii=False),flush=True)
            if unknown_cost>=3:stop='USAGE_UNAVAILABLE';break
            if sum(r['transport']!='SUCCESS' for r in existing.values())>=max(8,len(existing)//3):stop='TRANSPORT_ERROR_BUDGET';break
    except KeyboardInterrupt:
        stop='INTERRUPTED';raise
    finally:
        keys.clear()
        summary=dict(phase=args.phase,manifest=args.manifest,startedAt=started,finishedAt=datetime.now(timezone.utc).isoformat(),completedBlocks=len(completed),plannedBlocks=len(blocks),callCount=len(existing),estimatedCostCny=spent,unknownCostReserveCny=unknown_reserve,unknownCostCalls=unknown_cost,actualBilling='NOT_VERIFIED',stop=stop,raw=raw_path.name,budgetCny=args.budget_cny)
        tmp=out/'collection-summary.tmp';tmp.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(out/'collection-summary.json')
    print('COLLECTION_EXIT='+json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
