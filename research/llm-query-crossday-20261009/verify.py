"""Read-only fresh-coordinate/native/scorer/global-budget reconciliation."""
import json
from common import R, ORIGIN, read, lines, check, digest, net, parse_plan, primary_match, budget_state, review_input_check


def main():
    check(); cases = {c['id']: c for c in read(R / 'cases.json')}; plan = read(R / 'plan.json')
    calls = lines(R / 'results/calls.jsonl')
    if not calls:
        print('SOURCE SEAL PASS; paid requests NOT_RUN'); return
    summary = read(R / 'results/summary.json'); journal = lines(R / 'results/request-journal.jsonl')
    assert len(calls) == len({c['callId'] for c in calls})
    assert len(journal) == len({j['callId'] for j in journal})
    unknown = {j['callId'] for j in journal} - {c['callId'] for c in calls}
    if summary['stop'] is None:
        assert len(calls) == 234 and not unknown
    old = lines(ORIGIN / 'results/calls.jsonl')
    for c, prior in zip(calls, old):
        assert c['callId'].replace('QC4-DAY1/', 'QC4/', 1) == prior['callId']
        assert c['requestHash'] == prior['requestHash'] == digest(c['request'])
        assert c['request'] == prior['request'] and c['estimatedCostCny'] == net.estimate_cost(c, plan['providers'][c['callId'].rsplit('/', 1)[1]])
    native = {n['recordId']: n for system in ('library', 'qingye') for n in lines(R / f'results/native/native-{system}.jsonl')}
    if native:
        inputs = read(R / 'results/native/input.json'); by = {c['callId']: c for c in calls}
        assert len(inputs) == len(native)
        for src in inputs:
            n = native[src['recordId']]; c = by[src['callId']]
            assert src['rawContent'] == c['rawContent'] and src['complete'] == c['complete']
            assert src['question'] == cases[c['caseId']]['question']
            assert n['snapshotUnchanged'] and n['actor'] == src['actor'] and n['fixture'] == src['fixture']
            if n['response']['status'] == 'CONFIRM_SCOPE':
                assert n['crossActorRejected'] and n['crossSessionRejected'] and n['singleUse']
        for system in ('library', 'qingye'):
            assert (R / f'results/native/snapshot-{system}.json').read_bytes() == (ORIGIN / f'results/native/snapshot-{system}.json').read_bytes()
    if (R / 'output-v2/details.json').exists():
        detail = {d['callId']: d for d in read(R / 'output-v2/details.json')}; assert len(detail) == len(calls)
        for c in calls:
            p, error = parse_plan(c['system'], c['rawContent']) if c['complete'] else (None, 'INCOMPLETE')
            d = detail[c['callId']]
            assert d['plan'] == p and d['structureStatus'] == error and d['primaryPlanMatch'] == primary_match(p, cases[c['caseId']]['rule'], c['system'])
            for f in d['fixtures']:
                n = native[f['recordId']]
                assert f['nativeQualified'] == n['nativeQualified'] and f['status'] == n['response']['status'] and f['actualReadQueries'] == len(n['queryTrace'])
    reviews = lines(R / 'review-results/calls.jsonl')
    if reviews:
        review_input_check(); pmap = {c['callId']: c for c in calls}; rp = read(R / 'review-plan.json')
        assert len(reviews) == len({r['callId'] for r in reviews})
        if read(R / 'review-results/summary.json')['stop'] is None:
            assert len(reviews) == 468 and {(r['candidateCallId'], r['reviewer']) for r in reviews} == {(c, s) for c in pmap for s in ('a', 'b')}
        oldreviews = lines(ORIGIN / 'review-results/calls.jsonl')
        for r, prior in zip(reviews, oldreviews):
            c = pmap[r['candidateCallId']]; case = cases[c['caseId']]
            assert r['candidateCallId'].replace('QC4-DAY1/', 'QC4/', 1) == prior['candidateCallId'] and r['reviewer'] == prior['reviewer']
            prompt = (R / 'prompts/review.txt').read_text(encoding='utf-8') + '\n被审系统协议：\n' + (R / f'prompts/{case["system"]}.txt').read_text(encoding='utf-8')
            user = json.dumps({'question': case['question'], 'candidate': c['rawContent']}, ensure_ascii=False)
            assert r['request'] == net.payload(rp['providers'][r['reviewer']], prompt, user, 250)
            assert r['requestHash'] == digest(r['request']) and r['estimatedCostCny'] == net.estimate_cost(r, rp['providers'][r['reviewer']])
    budget = budget_state(); assert budget['firstAndRepeat'] <= 2 and all(v <= 20 for v in budget['globalCumulative'].values())
    print(json.dumps(dict(status='PASS', proposalRequests=len(calls), nativeRecords=len(native), reviews=len(reviews), journalOnlyUnknown=len(unknown), budget=budget), ensure_ascii=False))


if __name__ == '__main__':
    main()
