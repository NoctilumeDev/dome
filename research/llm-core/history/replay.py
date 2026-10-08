"""Transfer retained historical inputs/plans to current native read-only helpers."""
import os,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent;REPO=R.parents[1]
env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17'
for system,folder,package,cls in [('qingye','qingye/backend','cn/qingye','QingyeResearchReplayTest'),('library','coursework/library-management-system/backend','cn/kmbeast','LibraryResearchReplayTest')]:
 backend=REPO/folder;helper=backend/f'src/test/java/{package}/{cls}.java';shutil.copyfile(R/f'native/{cls}.java',helper)
 env.update(RESEARCH_NATIVE_INPUT=str(H/'native-input.json'),RESEARCH_NATIVE_OUTPUT=str(H/f'native-{system}.jsonl'),RESEARCH_NATIVE_SNAPSHOT=str(H/f'snapshot-{system}.json'))
 with (H/f'native-{system}.txt').open('wb') as f:
  result=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#nativeFrozenReplay','test'],cwd=backend,env=env,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(f'Historical native transfer failed: {system}')
 print(f'Historical transfer {system}: PASS',flush=True)
