"""Read-only day1 evidence reconciliation; never rewrite raw data or score rules."""
import hashlib
import json
import math
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R.parent / 'llm-core'))
from core import digest, parse_plan, score_plan
from collect import check


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    check()
    launch = read(R / 'diagnostics/day1-launch.json')
    assert launch['paidCallsAtPreparation'] == 0
    assert launch['originalCollectorSha256'] == sha(R / 'collect.py')
    assert launch['guardSha256'] == sha(R / 'day1_global_budget_guard.py')
    assert launch['parentSealSha256'] == sha(R / 'seal.json')
    baseline_path = R / launch['globalBaselineSource']
    assert launch['globalBaselineSha256'] == sha(baseline_path)
    s0 = read(R / 'results/day0/summary.json')
    s1 = read(R / 'results/day1/summary.json')
    start, end0 = datetime.fromisoformat(s1['startedAt']), datetime.fromisoformat(s0['finishedAt'])
    gap = (start - end0).total_seconds()
    shanghai = timezone(timedelta(hours=8))
    assert gap >= 86400 and start.astimezone(shanghai).date() > end0.astimezone(shanghai).date()
    assert datetime.fromisoformat(launch['preparedAt']) < start
    assert s1['stop'] is None and s1['requestIdentities'] == 72
    assert s1['completedBlocks'] == s1['plannedBlocks'] == 36
    cases = {c['id']: c for c in read(R / 'cases.json')}
    raw = {phase: lines(R / f'results/{phase}/calls.jsonl') for phase in ('day0', 'day1')}
    assert [c['callId'] for c in raw['day0']] == [c['callId'] for c in raw['day1']]
    assert len(raw['day1']) == len({c['callId'] for c in raw['day1']}) == 72
    journal = {j['callId']: j for j in lines(R / 'results/day1/request-journal.jsonl')}
    assert set(journal) == {c['callId'] for c in raw['day1']}
    native = {phase: {n['callId']: n for system in ('qingye', 'library')
                     for n in lines(R / f'results/{folder}/native-{system}.jsonl')}
              for phase, folder in [('day0', 'native-all'), ('day1', 'native-day1')]}
    assert len(native['day1']) == 82 and all(n['databaseUnchanged'] for n in native['day1'].values())
    source = {n['callId']: n for n in read(R / 'results/native-input-day1.json')}
    assert set(source) == set(native['day1'])
    paired = {p['callId']: p for p in read(R / 'output-day1/paired-ledger.json')}
    assert len(paired) == 72
    for c0, c1 in zip(raw['day0'], raw['day1']):
        assert c0['requestHash'] == c1['requestHash'] == digest(c0['request']) == digest(c1['request'])
        assert c1['requestHash'] == journal[c1['callId']]['requestHash']
        assert c0['requestedModel'] == c1['requestedModel'] and c0['caseId'] == c1['caseId']
        assert c1['phase'] == 'day1' and c1['collectorSha256'] == sha(R / 'collect.py')
        assert c1['httpStatus'] == 200 and c1['transport'] == 'SUCCESS' and c1['complete']
        assert c1['rawContent'] == c1['response']['choices'][0]['message']['content']
        src = source['day1/' + c1['callId']]
        assert src['rawContent'] == c1['rawContent'] and src['complete'] == c1['complete']
        assert src['question'] == cases[c1['caseId']]['question'] and src['system'] == c1['system']
        for phase, c in [('day0', c0), ('day1', c1)]:
            p, _ = parse_plan(c['system'], c['rawContent'])
            match = bool(c['complete'] and p is not None and score_plan(p, cases[c['caseId']]['oracle'])['proposal_correct'])
            n = native[phase][phase + '/' + c['callId']]
            entry = paired[c['callId']][phase]
            assert entry['match'] == match and entry['nativeQualified'] == n['nativeQualified']
            assert entry['status'] == n['response']['status']
            if c['caseId'] == 'library-R3-formal-06-1':
                if c['provider'] == 'deepseek':
                    assert n['response']['status'] == 'QUERY' and n['repositoryQueriesBeforeConfirm'] == 1
                else:
                    assert n['response']['status'] == 'REJECT' and n['repositoryQueriesBeforeConfirm'] == 0
    for system in ('qingye', 'library'):
        assert (R / f'results/native-all/snapshot-{system}.json').read_bytes() == (R / f'results/native-day1/snapshot-{system}.json').read_bytes()
        assert native['day1'][f'CONTROL/day1/{system}/positive']['response']['status'] == 'QUERY'
        for variant in ('foreign-user', 'missing-field', 'transport', 'omitted-private-filter'):
            n = native['day1'][f'CONTROL/day1/{system}/{variant}']
            assert n['response']['status'] != 'QUERY'
            if system == 'library':
                assert n['repositoryQueriesBeforeConfirm'] == 0
            else:
                assert not n['askSql']
        assert native['day1'][f'CONTROL/day1/{system}/omitted-private-filter']['response']['status'] == 'CONFIRM_SCOPE'
    plan = read(R / 'plan.json')
    resources = read(R / 'output-day1/physical-resources.json')['providers']
    baseline = read(baseline_path)['providers']
    for slot in ('a', 'b'):
        model = plan['providers'][slot]
        provider = model['name']
        calls = [c for c in raw['day1'] if c['provider'] == provider]
        row = resources[provider]
        assert len(calls) == row['requests'] == row['transportSuccess'] == 36
        inputs = sum(c['response']['usage']['prompt_tokens'] for c in calls)
        outputs = sum(c['response']['usage']['completion_tokens'] for c in calls)
        assert inputs == row['knownInputTokens'] and outputs == row['knownOutputTokens'] and row['usageMissing'] == 0
        estimate = (inputs * model['inputCnyPerMillion'] + outputs * model['outputCnyPerMillion']) / 1_000_000
        assert abs(estimate - row['conservativeNewCny']) < 1e-9
        prior = baseline[provider]['conservativeCumulativeCny']
        assert row['baselineConservativeCumulativeCny'] == prior
        assert abs(prior + estimate - row['conservativeGlobalCumulativeCny']) < 1e-9
        assert prior + estimate <= 20
        latencies = sorted(c['elapsedMs'] for c in calls)
        assert row['p50Ms'] == statistics.median(latencies)
        assert row['p95Ms'] == latencies[math.ceil(.95 * len(latencies)) - 1]
    metrics = read(R / 'output-day1/metrics.json')
    assert metrics['gapSeconds'] == gap and metrics['reporterSha256'] == sha(R / 'day1_report.py')
    for row in metrics['summary']:
        ps = [p for p in paired.values() if p['slot'] == row['slot']]
        assert row['pairedObservations'] == len(ps) == 36
        for phase in ('day0', 'day1'):
            assert row[phase]['match'] == sum(p[phase]['match'] for p in ps)
            assert row[phase]['qualified'] == sum(p[phase]['nativeQualified'] for p in ps)
    secret = re.compile(rb'(?:sk-[a-z0-9]{32,}|sk-ws-[A-Za-z0-9._-]{24,}|Bearer\s+sk-[A-Za-z0-9_.-]{12,})')
    for folder in (R, R.parent / 'llm-query-controls-20261008'):
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in ('.py', '.json', '.jsonl', '.md', '.csv', '.txt', '.html'):
                assert not secret.search(p.read_bytes()), 'Credential residue ' + str(p)
    print(json.dumps(dict(status='PASS', verifiedAt=datetime.now(timezone.utc).isoformat(),
                         requests=72, nativeRecords=82, gapSeconds=gap,
                         checks=['frozen source/tools', 'pre-call guard provenance', 'payload/order/date',
                                 'raw/native/scorer correspondence', 'price failure actual disposition',
                                 'negative controls and snapshots', 'usage and global budgets', 'secret residues']),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
