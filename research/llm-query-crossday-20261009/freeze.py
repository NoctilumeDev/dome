"""Freeze initial adapters or the complete fresh proposal pool, before paid calls."""
import argparse
from datetime import datetime, timezone
from common import R, REPO, ORIGIN, read, write, lines, hash_file, check, check_origin


def main():
    p = argparse.ArgumentParser(); p.add_argument('stage', choices=['initial', 'review']); a = p.parse_args()
    if a.stage == 'initial':
        check_origin()
        assert not (R / 'seal.json').exists() and not (R / 'results').exists()
        assert read(R / 'OFFLINE_PREFLIGHT.json')['status'] == 'PASS'
        names = ['CONTRACT.md', 'ADAPTATION.diff', 'common.py', 'collect.py', 'review_collect.py',
                 'native.py', 'measure_v2.py', 'review_measure.py', 'preflight.py', 'freeze.py',
                 'verify.py', 'compare.py', 'plan.json', 'review-plan.json', 'cases.json',
                 'fixtures.json', 'preflight-labels.json', 'OFFLINE_PREFLIGHT.json',
                 'prompts/library.txt', 'prompts/qingye.txt', 'prompts/review.txt',
                 'native/LibraryQueryControlsReplayTest.java', 'native/QingyeQueryControlsReplayTest.java']
        origins = ['research/llm-query-controls-20261008/' + n for n in
                   ['seal.json', 'measurement-v2.json', 'review-seal.json', 'results/calls.jsonl',
                    'results/summary.json', 'results/native/snapshot-library.json', 'results/native/snapshot-qingye.json',
                    'output-v2/details.json', 'output-v2/metrics.json', 'output-v2/physical-resources.json',
                    'review-results/calls.jsonl', 'review-results/summary.json', 'review-output/details.json', 'review-output/metrics.json']]
        origins += ['research/llm-controls-layer3-20261008/results/day1/calls.jsonl',
                    'research/llm-controls-layer3-20261008/output-day1/VERIFICATION.json']
        write(R / 'seal.json', dict(version='QC4-DAY1-v1', frozenAt=datetime.now(timezone.utc).isoformat(),
                                   files={n: hash_file(R / n) for n in names},
                                   origins={n: hash_file(REPO / n) for n in origins},
                                   paidCallsAtSeal=0, plannedProposals=234, plannedReviews=468))
        check(); print('INITIAL SEAL PASS; must commit before paid collection')
    else:
        check(); assert not (R / 'review-input-seal.json').exists() and not (R / 'review-results').exists()
        summary = read(R / 'results/summary.json'); assert summary['stop'] is None and summary['requestIdentities'] == 234
        calls = lines(R / 'results/calls.jsonl'); assert len(calls) == len({c['callId'] for c in calls}) == 234
        assert len(read(R / 'output-v2/details.json')) == 234
        files = ['results/calls.jsonl', 'results/summary.json', 'results/native/input.json',
                 'results/native/native-library.jsonl', 'results/native/native-qingye.jsonl',
                 'results/native/snapshot-library.json', 'results/native/snapshot-qingye.json',
                 'output-v2/details.json', 'output-v2/metrics.json']
        write(R / 'review-input-seal.json', dict(version='QC4-DAY1-REVIEW-v1',
              frozenAt=datetime.now(timezone.utc).isoformat(), proposals=234, reviewsAtSeal=0,
              selectedAllFrozenQuestions=True, files={n: hash_file(R / n) for n in files}))
        print('FRESH POOL SEAL PASS; must commit before paid reviews')


if __name__ == '__main__':
    main()
