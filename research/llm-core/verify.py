"""Offline evidence/readback checks. Does not call providers or repair records."""
import hashlib,json,re,subprocess
from pathlib import Path
from core import digest
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def main():
 frozen=json.loads((ROOT/'frozen-core-v2.json').read_text(encoding='utf-8'))
 portable=json.loads((ROOT/'source-portability.json').read_text(encoding='utf-8'))
 assert portable['sourceSha']=='dbb32160a811fd06c826a8d9eafbc660a0548219'
 for name,h in frozen['research'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
 for name,h in frozen['production'].items():
  content=(REPO/name).read_bytes()
  assert hashlib.sha256(content.replace(b'\r\n',b'\n')).hexdigest()==portable['productionLfSha256'][name],name
  # Original Windows byte identity remains recorded; only Git checkout EOL may differ.
  blob=subprocess.check_output(['git','show',portable['sourceSha']+':'+name],cwd=REPO)
  assert hashlib.sha256(blob.replace(b'\r\n',b'\n')).hexdigest()==portable['productionLfSha256'][name],name
 core=ROOT/'results/core';calls=lines(core/'calls.jsonl');blocks=lines(core/'blocks.jsonl');journal=lines(core/'request-journal.jsonl')
 assert len(calls)==len({c['callId'] for c in calls})==1728
 assert len(blocks)==len({b['block'] for b in blocks})==144
 assert {c['callId'] for c in calls}=={j['callId'] for j in journal}
 for c in calls:assert digest(c['request'])==c['requestHash'],c['callId']
 assert sum(c['transport']=='UNKNOWN_INTERRUPTED' for c in calls)==1
 for b in blocks:
  for role,models in [('p',[(m,str(i)) for m in ('a','b') for i in range(4)]),('r',[(m,n) for m in ('a','b') for n in ('a','b')])]:
   for m,n in models:assert any(c['callId']==f"{b['block']}/{role}/{m}/{n}" for c in calls)
 for system in ('qingye','library'):
  records=lines(core/f'native-v2/native-{system}.jsonl')
  assert len(records)==581 and all(r['databaseUnchanged'] for r in records)
  assert all('confirmationToken' not in r['response'] or r['response']['confirmationToken'] is None for r in records)
 # Retained scopes may mention foreign IDs as negative controls; actual credentials must not occur.
 suspicious=re.compile('s'+'k-(?:ws-[A-Za-z0-9_.-]{20,}|[0-9a-f]{24,})|a'+'rk-[0-9a-f-]{30,}')
 for p in ROOT.rglob('*'):
  if p.is_file() and p.suffix in ('.json','.jsonl','.txt','.md','.py','.ps1','.java','.csv','.html'):
   assert not suspicious.search(p.read_text(encoding='utf-8',errors='replace')),str(p.relative_to(ROOT))
 report=json.loads((core/'evaluation-v2/report.json').read_text(encoding='utf-8'))
 assert report['pairedBlocks']==144 and report['nativeControlsPassed'] and report['allSnapshotsUnchanged']
 ext=ROOT/'extension';ef=json.loads((ext/'frozen-core-v2.json').read_text(encoding='utf-8'))
 for name,h in ef['research'].items():assert hashlib.sha256((ext/name).read_bytes()).hexdigest()==h,name
 ec=lines(ext/'results/core/calls.jsonl');eb=lines(ext/'results/core/blocks.jsonl');ej=lines(ext/'results/core/request-journal.jsonl')
 assert len(ec)==len({c['callId'] for c in ec})==768 and len(eb)==len({b['block'] for b in eb})==64
 assert {c['callId'] for c in ec}=={c['callId'] for c in ej}
 assert all(c['complete'] and c['httpStatus']==200 and digest(c['request'])==c['requestHash'] for c in ec)
 ep=json.loads((ext/'results/core/evaluation-v2/report.json').read_text(encoding='utf-8'))
 assert ep['pairedBlocks']==64 and ep['nativeControlsPassed'] and ep['allSnapshotsUnchanged']
 for system in ('qingye','library'):
  er=lines(ext/f'results/core/native-v2/native-{system}.jsonl')
  assert len(er)==261 and all(r['databaseUnchanged'] for r in er)
  hr=lines(ROOT/f'history/native-{system}.jsonl')
  assert len(hr)==(271 if system=='qingye' else 135) and all(r['databaseUnchanged'] for r in hr)
 # All eight control families are accounted for; unproven studies must stay explicit.
 ledger=json.loads((ROOT/'CONTROL_LEDGER.json').read_text(encoding='utf-8'))
 assert {r['family'] for r in ledger['controls']}==set(range(1,9))
 assert not any(r['status']=='RUNNING' for r in ledger['controls'])
 assert all(c['status']=='NOT_QUALIFIED' for c in ledger['claims'] if c['id'] in ('K3','K4','K5'))
 print('Offline verifier: PASS; core 144/1728, extension 64/768, historical replay 406, Git source/EOL binding, raw hashes, native controls, no retained credentials; broad claims remain unqualified')
if __name__=='__main__':main()
