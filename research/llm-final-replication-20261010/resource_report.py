"""Derived resource receipts. Does not classify plans or modify frozen inputs."""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
from datetime import datetime, timezone

R = pathlib.Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    return values[int((len(values)-1)*fraction)]

def describe(records):
    known = [x for x in records if isinstance(x.get('response', {}).get('usage'), dict)]
    prompts = [x['response']['usage']['prompt_tokens'] for x in known if type(x['response']['usage'].get('prompt_tokens')) is int]
    outputs = [x['response']['usage']['completion_tokens'] for x in known if type(x['response']['usage'].get('completion_tokens')) is int]
    total = [x['response']['usage']['total_tokens'] for x in known if type(x['response']['usage'].get('total_tokens')) is int]
    times = [x['elapsedMs'] for x in records if isinstance(x.get('elapsedMs'), (int, float))]
    return dict(requestIdentities=len(records), transport=dict(collections.Counter(x['transport'] for x in records)),
        usageRecords=len(known), usageMissing=len(records)-len(known),
        inputTokenRecords=len(prompts), outputTokenRecords=len(outputs), totalTokenRecords=len(total),
        observedInputTokens=sum(prompts), observedOutputTokens=sum(outputs), observedTotalTokens=sum(total),
        tokenCoverageComplete=len(prompts)==len(outputs)==len(total)==len(records),
        apiLatencyRecords=len(times), apiLatencyP50Ms=percentile(times,.5), apiLatencyP95Ms=percentile(times,.95),
        requestedModels=sorted({x['requestedModel'] for x in records}),
        responseModels=sorted({x['response']['model'] for x in records if x.get('response',{}).get('model')}),
        estimatedBudgetCny=sum(x['estimatedCostCny'] for x in records if x.get('estimatedCostCny') is not None),
        priceEstimateMissing=sum(x.get('estimatedCostCny') is None for x in records))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('window',choices=['first-window','full-matrix']);args=parser.parse_args()
    matrix=read(R/'matrix.json')
    suites=[x for x in matrix['suites'] if args.window=='full-matrix' or not x['guardAfterFinishedSuite']]
    receipt=[];all_records=[];by_group=collections.defaultdict(list);ids=set()
    for suite in suites:
        root=R/'results'/suite['id'];summary=read(root/'summary.json')
        assert summary['stop'] is None and summary['requests']==suite['requests'],'Incomplete suite '+suite['id']
        records=rows(root/'calls.jsonl');journal=rows(root/'request-journal.jsonl')
        assert len(records)==len(journal)==suite['requests']
        assert [x['callId'] for x in records]==[x['callId'] for x in journal]
        assert [x['requestHash'] for x in records]==[x['requestHash'] for x in journal]
        for x in records:
            assert x['callId'] not in ids;ids.add(x['callId'])
            assert x['suite']==suite['id'];all_records.append(x)
            by_group[(suite['id'],x['provider'],x['requestedModel'],x['role'])].append(x)
        receipt.append(dict(suite=suite['id'],summary=summary,resources=describe(records),
            callsSha256=hashlib.sha256((root/'calls.jsonl').read_bytes()).hexdigest(),
            journalSha256=hashlib.sha256((root/'request-journal.jsonl').read_bytes()).hexdigest()))
    result=dict(version='resource-receipt-v1',window=args.window,generatedAt=datetime.now(timezone.utc).isoformat(),
        total=describe(all_records),providers={p:describe([x for x in all_records if x['provider']==p]) for p in ['deepseek','qwen']},
        suites=receipt,historicalConservativeCny=matrix['historicalConservativeCny'],
        qualification=['Fresh physical request identities, not independent users or statistically independent errors',
            'Observed usage totals exclude missing usage; unknown billed workload is not zero',
            'Tokens describe API workload and are not FLOPs or cross-model compute equivalence',
            'Latency is individual observed HTTP call latency including failures, not UI end-to-end latency',
            'Budget estimate uses frozen price assumptions; cash charge and promotional offsets are NOT_VERIFIED',
            'No semantic, safety, or patent qualification is established by this resource receipt'])
    dest=R/'resources'/args.window;assert not dest.exists(),'Keep original receipt';dest.mkdir(parents=True)
    (dest/'physical-resources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    data=[]
    for key,records in by_group.items():
        d=describe(records);data.append(dict(suite=key[0],provider=key[1],model=key[2],role=key[3],
            requests=d['requestIdentities'],usageRecords=d['usageRecords'],usageMissing=d['usageMissing'],
            observedInputTokens=d['observedInputTokens'],observedOutputTokens=d['observedOutputTokens'],
            observedTotalTokens=d['observedTotalTokens'],apiLatencyP50Ms=d['apiLatencyP50Ms'],apiLatencyP95Ms=d['apiLatencyP95Ms']))
    with (dest/'by-suite-provider-model-role.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    print(json.dumps(dict(window=args.window,requests=len(all_records),usageMissing=result['total']['usageMissing'],path=str(dest)),ensure_ascii=False))

if __name__=='__main__':main()
