"""Verify recovery provenance and complete accounting, without changing old scores."""
import hashlib, json, subprocess, sys
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = R.parents[1]

def readlines(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]

def main():
    subprocess.run([sys.executable,'-X','utf8','-B',str(R/'verify.py')],check=True,cwd=REPO)
    seal=json.loads((R/'window2-seal-v1.1.json').read_text(encoding='utf-8'))
    for p,h in seal['files'].items():
        assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
    original_hash=hashlib.sha256((R.parent/'llm-core/run.py').read_bytes()).hexdigest()
    recovery_hash=seal['files']['run-window2.py']
    natural=readlines(R/'results/core/calls.jsonl')
    assert len(natural)==1536
    assert all(x['collectorSha256']==original_hash for x in natural[:12])
    assert all(x['collectorSha256']==recovery_hash for x in natural[12:])
    assert sum(x['transport']=='TIMEOUT' for x in natural[:12])==6
    first=json.loads((R/'results/core/collection-summary-window1.json').read_text(encoding='utf-8'))
    assert first['stop']=='USAGE_UNAVAILABLE' and first['callCount']==12
    current=json.loads((R/'results/core/collection-summary.json').read_text(encoding='utf-8'))
    assert current['window']=='bounded-recovery-1' and current['stop'] is None and current['retainedPrior']==12
    assert current['completedBlocks']==128
    injected=json.loads((R/'results/challenge/summary.json').read_text(encoding='utf-8'))
    assert injected['calls']==96 and injected['stop'] is None
    account=json.loads((R/'output/accounting-complete.json').read_text(encoding='utf-8'))
    assert all(x['cumulativeWithConservativeReserves']<=20 for x in account['budget'])
    for system in ('qingye','library'):
        preflight=readlines(R/f'diagnostics/native-preflight/native-{system}.jsonl')
        candidates=[x for x in preflight if x['callId'].startswith('CHALLENGE/')]
        assert len(candidates)==8 and all(x['nativeQualified'] and x['databaseUnchanged'] for x in candidates)
    print('Recovery provenance and all-call budget PASS; first failure retained; old layer unchanged; humans and unrun controls remain unqualified')

if __name__=='__main__':main()
