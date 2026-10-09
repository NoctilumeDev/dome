"""Assemble proposal observations and original controls without changing any model plan."""
import argparse,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core'
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',default='all');p.add_argument('--output',default='results/native-all');a=p.parse_args()
 cases={c['id']:c for c in json.loads((R/'cases.json').read_text())+json.loads((R/'external-cases.json').read_text())};inputs=[]
 for path in sorted((R/'results').glob('*/calls.jsonl')):
  if a.phase!='all' and path.parent.name!=a.phase:continue
  for line in path.read_text(encoding='utf-8').splitlines():
   c=json.loads(line)
   if c['role']=='proposal':inputs.append(dict(callId=c['phase']+'/'+c['callId'],system=c['system'],question=cases[c['caseId']]['question'],rawContent=c['rawContent'],complete=c['complete']))
 # Extract controls from immutable historical native input; no model response reused as a new proposal.
 original=json.loads((OLD/'results/core/native-input.json').read_text(encoding='utf-8'))
 inputs.extend(dict(c,callId='CONTROL/'+a.phase+'/'+c['callId'].removeprefix('CONTROL/')) for c in original if c['callId'].startswith('CONTROL/'))
 dest=R/('results/native-input-'+a.phase+'.json')
 if dest.exists():raise SystemExit('Input coordinate exists, preserve old replay')
 dest.write_bytes((json.dumps(inputs,ensure_ascii=False,indent=2)+'\n').encode())
 code=subprocess.run([sys.executable,'-X','utf8','-B',str(R/'native.py'),str(dest.relative_to(R)),a.output]).returncode
 if code:raise SystemExit(code)
 print('Completed native',len(inputs),'records; proposals and original controls',flush=True)
if __name__=='__main__':main()
