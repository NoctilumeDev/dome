"""Read-only check of the all-proposal review intervention and accounting."""
from collections import Counter
from common import R, read, lines, hash_file, net, digest
from review_collect import review_check
from core import review

def main():
    review_check();seal=read(R/'review-seal.json');plan=read(R/'review-plan.json');props={p['callId']:p for p in lines(R/'results/calls.jsonl')};cases={c['id']:c for c in read(R/'cases.json')}
    reviews=lines(R/'review-results/calls.jsonl');journal=lines(R/'review-results/request-journal.jsonl');summary=read(R/'review-results/summary.json')
    assert len(props)==234 and len(plan['jobs'])==len(props)*2==468 and seal['reviewsAtSeal']==0
    assert {(j['candidateCallId'],j['reviewer']) for j in plan['jobs']}=={(cid,s) for cid in props for s in ['a','b']}
    assert len({r['callId'] for r in reviews})==len(reviews) and len({j['callId'] for j in journal})==len(journal)
    unknown={j['callId'] for j in journal}-{r['callId'] for r in reviews}
    if summary['stop'] is None:assert len(reviews)==468 and not unknown
    for r in reviews:
        candidate=props[r['candidateCallId']];c=cases[candidate['caseId']];provider=plan['providers'][r['reviewer']]
        prompt=(R/'prompts/review.txt').read_text(encoding='utf-8')+'\n被审系统协议：\n'+(R/f'prompts/{c["system"]}.txt').read_text(encoding='utf-8')
        user=__import__('json').dumps({'question':c['question'],'candidate':candidate['rawContent']},ensure_ascii=False)
        body=net.payload(provider,prompt,user,250)
        assert r['request']==body and r['requestHash']==digest(body) and r['caseId']==candidate['caseId']
        assert r['collectorSha256']==seal['files']['review_collect.py'] and r['estimatedCostCny']==net.estimate_cost(r,provider)
        assert 'authorization' not in __import__('json').dumps(r).lower()
    cost={p:sum(r['estimatedCostCny'] if r['estimatedCostCny'] is not None else .05 for r in reviews if r['provider']==p) for p in ['deepseek','qwen']}
    assert sum(cost.values())+plan['proposalBudgetUsedCny']<=2
    for provider,value in cost.items():assert value+plan['cumulativeBeforeReviewCny'][provider]+plan['reservedDay1CnyPerProvider']<=20
    if (R/'review-output/metrics.json').exists():
        metrics=read(R/'review-output/metrics.json');details=read(R/'review-output/details.json')
        assert metrics['pairedBlocks']==len(details)==117 and metrics['reviewRequestIdentities']==len(reviews)
        assert metrics['BresidualWrongOpportunities']==sum(d['BwrongQueryOrScopeOpportunity'] for d in details)
        for d in details:
            b=d['strategies']['B']['allowed']
            assert all(not d['strategies'][s]['allowed'] or b for s in ['C:a','C:b','D'])
        for strategy,m in metrics['strategies'].items():
            assert m['incrementalWrongQueryOrScopeBlocked']==sum(d['BwrongQueryOrScopeOpportunity'] and d['strategies'][strategy]['incrementalVeto'] for d in details)
            assert m['incrementalCorrectQueryOrScopeBlocked']==sum(d['BcorrectQueryOrScope'] and d['strategies'][strategy]['incrementalVeto'] for d in details)
    print(__import__('json').dumps(dict(status='PASS',reviewRequests=len(reviews),journalOnlyUnknown=len(unknown),reviewFormats=dict(Counter(review(r['rawContent']) if r['complete'] else 'UNAVAILABLE' for r in reviews)),newReviewEstimateCny=cost,proposalResubmissions=0),ensure_ascii=False))
if __name__=='__main__':main()
