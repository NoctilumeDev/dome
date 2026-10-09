"""Archive verifier, no API call and no evidence rewriting."""
from common import R, read, lines, check, digest, net, hash_file

def main():
    seal=check();cases={c['id']:c for c in read(R/'cases.json')};plan=read(R/'plan.json');labels=read(R/'preflight-labels.json')
    calls=lines(R/'results/calls.jsonl');journal=lines(R/'results/request-journal.jsonl')
    if not calls:
        print('Input seal PASS; results NOT_RUN');return
    identities={c['callId'] for c in calls};assert len(identities)==len(calls)
    assert len(journal)==len({j['callId'] for j in journal})
    unknown={j['callId'] for j in journal}-identities
    summary=read(R/'results/summary.json')
    if summary['stop'] is None:assert not unknown and len(calls)==sum(l['plannerReachable'] for l in labels)*plan['repetitions']*2
    for call in calls:
        c=cases[call['caseId']];provider=next(p for p in plan['providers'].values() if p['name']==call['provider'])
        body=net.payload(provider,(R/f'prompts/{c["system"]}.txt').read_text(encoding='utf-8'),c['question'],plan['maxTokens'][c['system']])
        assert call['request']==body and call['requestHash']==digest(body)
        assert call['collectorSha256']==seal['research']['collect.py'] and call['estimatedCostCny']==net.estimate_cost(call,provider)
        assert 'authorization' not in __import__('json').dumps(call).lower()
    for provider in ['deepseek','qwen']:
        cost=sum(c.get('estimatedCostCny') or plan['unknownReserveCny'] for c in calls if c['provider']==provider)
        assert cost+plan['priorConservativeCny'][provider]+plan['reservedLayer3Day1CnyPerProvider']<=20
    assert sum(c.get('estimatedCostCny') or plan['unknownReserveCny'] for c in calls)<=plan['newBudgetCny']
    if (R/'results/native/input.json').exists():
        inputs=read(R/'results/native/input.json');by_call={c['callId']:c for c in calls}
        observed={n['recordId']:n for s in ['library','qingye'] for n in lines(R/f'results/native/native-{s}.jsonl')}
        assert len(inputs)==len(observed)
        for n in inputs:
            call=by_call[n['callId']];assert n['rawContent']==call['rawContent'] and n['complete']==call['complete'] and n['question']==cases[call['caseId']]['question']
            record=observed[n['recordId']];assert record['snapshotUnchanged'] and record['actor']==n['actor'] and record['fixture']==n['fixture']
            if record['response']['status']=='CONFIRM_SCOPE':assert record['crossActorRejected'] and record['crossSessionRejected'] and record['singleUse']
    print('Archive PASS:',len(calls),'requests;',len(unknown),'interrupted/unknown journal-only identities; frozen inputs/source/request/native/budget checked')
if __name__=='__main__':main()
