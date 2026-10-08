import argparse
import csv
import json
import random
from collections import defaultdict,Counter
from pathlib import Path
from core import canonical,decisions,parse_plan,review,score_plan
ROOT=Path(__file__).resolve().parent

def read_lines(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
def percentile(values,p):
    if not values:return None
    ordered=sorted(values);return ordered[min(len(ordered)-1,int((len(ordered)-1)*p))]

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['pilot','core']);args=p.parse_args();folder=ROOT/f'results/{args.phase}'
    calls={r['callId']:r for r in read_lines(folder/'calls.jsonl')}
    native={}
    for system in ('qingye','library'):
        for r in read_lines(folder/f'native-{system}.jsonl'):
            if r['callId'] in native:raise ValueError('Duplicate native identity')
            native[r['callId']]=r
    for system in ('qingye','library'):
        positive=native[f'CONTROL/{system}/positive'];assert positive['response']['status']=='QUERY'
        for variant in ('foreign-user','missing-field','transport'):
            n=native[f'CONTROL/{system}/{variant}'];assert n['response']['status']!='QUERY'
        n=native[f'CONTROL/{system}/omitted-private-filter'];assert n['response']['status']=='CONFIRM_SCOPE'
        if system=='qingye':assert not any('FROM loan ' in s for s in n['askSql'])
        else:assert n['repositoryQueriesBeforeConfirm']==0
    assert all(n['databaseUnchanged'] for n in native.values())
    cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))}
    blocks={r['block']:r for r in read_lines(folder/'blocks.jsonl')}
    rows=[];review_rows=[]
    for block,metadata in blocks.items():
        case=cases[metadata['caseId']];pools={};native_for={};parsed_first={};reviews={}
        for model in ('a','b'):
            pool=[]
            for index in range(4):
                cid=f'{block}/p/{model}/{index}';r=calls[cid];n=native[cid]
                parsed,format_status=parse_plan(case['system'],r['rawContent'])
                qualified=parsed is not None and r['complete'] and n['nativeQualified']
                pool.append(parsed if qualified else None)
                if qualified:native_for.setdefault(canonical(parsed),n)
                if index==0:parsed_first[model]=parsed
            pools[model]=pool
        for reviewer in ('a','b'):
            for proposer in ('a','b'):
                r=calls[f'{block}/r/{reviewer}/{proposer}'];verdict=review(r['rawContent']) if r['complete'] else 'UNAVAILABLE';reviews[f'{reviewer}:{proposer}']=verdict
                proposal=parsed_first[proposer];correct=score_plan(proposal,case['oracle'])['proposal_correct']
                review_rows.append(dict(block=block,system=case['system'],family=case['family'],reviewer=reviewer,proposer=proposer,verdict=verdict,proposalCorrect=correct,nativeQualified=pools[proposer][0] is not None,falseKill=correct and verdict in ('CLARIFY','REJECT'),reviewUnavailableCorrect=correct and verdict in ('INVALID_REVIEW','UNAVAILABLE'),missedError=not correct and verdict=='ACCEPT'))
        selected=decisions(pools['a'][0],pools['b'][0],reviews,pools)
        for group,plan in selected.items():
            scored=score_plan(plan,case['oracle']);n=native_for.get(canonical(plan))
            # A is the actual original product outcome, even when parsing/qualification failed.
            if group.startswith('A:'):n=native[f"{block}/p/{group[-1]}/0"]
            status=n['response']['status'] if n else 'NOT_EXECUTED_BY_POLICY'
            semantic=scored['proposal_correct'];expected_query=any(a.get('action')=='QUERY' for a in case['oracle']['allowed'])
            expected_decline=any(a.get('action')=='CLARIFY' for a in case['oracle']['allowed'])
            pending=status=='CONFIRM_SCOPE';actual_public=status=='QUERY'
            rows.append(dict(block=block,caseId=case['id'],system=case['system'],family=case['family'],repeat=metadata['repeat'],group=group,selectedPlan=plan,semanticPlanCorrect=semantic,handlingCorrect=semantic or (expected_decline and status in ('CLARIFY','NOT_EXECUTED_BY_POLICY')),expectedQuery=expected_query,actualStatus=status,pendingScope=pending,publicCompletedCorrect=semantic and actual_public,wrongAutomaticExecution=actual_public and not semantic,simulatedPersonalCompletedCorrect=semantic and pending and n.get('simulatedConfirmation',{}).get('status')=='QUERY',humanCorrectionObserved=False))
    (folder/'decisions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'review-decisions.json').write_text(json.dumps(review_rows,ensure_ascii=False,indent=2),encoding='utf-8')
    summaries=[]
    for system in ('qingye','library','both'):
        for group in sorted({r['group'] for r in rows}):
            part=[r for r in rows if r['group']==group and (system=='both' or r['system']==system)]
            summaries.append(dict(system=system,group=group,n=len(part),semanticPlanCorrect=sum(r['semanticPlanCorrect'] for r in part),handlingCorrect=sum(r['handlingCorrect'] for r in part),publicCompletedCorrect=sum(r['publicCompletedCorrect'] for r in part),pendingScope=sum(r['pendingScope'] for r in part),wrongAutomaticExecution=sum(r['wrongAutomaticExecution'] for r in part),simulatedPersonalCompletedCorrect=sum(r['simulatedPersonalCompletedCorrect'] for r in part)))
    with (folder/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows(summaries)
    # Family is resampled as a whole, including both domains and all repetitions.
    paired={};families=sorted({r['family'] for r in rows});rng=random.Random(20261008)
    by={(r['block'],r['group']):r for r in rows}
    for target,base in [('B','A:a'),('B','A:b'),('C:a','B'),('C:b','B'),('D','B'),('E:a','A:a'),('E:b','A:b'),('F2:a','E:a'),('F2:b','E:b'),('F3:a','C:a'),('F3:b','C:b'),('F4:a','D'),('F4:b','D')]:
        per=defaultdict(list)
        for metadata in blocks.values():
            block=metadata['block'];left=by[(block,target)];right=by[(block,base)]
            per[left['family']].append(int(left['handlingCorrect'])-int(right['handlingCorrect']))
        means={f:sum(v)/len(v) for f,v in per.items()};fs=sorted(means);boot=[sum(means[rng.choice(fs)] for _ in fs)/len(fs) for _ in range(4000)]
        paired[target+' minus '+base]=dict(families=len(fs),difference=sum(means.values())/len(fs),familyBootstrap95=[percentile(boot,.025),percentile(boot,.975)],interpretation='known mechanism families, executor labels, exploratory paired interval; no independent user population claim')
    collection=json.loads((folder/'collection-summary.json').read_text(encoding='utf-8'))
    latency={}
    for provider in ('deepseek','qwen'):
        all_values=[r['elapsedMs'] for r in calls.values() if r['provider']==provider]
        latency[provider]=dict(n=len(all_values),medianMs=percentile(all_values,.5),p95Ms=percentile(all_values,.95),scope='individual HTTP calls including failures; not reused-plan end-to-end')
    report=dict(phase=args.phase,pairedBlocks=len(blocks),groups=summaries,review=review_rows,pairedExploratoryIntervals=paired,collection=collection,latency=latency,nativeControlsPassed=True,allSnapshotsUnchanged=True,limitations=['Known families, no independent human oracle','No human correction observed','No online multi-model deployment measured','No production MySQL or WeChat device'])
    (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pairedBlocks':len(blocks),'controls':'PASS','groups':len(summaries),'wrongAutomaticExecutions':sum(r['wrongAutomaticExecution'] for r in rows)},ensure_ascii=False))
if __name__=='__main__':main()
