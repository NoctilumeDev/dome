"""Non-echo credential preload and timed call of the unchanged day1 runner.

No model request is made by this module. No credential is written to a file,
environment variable, process argument, status receipt, or exception message.
"""
import argparse
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import warnings

import collect
import second_window

R = Path(__file__).resolve().parent
STATUS = R / 'SECOND_WINDOW_WAIT_STATUS.json'
EVENTS = R / 'SECOND_WINDOW_WAIT_EVENTS.jsonl'
SEAL = R / 'wait-second-window-seal.json'


def preflight():
    seal = collect.read(SEAL)
    for name, digest in seal['files'].items():
        assert hashlib.sha256((R / name).read_bytes()).hexdigest() == digest, 'Wait launcher input changed: ' + name
    collect.check()
    collect.check(runtime=True)
    first = collect.read(R / 'WINDOW_STATUS.json')
    assert first['stop'] == 'WAIT_FOR_NEW_24H_WINDOW' and first['credentialsCleared']
    matrix = collect.read(R / 'matrix.json')
    suites = [x for x in matrix['suites'] if x['guardAfterFinishedSuite']]
    assert [x['id'] for x in suites] == ['time-day1', 'query-day1', 'query-review-day1']
    assert sum(x['requests'] for x in suites) == 774
    assert first['completedSuites'] == [x['id'] for x in matrix['suites'] if not x['guardAfterFinishedSuite']]
    assert not (R / 'SECOND_WINDOW_STATUS.json').exists(), 'Second-window attempt is already retained'
    deadlines = []
    for suite in suites:
        assert not (R / 'results' / suite['id']).exists(), 'Prior day1 attempt is retained'
        previous = collect.read(R / 'results' / suite['guardAfterFinishedSuite'] / 'summary.json')
        assert previous['stop'] is None and previous['requests'] == previous['plannedRequests']
        deadlines.append(datetime.fromisoformat(previous['finishedAt']) + timedelta(seconds=suite['minimumGapSeconds']))
    eligibility = collect.read(R / 'SECOND_WINDOW_ELIGIBILITY.json')
    assert max(deadlines) == datetime.fromisoformat(eligibility['earliestAllGuardsUtc'])
    not_before = max(max(deadlines), datetime.fromisoformat(eligibility['scheduledWakeShanghai']).astimezone(timezone.utc))
    retained = [x for path in sorted((R / 'results').glob('*/calls.jsonl')) for x in collect.rows(path)]
    history = {x['callId'] for x in retained}
    assert len(history) == len(retained) == 7446
    for path in (R / 'results').glob('*/request-journal.jsonl'):
        assert all(x['callId'] in history for x in collect.rows(path)), 'Unknown attempt prevents continuation'
    cumulative = collect.totals(matrix, retained)
    assert all(value + matrix['reserveBeforeEachRequestCny'] <= matrix['hardCumulativePerProviderCny'] for value in cumulative.values())
    return suites, not_before, cumulative


def record(state, **extra):
    value = dict(state=state, observedAt=datetime.now(timezone.utc).isoformat(), pid=os.getpid(), **extra)
    collect.net.append(EVENTS, value)
    collect.write(STATUS, value)
    return value


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    suites, not_before, cumulative = preflight()
    if args.preflight_only:
        print(json.dumps(dict(preflight='PASS', modelRequests=0, remainingRequests=774,
                             notBeforeUtc=not_before.isoformat(), globalConservativeCny=cumulative)))
        return
    assert not STATUS.exists() and not EVENTS.exists(), 'An earlier preload attempt is retained'
    if not sys.stdin.isatty():
        raise SystemExit('Non-echo console required')
    warnings.simplefilter('error', getpass.GetPassWarning)
    original_getpass = getpass.getpass
    credential_text = ''
    keys = {}
    state = 'PRELOAD_STARTED'
    record(state, notBeforeUtc=not_before.isoformat(), credentialReferencesHeld=False, modelRequests=0)
    try:
        credential_text = original_getpass('CREDENTIAL_INPUT: ')
        try:
            keys = json.loads(credential_text)
            assert set(keys) == {'deepseek', 'qwen'}
            assert all(isinstance(v, str) and v.strip() for v in keys.values())
        except Exception:
            raise RuntimeError('Invalid credential envelope') from None
        state = 'CREDENTIALS_READY_WAITING'
        record(state, notBeforeUtc=not_before.isoformat(), credentialReferencesHeld=True, modelRequests=0)
        print('CREDENTIALS_READY_WAITING_UNTIL=' + not_before.isoformat(), flush=True)
        while True:
            remaining = (not_before - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(30.0, remaining))
        suites, not_before, cumulative = preflight()
        assert datetime.now(timezone.utc) >= not_before
        gaps = [collect.stage_guard(suite) for suite in suites]
        state = 'SECOND_WINDOW_RUNNING'
        record(state, notBeforeUtc=not_before.isoformat(), credentialReferencesHeld=True,
               paymentGuards=gaps, globalConservativeCny=cumulative)
        getpass.getpass = lambda _: credential_text
        second_window.main()
        state = 'SECOND_WINDOW_COMPLETED'
    except BaseException as error:
        state = 'PRELOAD_OR_RUN_STOPPED'
        record(state, credentialReferencesHeld=bool(credential_text), stopType=type(error).__name__)
        print('WAIT_RUNNER_STOP_TYPE=' + type(error).__name__, flush=True)
        raise SystemExit(2) from None
    finally:
        keys.clear()
        credential_text = ''
        getpass.getpass = original_getpass
        record(state, credentialReferencesHeld=False, credentialsCleared=True)
        print('WAIT_RUNNER_CREDENTIAL_REFERENCES_CLEARED', flush=True)


if __name__ == '__main__':
    main()
