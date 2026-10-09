"""Review every retained paired proposal; never resample or repair a candidate."""
import getpass, random, sys, warnings
from datetime import datetime, timezone
from common import R, read, write, lines, hash_file, check, digest, net, budget_boundary, stage_time, review_input_check

def review_check():
    review_input_check();stage_time('review')

def main():
    sys.stdout.reconfigure(encoding='utf-8');review_check();plan=read(R/'review-plan.json');source=lines(R/'results/calls.jsonl');cases={c['id']:c for c in read(R/'cases.json')}
    by_id={c['callId']:c for c in source};out=R/'review-results'
    if out.exists():raise SystemExit('Review output coordinate exists; preserve attempts')
    if not sys.stdin.isatty():raise SystemExit('Non-echo credential console required')
    warnings.simplefilter('error',getpass.GetPassWarning);keys=__import__('json').loads(getpass.getpass('CREDENTIAL_INPUT: '));assert set(keys)=={'deepseek','qwen'}
    out.mkdir();started=datetime.now(timezone.utc).isoformat();spent={'deepseek':0.,'qwen':0.};unknown=0;bad=0;stop=None;count=0
    schedule=list(plan['jobs']);random.Random(plan['seed']).shuffle(schedule)
    try:
        for job in schedule:
            review_check();slot=job['reviewer'];provider=plan['providers'][slot];name=provider['name'];candidate=by_id[job['candidateCallId']];case=cases[candidate['caseId']]
            if budget_boundary(name,'review'):raise RuntimeError('BUDGET_BOUNDARY')
            if unknown>=3:raise RuntimeError('USAGE_UNAVAILABLE')
            if bad>=max(5,count//5):raise RuntimeError('TRANSPORT_BOUNDARY')
            prompt=(R/'prompts/review.txt').read_text(encoding='utf-8')+'\n被审系统协议：\n'+(R/f'prompts/{case["system"]}.txt').read_text(encoding='utf-8')
            text=__import__('json').dumps({'question':case['question'],'candidate':candidate['rawContent']},ensure_ascii=False)
            body=net.payload(provider,prompt,text,250);cid='QC4-DAY1-REVIEW/'+job['candidateCallId']+'/'+slot
            net.append(out/'request-journal.jsonl',dict(callId=cid,state='STARTED',requestHash=digest(body),startedAt=datetime.now(timezone.utc).isoformat()))
            obs=net.request(provider['url'],keys[name],body,5000)
            record=dict(callId=cid,candidateCallId=candidate['callId'],caseId=case['id'],repeat=candidate['repeat'],system=case['system'],provider=name,reviewer=slot,requestedModel=provider['model'],requestHash=digest(body),request=body,collectorSha256=hash_file(R/'review_collect.py'),observedAt=datetime.now(timezone.utc).isoformat(),**obs)
            record['estimatedCostCny']=net.estimate_cost(record,provider);choices=record.get('response',{}).get('choices',[])
            record['rawContent']=choices[0].get('message',{}).get('content','') if choices else '';record['complete']=record['transport']=='SUCCESS' and bool(choices) and choices[0].get('finish_reason')=='stop'
            net.append(out/'calls.jsonl',record);count+=1
            if record['estimatedCostCny'] is None:unknown+=1;spent[name]+=.05
            else:spent[name]+=record['estimatedCostCny']
            if record['transport']!='SUCCESS':bad+=1
            if record.get('httpStatus') in [401,403]:raise RuntimeError('AUTHENTICATION_BLOCK')
            if count%20==0:print(__import__('json').dumps(dict(reviews=count,planned=len(schedule),newReviewEstimateCny=spent)),flush=True)
    except (RuntimeError,AssertionError) as e:stop=str(e)
    except KeyboardInterrupt:stop='INTERRUPTED';raise
    finally:
        keys.clear();write(out/'summary.json',dict(startedAt=started,finishedAt=datetime.now(timezone.utc).isoformat(),requestIdentities=count,plannedRequestIdentities=len(schedule),stop=stop,reviewConservativeCny=spent,actualCash='NOT_VERIFIED'))
    print('REVIEW_EXIT stop='+str(stop),flush=True)
if __name__=='__main__':main()
