"""Before paid calls: adjudicate deterministic entry reachability and bind exact bytes."""
import hashlib,json,subprocess
from pathlib import Path
from prepare import R,write
def main():
 if (R/'seal.json').exists():raise SystemExit('Already sealed')
 records={n['callId']:n for s in ('qingye','library') for n in [json.loads(x) for x in (R/f'diagnostics/native-preflight/native-{s}.jsonl').read_text().splitlines()]}
 cases=json.loads((R/'cases.json').read_text());external=json.loads((R/'external-cases.json').read_text());labels=[]
 for c in cases+external:
  n=records['PREFLIGHT/'+c['id']];reachable=n['nativePlannerCalled'];status=n['response']['status']
  if c['stage']!='external':assert reachable and n['nativeQualified'],'Generator fails entry/contract before paid calls: '+c['id']
  elif c['stratum']=='external_adapted_compatible':assert reachable and status=='QUERY' and n['nativeQualified'],'Adaptation not expressible'
  else:c['oracle']={'allowed':[{'action':'CLARIFY' if reachable else 'REJECT'}]};c['expectedNativeEntry']=reachable
  labels.append(dict(caseId=c['id'],reachable=reachable,statusWithFrozenCandidate=status,nativeQualified=n['nativeQualified'],oracleAction=c['oracle']['allowed'][0]['action'],scope='pre-model deterministic replay; not independent human review'))
 # This is before any API call; retain initial stub results and explicit label reconciliation.
 write(R/'external-cases.json',external);write(R/'diagnostics/pre-model-label-review.json',labels)
 parent_product=json.loads((R.parent/'llm-counterexamples-20261008/frozen-core-v2.json').read_text())['production'];product={}
 for n,h in parent_product.items():
  data=(R.parents[1]/n).read_bytes()
  normalized=data if hashlib.sha256(data).hexdigest()==h else data.replace(b'\r\n',b'\n')
  assert hashlib.sha256(normalized).hexdigest()==h,'Parent source content differs '+n
  git_data=subprocess.check_output(['git','show','e3e4934:'+n],cwd=R.parents[1])
  assert git_data==normalized,'Git source differs '+n
  product[n]=hashlib.sha256(data).hexdigest()
 names=['CONTRACT.md','prepare.py','adapt.py','collect.py','native.py','freeze.py','measure.py','tests/test_measure.py','plan.json','cases.json','external-cases.json','external-provenance.json','prompts/qingye.txt','prompts/library.txt','prompts/review.txt']
 research={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in names}
 tools={f'research/llm-core/{n}':hashlib.sha256((R.parent/f'llm-core/{n}').read_bytes()).hexdigest() for n in ('run.py','core.py','analyze.py','prepare_native.py','native/QingyeResearchReplayTest.java','native/LibraryResearchReplayTest.java')}
 write(R/'seal.json',dict(parentSha='e3e4934a10b0284b3c7d4deb6c0eeb8a101fb082',research=research,product=product,parentLfSource=parent_product,immutableImportedTools=tools,preflight='diagnostics/pre-model-label-review.json',callsObservedAtSeal=0,lineEndingBoundary='Parent Git content exact after CRLF-to-LF only; local runtime bytes separately bound. No source edits.'))
 print('Seal created:',len(product),'product files;',len(research),'research files; all prospective cases reachable')
if __name__=='__main__':main()
