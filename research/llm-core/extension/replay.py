"""Reuse frozen native helpers in a separate, sequential extension environment."""
import os,shutil,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent;R=E.parent;REPO=R.parents[1]
sys.path.insert(0,str(R))
import prepare_native
prepare_native.ROOT=E
sys.argv=['prepare_native','core'];prepare_native.main()
out=E/'results/core/native-v2';out.mkdir(exist_ok=True)
env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17'
for system,folder,package,cls in [('qingye','qingye/backend','cn/qingye','QingyeResearchReplayTest'),('library','coursework/library-management-system/backend','cn/kmbeast','LibraryResearchReplayTest')]:
 backend=REPO/folder;helper=backend/f'src/test/java/{package}/{cls}.java'
 shutil.copyfile(R/f'native/{cls}.java',helper)
 env.update(RESEARCH_NATIVE_INPUT=str(E/'results/core/native-input.json'),RESEARCH_NATIVE_OUTPUT=str(out/f'native-{system}.jsonl'),RESEARCH_NATIVE_SNAPSHOT=str(out/f'snapshot-{system}.json'))
 with (out/f'native-{system}.txt').open('wb') as f:
  result=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#nativeFrozenReplay','test'],cwd=backend,env=env,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(f'Native extension failed: {system}; retained log')
 print(f'Native extension {system}: PASS',flush=True)
