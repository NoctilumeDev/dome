"""One paid first window; stop at actual day1 boundary, never invent a wait."""
import getpass,json,subprocess,sys,warnings
import collect
from collect import R,read,write,check
def run(script,arg):
 code=subprocess.run([sys.executable,'-X','utf8','-B',str(R/script),arg]).returncode
 if code:raise RuntimeError(script+' failed in '+arg)
def main():
 sys.stdout.reconfigure(encoding='utf-8');check()
 if not sys.stdin.isatty():raise SystemExit('Non-echo console required')
 warnings.simplefilter('error',getpass.GetPassWarning)
 text=getpass.getpass('CREDENTIAL_INPUT: ');keys=json.loads(text);assert set(keys)=={'deepseek','qwen'}
 getpass.getpass=lambda _:text
 completed=[];stop=None
 try:
  if not (R/'offline/standard-controls').exists():run('replay.py','controls')
  for suite in read(R/'matrix.json')['suites']:
   name=suite['id']
   if suite['guardAfterFinishedSuite']:
    stop='WAIT_FOR_NEW_24H_WINDOW';break
   if (R/'results'/name).exists():raise RuntimeError('Existing suite: no implicit second execution')
   sys.argv=['collect',name];collect.main()
   run('replay.py',name);run('score.py',name);completed.append(name)
 except BaseException as e:
  stop=type(e).__name__+': '+str(e);print('PIPELINE_STOP='+stop,flush=True)
 finally:
  keys.clear();text='';getpass.getpass=lambda _:(_ for _ in ()).throw(RuntimeError('Credentials cleared'))
  write(R/'WINDOW_STATUS.json',dict(completedSuites=completed,stop=stop,credentialsCleared=True,fullMatrixComplete=False,human='PENDING_HUMAN_STUDY'))
 print('PIPELINE_EXIT='+json.dumps({'completedSuites':completed,'stop':stop,'credentialsCleared':True}),flush=True)
 if stop!='WAIT_FOR_NEW_24H_WINDOW':raise SystemExit(2)
if __name__=='__main__':main()
