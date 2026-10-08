import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1];OLD=R.parent/'llm-core'
if (R/'frozen-core-v2.json').exists():raise SystemExit('Frozen layer exists')
assert not subprocess.check_output(['git','diff','--name-only','60cd5d4','--','research/llm-core','qingye/backend/src/main','coursework/library-management-system/backend/src/main'],cwd=REPO)
files=['prepare.py','run.py','challenge.py','freeze.py','replay.py','evaluate.py','analysis.py','stats.py','verify.py','tests/test_stats.py','CONTRACT.md','cases.json','challenge-plans.json','plan.json','prompts/qingye.txt','prompts/library.txt','prompts/review.txt','../llm-core/core.py','../llm-core/run.py','../llm-core/analyze.py','../llm-core/prepare_native.py','../llm-core/native/QingyeResearchReplayTest.java','../llm-core/native/LibraryResearchReplayTest.java']
prior=json.loads((OLD/'frozen-core-v2.json').read_text())
manifest=dict(parentSha='60cd5d4ea1fed388609170fe5b72136c49edfab1',research={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in files},production={n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in prior['production']})
(R/'frozen-core-v2.json').write_bytes(json.dumps(manifest,indent=2).encode());print('Frozen research:',len(files),'product:',len(manifest['production']))
