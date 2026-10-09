"""Seal inputs after deterministic preflight, before any paid observation."""
import subprocess
from common import R, REPO, read, write, lines, hash_file

def main():
    assert not (R/'seal.json').exists() and not (R/'results').exists()
    cases=read(R/'cases.json');records=[r for s in ['library','qingye'] for r in lines(R/f'diagnostics/preflight/native-{s}.jsonl')]
    labels=[]
    for c in cases:
        group=[r for r in records if r['callId']=='PREFLIGHT/'+c['id']]
        assert len(group)==len(c['scenarios']) and all(r['snapshotUnchanged'] for r in group)
        assert len({r['nativePlannerCalled'] for r in group})==1,'Entry depends on fixture unexpectedly'
        reachable=group[0]['nativePlannerCalled']
        if reachable:assert all(r['nativeQualified'] for r in group),'Preflight candidate not admissible: '+c['id']
        labels.append(dict(caseId=c['id'],plannerReachable=reachable,entryStatus=group[0]['response']['status'],oracleRule=c['rule'],scenarios=len(group),labelOwner='same executor, source-grounded; not independent blind annotation'))
    for r in records:
        if r['callId'].startswith('CONTROL/'):
            assert r['response']['status']=='REJECT' and not r['queryTrace'],'Injected identity field must not execute'
    write(R/'preflight-labels.json',labels)
    parent=read(R.parent/'llm-controls-layer3-20261008/seal.json')
    product=dict(parent['product'])
    for name,expected in product.items():assert hash_file(REPO/name)==expected,'Product differs from layer3 seal'
    imports={'research/llm-core/'+n:hash_file(R.parent/'llm-core'/n) for n in ['run.py','core.py']}
    imports['coursework/library-management-system/backend/src/test/java/cn/kmbeast/AssistantFactsTest.java']=hash_file(REPO/'coursework/library-management-system/backend/src/test/java/cn/kmbeast/AssistantFactsTest.java')
    names=['CONTRACT.md','plan.json','cases.json','fixtures.json','preflight-labels.json','common.py','collect.py','native.py','freeze.py','measure.py','verify.py','tests/test_measure.py','native/LibraryQueryControlsReplayTest.java','native/QingyeQueryControlsReplayTest.java','prompts/library.txt','prompts/qingye.txt']
    write(R/'seal.json',dict(parentSha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),productSha=read(R/'plan.json')['productSha'],research={n:hash_file(R/n) for n in names},product=product,imports=imports,callsObservedAtSeal=0,preflightRecords=len(records),modelReachableCases=sum(l['plannerReachable'] for l in labels),scope='New exploratory mechanism controls, not final replication; no product edits'))
    print('Sealed',len(cases),'questions;',sum(l['plannerReachable'] for l in labels),'planner-reachable;',len(records),'native preflight/control records')
if __name__=='__main__':main()
