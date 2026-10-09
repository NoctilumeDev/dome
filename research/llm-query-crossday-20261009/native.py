"""Research-only H2 replay, separate helpers and fresh output coordinates."""
import argparse, os, subprocess, sys
from common import R, REPO, read, write, check

def input_record(call, case, scenario, label):
    return dict(recordId=label, callId=call['callId'], system=case['system'], question=case['question'], rawContent=call['rawContent'], complete=call['complete'], **scenario)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','observed']);a=p.parse_args()
    cases=read(R/'cases.json'); inputs=[]
    if a.mode=='observed':
        check(); calls=__import__('common').lines(R/'results/calls.jsonl'); by_case={c['id']:c for c in cases}
        for call in calls:
            c=by_case[call['caseId']]
            for index, scenario in enumerate(c['scenarios']):
                inputs.append(input_record(call,c,scenario,call['callId']+'/fixture/'+str(index)))
    else:
        for c in cases:
            call={'callId':'PREFLIGHT/'+c['id'],'rawContent':__import__('json').dumps(c['preflightPlan'],ensure_ascii=False),'complete':True}
            for index, scenario in enumerate(c['scenarios']): inputs.append(input_record(call,c,scenario,call['callId']+'/'+str(index)))
        for system in ['library','qingye']:
            c=next(c for c in cases if c['id']=='I01_'+system)
            for field,value in [('userId',102),('userName','张三')]:
                plan=dict(c['preflightPlan'],**{field:value});call={'callId':'CONTROL/'+system+'/extra-'+field,'rawContent':__import__('json').dumps(plan,ensure_ascii=False),'complete':True}
                inputs.append(input_record(call,c,c['scenarios'][0],call['callId']))
    dest=R/('diagnostics/preflight' if a.mode=='preflight' else 'results/native')
    if dest.exists(): raise SystemExit('Replay coordinate exists; preserve it')
    dest.mkdir(parents=True); src=dest/'input.json';write(src,inputs)
    env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17';env['QUERY_CONTROLS_FIXTURES']=str(R/'fixtures.json');env['RESEARCH_NATIVE_INPUT']=str(src)
    for system,folder,package,cls in [('library','coursework/library-management-system/backend','cn/kmbeast','LibraryQueryControlsReplayTest'),('qingye','qingye/backend','cn/qingye','QingyeQueryControlsReplayTest')]:
        backend=REPO/folder;copy=backend/f'src/test/java/{package}/{cls}.java';original=(R/f'native/{cls}.java').read_bytes()
        if copy.exists(): assert copy.read_bytes()==original,'Unknown helper copy: refuse overwrite'
        else: copy.write_bytes(original)
        env['RESEARCH_NATIVE_OUTPUT']=str(dest/f'native-{system}.jsonl');env['RESEARCH_NATIVE_SNAPSHOT']=str(dest/f'snapshot-{system}.json')
        with (dest/f'{system}.log').open('wb') as log:
            code=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#nativeQueryControls','test'],cwd=backend,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        if code: raise SystemExit('Native failure preserved: '+system)
        print(system+' native invariant replay PASS',flush=True)
    print('Replay records',len(inputs),flush=True)
if __name__=='__main__':main()
