"""Finish only the three predeclared day1 suites after all fresh 24h guards."""
import getpass
import json
import subprocess
import sys
import warnings
from collect import R, check, read, stage_guard, write
import collect

def run(script, suite):
    code=subprocess.run([sys.executable,'-X','utf8','-B',str(R/script),suite]).returncode
    if code:
        raise RuntimeError(script+' failed in '+suite)

def main():
    sys.stdout.reconfigure(encoding='utf-8');check()
    first=read(R/'WINDOW_STATUS.json')
    assert first['stop']=='WAIT_FOR_NEW_24H_WINDOW' and first['credentialsCleared']
    matrix=read(R/'matrix.json');suites=[x for x in matrix['suites'] if x['guardAfterFinishedSuite']]
    assert [x['id'] for x in suites]==['time-day1','query-day1','query-review-day1']
    assert sum(x['requests'] for x in suites)==774
    assert first['completedSuites']==[x['id'] for x in matrix['suites'] if not x['guardAfterFinishedSuite']]
    for suite in suites:
        stage_guard(suite)
        assert not (R/'results'/suite['id']).exists(),'Prior attempt is retained; no implicit resubmission'
    adapter=read(R/'second-window-adapter-seal.json')
    import hashlib
    for name,digest in adapter['files'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'Second-window adapter changed: '+name
    if not sys.stdin.isatty():
        raise SystemExit('Non-echo console required')
    warnings.simplefilter('error',getpass.GetPassWarning)
    text=getpass.getpass('CREDENTIAL_INPUT: ');keys=json.loads(text)
    assert set(keys)=={'deepseek','qwen'}
    getpass.getpass=lambda _:text
    completed=[];stop=None
    try:
        for suite in suites:
            name=suite['id'];sys.argv=['collect',name];collect.main()
            run('replay.py',name);run('score.py',name);completed.append(name)
    except BaseException as e:
        stop=type(e).__name__+': '+str(e);print('SECOND_WINDOW_STOP='+stop,flush=True)
    finally:
        keys.clear();text='';getpass.getpass=lambda _:(_ for _ in ()).throw(RuntimeError('Credentials cleared'))
        write(R/'SECOND_WINDOW_STATUS.json',dict(completedSuites=completed,stop=stop,credentialsCleared=True,
            fullMatrixComplete=stop is None and len(completed)==3,human='PENDING_HUMAN_STUDY'))
    print('SECOND_WINDOW_EXIT='+json.dumps(dict(completedSuites=completed,stop=stop,credentialsCleared=True)),flush=True)
    if stop is not None:
        raise SystemExit(2)

if __name__=='__main__':main()
