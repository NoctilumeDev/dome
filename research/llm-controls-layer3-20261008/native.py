"""Replay exact frozen production helpers to a new, non-overwriting coordinate."""
import argparse,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core';REPO=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');args=p.parse_args()
 src=R/args.input;out=R/args.output
 if out.exists():raise SystemExit('Output already exists: preserve first replay')
 out.mkdir(parents=True);env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17'
 for system,folder,package,cls in [('qingye','qingye/backend','cn/qingye','QingyeResearchReplayTest'),('library','coursework/library-management-system/backend','cn/kmbeast','LibraryResearchReplayTest')]:
  backend=REPO/folder;helper=backend/f'src/test/java/{package}/{cls}.java';original=(OLD/f'native/{cls}.java').read_bytes()
  if helper.exists():assert helper.read_bytes()==original,'Unknown helper: refuse overwrite'
  else:helper.write_bytes(original)
  env.update(RESEARCH_NATIVE_INPUT=str(src),RESEARCH_NATIVE_OUTPUT=str(out/f'native-{system}.jsonl'),RESEARCH_NATIVE_SNAPSHOT=str(out/f'snapshot-{system}.json'))
  with (out/f'native-{system}.txt').open('wb') as f:
   code=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#nativeFrozenReplay','test'],cwd=backend,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
  if code:raise SystemExit('Native failure retained: '+system)
  print('Native PASS: '+system,flush=True)
if __name__=='__main__':main()
