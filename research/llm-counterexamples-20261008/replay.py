"""Same native helper, fixed H2 source; new outputs only."""
import os,shutil,subprocess,sys,json
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core';REPO=R.parents[1]
sys.path.insert(0,str(OLD));import prepare_native
prepare_native.ROOT=R;sys.argv=['prepare_native','core'];prepare_native.main()
inputs=json.loads((R/'results/core/native-input.json').read_text())
for c in json.loads((R/'challenge-plans.json').read_text()):inputs.append(dict(callId='CHALLENGE/'+c['id'],system=c['system'],question=c['question'],rawContent=json.dumps(c['candidate'],ensure_ascii=False),complete=True))
(R/'results/core/native-input.json').write_bytes(json.dumps(inputs,ensure_ascii=False,indent=2).encode())
out=R/'results/core/native-v2';out.mkdir(exist_ok=True)
env=os.environ.copy();env['JAVA_HOME']='D:/IDEA/JDK17'
for system,folder,package,cls in [('qingye','qingye/backend','cn/qingye','QingyeResearchReplayTest'),('library','coursework/library-management-system/backend','cn/kmbeast','LibraryResearchReplayTest')]:
 backend=REPO/folder;helper=backend/f'src/test/java/{package}/{cls}.java';assert not helper.exists(),'Do not overwrite user helper'
 shutil.copyfile(OLD/f'native/{cls}.java',helper)
 env.update(RESEARCH_NATIVE_INPUT=str(R/'results/core/native-input.json'),RESEARCH_NATIVE_OUTPUT=str(out/f'native-{system}.jsonl'),RESEARCH_NATIVE_SNAPSHOT=str(out/f'snapshot-{system}.json'))
 with (out/f'native-{system}.txt').open('wb') as f:result=subprocess.run(['D:/Maven/apache-maven-3.9.11-bin/apache-maven-3.9.11/bin/mvn.cmd','-B','-ntp',f'-Dtest={cls}#nativeFrozenReplay','test'],cwd=backend,env=env,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit('Native failure retained: '+system)
 print('Native PASS:',system,flush=True)
