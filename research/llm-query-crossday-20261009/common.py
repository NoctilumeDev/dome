"""Coordinate adapter only; all semantic helpers and transport come from frozen QC4."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = R.parents[1]
ORIGIN = R.parent / 'llm-query-controls-20261008'
spec = importlib.util.spec_from_file_location('qc4_frozen_common', ORIGIN / 'common.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
read, write, lines, hash_file = original.read, original.write, original.lines, original.hash_file
digest, net, parse_plan = original.digest, original.net, original.parse_plan
primary_match, goal_rows_match, facts_match = original.primary_match, original.goal_rows_match, original.facts_match


def check_origin():
    original.check()
    version = read(ORIGIN / 'measurement-v2.json')
    assert hash_file(ORIGIN / 'seal.json') == version['parentSealSha256']
    for name, expected in version['files'].items():
        assert hash_file(ORIGIN / name) == expected
    review = read(ORIGIN / 'review-seal.json')
    assert review['originalSealHash'] == hash_file(ORIGIN / 'seal.json')
    for name, expected in review['files'].items():
        assert hash_file(ORIGIN / name) == expected


def check():
    check_origin()
    seal = read(R / 'seal.json')
    for name, expected in seal['files'].items():
        assert hash_file(R / name) == expected, 'Frozen day1 adapter differs: ' + name
    for name, expected in seal['origins'].items():
        assert hash_file(REPO / name) == expected, 'Frozen origin differs: ' + name
    return seal


def stage_time(stage):
    folder = 'results' if stage == 'proposal' else 'review-results'
    end = datetime.fromisoformat(read(ORIGIN / folder / 'summary.json')['finishedAt'])
    now = datetime.now(timezone.utc)
    shanghai = timezone(timedelta(hours=8))
    assert (now - end).total_seconds() >= 86400, 'REAL_24H_NOT_REACHED'
    assert now.astimezone(shanghai).date() > end.astimezone(shanghai).date(), 'SHANGHAI_DATE_NOT_CHANGED'


def budget_state():
    baseline = read(ORIGIN / 'output-v2/physical-resources.json')['providers']
    day1 = lines(REPO / 'research/llm-controls-layer3-20261008/results/day1/calls.jsonl')
    fresh = lines(R / 'results/calls.jsonl') + lines(R / 'review-results/calls.jsonl')
    cost = lambda c: c['estimatedCostCny'] if c['estimatedCostCny'] is not None else .05
    added = {p: sum(cost(c) for c in fresh if c['provider'] == p) for p in baseline}
    total = {p: baseline[p]['conservativeCumulativeCny'] + sum(cost(c) for c in day1 if c['provider'] == p) + added[p] for p in baseline}
    first = sum(v['conservativeNewEstimateCny'] for v in baseline.values())
    return dict(new=added, globalCumulative=total, firstAndRepeat=first + sum(added.values()))


def budget_boundary(provider, stage):
    stage_time(stage)
    value = budget_state()
    return value['firstAndRepeat'] + .10 > 2 or value['globalCumulative'][provider] + .10 > 20


def review_input_check():
    check()
    pool = read(R / 'review-input-seal.json')
    for name, expected in pool['files'].items():
        assert hash_file(R / name) == expected, 'New proposal pool changed: ' + name
    assert pool['proposals'] == 234 and pool['reviewsAtSeal'] == 0
