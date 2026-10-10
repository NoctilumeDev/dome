"""Read-only provenance verification. Never repairs, resends or scores a plan."""
import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from collect import R, read, rows, check, net

def main():
    p=argparse.ArgumentParser();p.add_argument('window',choices=['first-window','full-matrix']);a=p.parse_args()
    check();matrix=read(R/'matrix.json');jobs=rows(R/'jobs.jsonl')
    suites=[s for s in matrix['suites'] if a.window=='full-matrix' or not s['guardAfterFinishedSuite']]
    seen={};checks=[]
    for suite in suites:
        root=R/'results'/suite['id'];summary=read(root/'summary.json');records=rows(root/'calls.jsonl');journal=rows(root/'request-journal.jsonl')
        expected=[j for j in jobs if j['suite']==suite['id']]
        assert summary['stop'] is None and len(records)==len(journal)==len(expected)==suite['requests']
        assert summary['requests']==summary['plannedRequests']==suite['requests']
        assert [r['callId'] for r in records]==[j['callId'] for j in expected]==[j['callId'] for j in journal]
        for job,record,entry in zip(expected,records,journal):
            assert record['callId'] not in seen
            assert record['legacyCallId']==job['legacyCallId']
            assert record['provider']==job['provider'] and record['system']==job['system']
            assert record['caseId']==job['caseId'] and record['role']==job['role']
            assert record['sourceMetadata']==job['sourceMetadata']
            assert record['sourceRequestHash']==job['sourceRequestHash']
            assert record['candidateDependency']==entry['candidateDependency']==job['candidateDependency']
            body=copy.deepcopy(job['request'])
            if job['candidateDependency']:
                candidate=seen[job['candidateDependency']]['rawContent']
                content=json.loads(body['messages'][-1]['content']);content['candidate']=candidate
                body['messages'][-1]['content']=json.dumps(content,ensure_ascii=False)
                assert entry['candidateSha256']==hashlib.sha256(candidate.encode()).hexdigest()
            else:
                assert entry['candidateSha256'] is None
                assert net.digest(body)==job['sourceRequestHash']
            assert body==record['request']
            assert net.digest(body)==record['requestHash']==entry['requestHash']
            assert record['requestedModel']==job['request']['model']
            assert datetime.fromisoformat(entry['startedAt'])<=datetime.fromisoformat(record['observedAt'])
            seen[record['callId']]=record
        if suite['guardAfterFinishedSuite']:
            prior=read(R/'results'/suite['guardAfterFinishedSuite']/'summary.json')
            gap=(datetime.fromisoformat(summary['startedAt'])-datetime.fromisoformat(prior['finishedAt'])).total_seconds()
            assert gap>=86400 and summary['gap']['gapSeconds']>=86400
        checks.append(dict(suite=suite['id'],requests=len(records),freshIdentityOrder='PASS',payloadBinding='PASS',
            reviewCandidateBinding='PASS',callsSha256=hashlib.sha256((root/'calls.jsonl').read_bytes()).hexdigest(),
            journalSha256=hashlib.sha256((root/'request-journal.jsonl').read_bytes()).hexdigest()))
    result=dict(version='replication-provenance-receipt-v1',window=a.window,requests=len(seen),
        observedAt=datetime.now(timezone.utc).isoformat(),frozenInputs='PASS',suites=checks,
        qualification='Identity, order and payload provenance only; semantic/native qualification comes from unchanged scorers and retained witnesses')
    dest=R/'verification'/a.window;assert not dest.exists(),'Keep first verification receipt';dest.mkdir(parents=True)
    (dest/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(window=a.window,requests=len(seen),provenance='PASS'),ensure_ascii=False))

if __name__=='__main__':main()
