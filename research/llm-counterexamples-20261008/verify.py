import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1];sys.path.insert(0,str(R.parent/'llm-core'))
from core import digest
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def main():
 frozen=json.loads((R/'frozen-core-v2.json').read_text())
 for n,h in frozen['research'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 assert not subprocess.check_output(['git','diff','--name-only','60cd5d4','--','research/llm-core','qingye/backend/src/main','coursework/library-management-system/backend/src/main'],cwd=REPO)
 portable=json.loads((R.parent/'llm-core/source-portability.json').read_text())
 for n,h in frozen['production'].items():assert hashlib.sha256((REPO/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==portable['productionLfSha256'][n],n
 for phase,count in [('core',1536),('challenge',96)]:
  calls=lines(R/f'results/{phase}/calls.jsonl');journal=lines(R/f'results/{phase}/request-journal.jsonl')
  assert len(calls)==len({c['callId'] for c in calls})==count
  assert {c['callId'] for c in calls}=={j['callId'] for j in journal}
  assert all(digest(c['request'])==c['requestHash'] for c in calls)
 for s,n in [('qingye',397),('library',653)]:
  native=lines(R/f'results/core/native-v2/native-{s}.jsonl');assert len(native)==n and all(x['databaseUnchanged'] for x in native)
  assert all(x['response'].get('confirmationToken') is None for x in native)
 suspicious=re.compile('s'+'k-(?:ws-[A-Za-z0-9_.-]{20,}|[0-9a-f]{24,})')
 for p in R.rglob('*'):
  if p.is_file() and p.suffix in ('.json','.jsonl','.md','.txt','.py','.html','.csv'):assert not suspicious.search(p.read_text(encoding='utf-8',errors='replace')),p
 print('Second layer verifier PASS; frozen source/prompts/scorer, 1536 natural + 96 injected reviews, original evidence unchanged, snapshots and retained credentials checked')
if __name__=='__main__':main()
