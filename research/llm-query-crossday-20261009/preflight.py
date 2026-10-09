"""Offline adapter/source/order checks; never call a provider."""
import json
import random
from datetime import datetime, timezone
from common import R, ORIGIN, read, lines, write, hash_file, check_origin, net, digest, stage_time, budget_state


def main():
    check_origin()
    for stage in ('proposal', 'review'):
        stage_time(stage)
    copies = ['plan.json', 'cases.json', 'fixtures.json', 'preflight-labels.json',
              'native.py', 'measure_v2.py', 'review_measure.py', 'prompts/library.txt',
              'prompts/qingye.txt', 'prompts/review.txt',
              'native/LibraryQueryControlsReplayTest.java', 'native/QingyeQueryControlsReplayTest.java']
    for name in copies:
        assert (R / name).read_bytes() == (ORIGIN / name).read_bytes(), name
    for p in R.glob('*.py'):
        compile(p.read_text(encoding='utf-8'), str(p), 'exec')
    plan = read(R / 'plan.json')
    cases = read(R / 'cases.json')
    eligible = {x['caseId'] for x in read(R / 'preflight-labels.json') if x['plannerReachable']}
    assert len(cases) == 42 and len(eligible) == 39
    schedule = [(r, c) for r in range(plan['repetitions']) for c in cases if c['id'] in eligible]
    rng = random.Random(plan['seed']); rng.shuffle(schedule)
    built = []
    for repeat, c in schedule:
        slots = ['a', 'b']; rng.shuffle(slots)
        for slot in slots:
            body = net.payload(plan['providers'][slot], (R / f'prompts/{c["system"]}.txt').read_text(encoding='utf-8'), c['question'], plan['maxTokens'][c['system']])
            built.append((f'QC4/{c["id"]}/r{repeat}/{slot}', digest(body)))
    prior = lines(ORIGIN / 'results/calls.jsonl')
    assert built == [(c['callId'], c['requestHash']) for c in prior] and len(built) == 234
    reviewplan = read(R / 'review-plan.json')
    restored = json.loads(json.dumps(reviewplan))
    for job in restored['jobs']:
        job['candidateCallId'] = job['candidateCallId'].replace('QC4-DAY1/', 'QC4/', 1)
    assert restored == read(ORIGIN / 'review-plan.json')
    jobs = list(reviewplan['jobs']); random.Random(reviewplan['seed']).shuffle(jobs)
    oldreviews = lines(ORIGIN / 'review-results/calls.jsonl')
    assert [(j['candidateCallId'].replace('QC4-DAY1/', 'QC4/', 1), j['reviewer']) for j in jobs] == [(r['candidateCallId'], r['reviewer']) for r in oldreviews]
    sources = {c['callId']: c for c in prior}; by_case = {c['id']: c for c in cases}
    for job, retained in zip(jobs, oldreviews):
        candidate = sources[job['candidateCallId'].replace('QC4-DAY1/', 'QC4/', 1)]
        case = by_case[candidate['caseId']]
        prompt = (R / 'prompts/review.txt').read_text(encoding='utf-8') + '\n被审系统协议：\n' + (R / f'prompts/{case["system"]}.txt').read_text(encoding='utf-8')
        user = json.dumps({'question': case['question'], 'candidate': candidate['rawContent']}, ensure_ascii=False)
        assert digest(net.payload(reviewplan['providers'][job['reviewer']], prompt, user, 250)) == retained['requestHash']
    budget = budget_state()
    assert budget['firstAndRepeat'] + .10 < 2 and all(v + .10 < 20 for v in budget['globalCumulative'].values())
    receipt = dict(status='PASS', observedAt=datetime.now(timezone.utc).isoformat(), paidCalls=0,
                   identicalCopies={n: hash_file(R / n) for n in copies},
                   proposalPayloadAndOrder=234, reviewOrderAndPromptReconstruction=468,
                   budgetBeforeFirstCall=budget, credentialStorage='No keys in files/environment/scheduler')
    dest = R / 'OFFLINE_PREFLIGHT.json'
    assert not dest.exists(), 'Preserve preflight identity'
    write(dest, receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
