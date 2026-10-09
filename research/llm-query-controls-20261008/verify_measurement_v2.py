"""Check versioned measurement provenance and recompute counts from retained evidence."""
from collections import Counter
from common import R, read, lines, check, hash_file, parse_plan, primary_match

def main():
    check();version=read(R/'measurement-v2.json')
    assert hash_file(R/'seal.json')==version['parentSealSha256']
    for name,expected in version['files'].items():assert hash_file(R/name)==expected
    calls=lines(R/'results/calls.jsonl');native={n['recordId']:n for s in ['library','qingye'] for n in lines(R/f'results/native/native-{s}.jsonl')}
    cases={c['id']:c for c in read(R/'cases.json')};details=read(R/'output-v2/details.json');metrics=read(R/'output-v2/metrics.json')
    assert len(details)==len(calls)==metrics['requestIdentities'] and len(native)==metrics['nativeObservedRecords']
    dmap={d['callId']:d for d in details}
    for call in calls:
        d=dmap[call['callId']];case=cases[call['caseId']]
        p,error=parse_plan(case['system'],call['rawContent']) if call['complete'] else (None,'INCOMPLETE')
        assert p==d['plan'] and error==d['structureStatus'] and d['primaryPlanMatch']==primary_match(p,case['rule'],case['system'])
        for fixture in d['fixtures']:
            n=native[fixture['recordId']]
            assert fixture['nativeQualified']==n['nativeQualified'] and fixture['status']==n['response']['status'] and fixture['actualReadQueries']==len(n['queryTrace'])
    for provider,m in metrics['resources'].items():
        group=[c for c in calls if c['provider']==provider];known=[c for c in group if 'prompt_tokens' in c.get('response',{}).get('usage',{}) and 'completion_tokens' in c.get('response',{}).get('usage',{})]
        assert m['clientRequestIdentities']==len(group) and m['transport']==dict(Counter(c['transport'] for c in group))
        assert m['usageKnown']==len(known) and m['usageMissing']==len(group)-len(known)
        assert m['knownInputTokens']==sum(c['response']['usage']['prompt_tokens'] for c in known)
        assert m['knownOutputTokens']==sum(c['response']['usage']['completion_tokens'] for c in known)
    print('Measurement v2 PASS; original failure/scorer retained, raw/native correspondence and request/usage counts verified')
if __name__=='__main__':main()
