import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
def main():
 files=[p for p in ROOT.rglob('*') if p.is_file() and p.suffix in ('.py','.ps1','.java','.json','.txt','.md') and 'results' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts and p.name!='frozen-core.json']
 production=subprocess.check_output(['git','-C',str(REPO),'ls-files','qingye/backend/src/main','coursework/library-management-system/backend/src/main'],text=True).splitlines()
 manifest={'baseSha':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),'research':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},'production':{name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in production},'preflight':'8 blocks, 96 calls; component HTTP success is separate from native qualification; collector console first failure retained','formalBudgetCny':10,'budgetRationale':'bounded user-authorized experiment; pilot extrapolation about CNY 2.5, conservative local hard ceiling CNY 10 unless user sets a lower cap'}
 path=ROOT/'frozen-core.json'
 if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==manifest,'Frozen manifest differs'
 else:path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Frozen research files:',len(files),'production files:',len(production))
if __name__=='__main__':main()
