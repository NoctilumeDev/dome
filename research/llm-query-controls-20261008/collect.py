"""One frozen new window, no retries or output overwrites; non-echo keys only."""
import getpass, random, sys, warnings
from datetime import datetime, timezone
from common import R, read, write, lines, hash_file, check, digest, net

def main():
    sys.stdout.reconfigure(encoding='utf-8');check();plan=read(R/'plan.json');cases=read(R/'cases.json')
    labels=read(R/'preflight-labels.json');eligible={x['caseId'] for x in labels if x['plannerReachable']}
    out=R/'results'
    if out.exists():raise SystemExit('Collection coordinate already exists; no implicit retry')
    if not sys.stdin.isatty():raise SystemExit('Non-echo credential console required')
    warnings.simplefilter('error',getpass.GetPassWarning);keys=__import__('json').loads(getpass.getpass('CREDENTIAL_INPUT: '));assert set(keys)=={'deepseek','qwen'}
    out.mkdir();started=datetime.now(timezone.utc).isoformat();spent={'deepseek':0.,'qwen':0.};unknown=0;bad=0;stop=None;count=0
    schedule=[(r,c) for r in range(plan['repetitions']) for c in cases if c['id'] in eligible]
    rng=random.Random(plan['seed']);rng.shuffle(schedule)
    try:
        for repeat,c in schedule:
            models=['a','b'];rng.shuffle(models)
            for slot in models:
                check();provider=plan['providers'][slot];name=provider['name']
                # Reserve before every request; includes separately reserved day1 budget.
                if sum(spent.values())+.10>plan['newBudgetCny'] or spent[name]+plan['priorConservativeCny'][name]+plan['reservedLayer3Day1CnyPerProvider']+.10>plan['hardCumulativePerProviderCny']:raise RuntimeError('BUDGET_BOUNDARY')
                if unknown>=3:raise RuntimeError('USAGE_UNAVAILABLE')
                if bad>=max(5,count//5):raise RuntimeError('TRANSPORT_BOUNDARY')
                body=net.payload(provider,(R/f'prompts/{c["system"]}.txt').read_text(encoding='utf-8'),c['question'],plan['maxTokens'][c['system']])
                cid=f'QC4/{c["id"]}/r{repeat}/{slot}'
                net.append(out/'request-journal.jsonl',dict(callId=cid,state='STARTED',requestHash=digest(body),startedAt=datetime.now(timezone.utc).isoformat()))
                obs=net.request(provider['url'],keys[name],body,plan['deadlineMs'])
                record=dict(callId=cid,caseId=c['id'],repeat=repeat,system=c['system'],provider=name,requestedModel=provider['model'],requestHash=digest(body),request=body,collectorSha256=hash_file(R/'collect.py'),observedAt=datetime.now(timezone.utc).isoformat(),**obs)
                record['estimatedCostCny']=net.estimate_cost(record,provider)
                choices=record.get('response',{}).get('choices',[]);record['rawContent']=choices[0].get('message',{}).get('content','') if choices else ''
                record['complete']=record['transport']=='SUCCESS' and bool(choices) and choices[0].get('finish_reason')=='stop'
                net.append(out/'calls.jsonl',record);count+=1
                if record['estimatedCostCny'] is None:unknown+=1;spent[name]+=plan['unknownReserveCny']
                else:spent[name]+=record['estimatedCostCny']
                if record['transport']!='SUCCESS':bad+=1
                if record.get('httpStatus') in [401,403]:raise RuntimeError('AUTHENTICATION_BLOCK')
            print(__import__('json').dumps(dict(completedPairedBlocks=count//2,plannedPairedBlocks=len(schedule),calls=count,conservativeNew=spent)),flush=True)
    except (RuntimeError,AssertionError) as e:stop=str(e)
    except KeyboardInterrupt:stop='INTERRUPTED';raise
    finally:
        keys.clear();write(out/'summary.json',dict(startedAt=started,finishedAt=datetime.now(timezone.utc).isoformat(),requestIdentities=count,plannedRequestIdentities=len(schedule)*2,excludedBeforeModel=len(cases)-len(eligible),stop=stop,conservativeNewCny=spent,actualCash='NOT_VERIFIED'))
    print('COLLECTION_EXIT stop='+str(stop),flush=True)
if __name__=='__main__':main()
