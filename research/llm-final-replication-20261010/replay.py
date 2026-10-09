"""New native witnesses using byte-identical historical helpers and identity views."""
import argparse,copy,importlib.util,json,os,pathlib,re,subprocess,sys
from collect import R,REPO,read,rows,write,check

def materialize(suite):
 m=read(R/'matrix.json');s=next(x for x in m['suites'] if x['id']==suite)
 summary=read(R/'results'/suite/'summary.json')
 assert summary['stop'] is None and summary['requests']==s['requests'],'Incomplete collection is not an evaluated complete suite'
 logical='layer3' if suite in ['formal','external','tier','time-day0','time-day1'] else 'counterexamples' if suite=='challenge' else 'query-day1' if suite=='query-review-day1' else 'query-day0' if suite=='query-review-day0' else suite
 view=R/'views'/logical;origin=REPO/'research'/s['sourceFolder'];view.mkdir(parents=True,exist_ok=True)
 for file in ['cases.json','external-cases.json','plan.json','challenge-plans.json','fixtures.json','preflight-labels.json']:
  if (origin/file).exists():
   target=view/file
   if target.exists():assert target.read_bytes()==(origin/file).read_bytes(),file
   else:target.write_bytes((origin/file).read_bytes())
 phase={'core':'core','extension':'core','counterexamples':'core','challenge':'challenge','formal':'formal','external':'external','tier':'tier','time-day0':'day0','time-day1':'day1'}.get(suite)
 path=view/'results'/phase if phase else view/'review-results' if 'review' in suite else view/'results'
 path.mkdir(parents=True,exist_ok=True);dest=path/'calls.jsonl'
 assert not dest.exists(),'Keep first identity view'
 projection=[]
 for x in rows(R/'results'/suite/'calls.jsonl'):
  y=copy.deepcopy(x);y.update(y.pop('sourceMetadata'));y['physicalCallId']=y['callId'];y['callId']=x['legacyCallId'];projection.append(y)
 dest.write_bytes((''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in projection)).encode())
 blocks={}
 for x in projection:
  if x['role']=='proposal' and '/p/' in x['callId']:
   block=x['callId'].split('/p/')[0];repeat=int(re.search(r'-r(\d+)$',block).group(1));blocks[block]=dict(block=block,caseId=x['caseId'],repeat=repeat,completed=True)
 if blocks:(path/'blocks.jsonl').write_bytes((''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in blocks.values())).encode())
 write(path/'collection-summary.json',dict(summary,callCount=summary['requests'],phase=phase,completedBlocks=len(blocks),plannedBlocks=len(blocks),identityQualification='Legacy callId is only an evaluator namespace; physicalCallId binds new attempts'))
 return s,view,path,projection

def native_run(inputs,out,query=False,fixtures=None):
 assert not out.exists(),'Keep first native witness';out.mkdir(parents=True);src=out/'input.json';write(src,inputs)
 env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17';env['RESEARCH_NATIVE_INPUT']=str(src)
 if query:env['QUERY_CONTROLS_FIXTURES']=str(fixtures)
 for system,folder,package in [('qingye','qingye/backend','cn/qingye'),('library','coursework/library-management-system/backend','cn/kmbeast')]:
  cls=('Qingye' if system=='qingye' else 'Library')+('QueryControlsReplayTest' if query else 'ResearchReplayTest')
  source=REPO/'research'/('llm-query-controls-20261008' if query else 'llm-core')/'native'/f'{cls}.java'
  backend=REPO/folder;helper=backend/f'src/test/java/{package}/{cls}.java'
  if helper.exists():assert helper.read_bytes()==source.read_bytes(),'Unknown helper copy'
  else:helper.write_bytes(source.read_bytes())
  env['RESEARCH_NATIVE_OUTPUT']=str(out/f'native-{system}.jsonl');env['RESEARCH_NATIVE_SNAPSHOT']=str(out/f'snapshot-{system}.json')
  method='nativeQueryControls' if query else 'nativeFrozenReplay'
  with (out/f'{system}.log').open('wb') as log:
   code=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#{method}','test'],cwd=backend,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  assert code==0,'Native failure retained: '+system
  print('NATIVE_PASS '+system+' '+str(out.relative_to(R)),flush=True)
 return len(inputs)

def original_controls():return [x for x in read(REPO/'research/llm-core/results/core/native-input.json') if x['callId'].startswith('CONTROL/')]
def main():
 p=argparse.ArgumentParser();p.add_argument('suite');a=p.parse_args();check()
 if a.suite=='controls':
  native_run(original_controls(),R/'offline/standard-controls')
  native_run(read(REPO/'research/llm-query-controls-20261008/diagnostics/preflight/input.json'),R/'offline/query-controls',True,REPO/'research/llm-query-controls-20261008/fixtures.json')
  native_run(read(REPO/'research/llm-core/history/native-input.json'),R/'offline/history-transfer')
  return
 s,view,path,projection=materialize(a.suite)
 if s['kind'] in ['pool_review','fixed_review']:return
 cases={x['id']:x for x in read(view/'cases.json')+(read(view/'external-cases.json') if (view/'external-cases.json').exists() else [])}
 inputs=[]
 if a.suite.startswith('query-'):
  for x in projection:
   c=cases[x['caseId']]
   for i,scenario in enumerate(c['scenarios']):inputs.append(dict(recordId=x['callId']+'/fixture/'+str(i),callId=x['callId'],physicalCallId=x['physicalCallId'],system=x['system'],question=c['question'],rawContent=x['rawContent'],complete=x['complete'],**scenario))
  native_run(inputs,path/'native',True,view/'fixtures.json')
 else:
  for x in projection:
   if x['role']=='proposal':inputs.append(dict(callId=(x['phase']+'/' if 'phase' in x else '')+x['callId'],physicalCallId=x['physicalCallId'],system=x['system'],question=cases[x['caseId']]['question'],rawContent=x['rawContent'],complete=x['complete']))
  inputs.extend(original_controls())
  if a.suite=='counterexamples':
   for c in read(view/'challenge-plans.json'):inputs.append(dict(callId='CHALLENGE/'+c['id'],system=c['system'],question=c['question'],rawContent=json.dumps(c['candidate'],ensure_ascii=False),complete=True))
  out=path/'native-v2' if a.suite in ['core','extension','counterexamples'] else view/'native'/a.suite
  native_run(inputs,out)
 if a.suite in ['formal','external','tier','time-day0','time-day1']:
  merged=view/'results/native-all';merged.mkdir(parents=True,exist_ok=True)
  for system in ['qingye','library']:
   seen={};
   for f in sorted((view/'native').glob('*/native-'+system+'.jsonl')):
    for n in rows(f):
     if n['callId'].startswith('CONTROL/'):continue
     assert n['callId'] not in seen;seen[n['callId']]=n
   target=merged/f'native-{system}.jsonl';target.write_bytes((''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in seen.values())).encode())
 print('NATIVE_SUITE_EXIT '+a.suite+' records='+str(len(inputs)),flush=True)
if __name__=='__main__':main()
