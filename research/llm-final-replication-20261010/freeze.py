"""Seal new adapters and all original source assets before paid collection."""
import ast,hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent;REPO=R.parents[1]
def main():
 assert not (R/'seal.json').exists(),'Do not replace a frozen candidate'
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0')
 inputs={};runtime={}
 for n in tracked:
  if not n:continue
  if n.startswith('research/') or n.startswith('qingye/') or n.startswith('coursework/library-management-system/'):
   p=REPO/n
   if p.exists():inputs[n]=hashlib.sha256(p.read_bytes()).hexdigest()
   if n.endswith(('.java','.py','.txt','.xml','.json')) and not any(x in n for x in ['/results/','/output','/history/','/diagnostics/','/docs/','/sources/']):
    if p.exists() and p.stat().st_size<150000:runtime[n]=inputs[n]
 for p in R.rglob('*'):
  if p.is_file() and not any(x in p.parts for x in ['results','offline','scoring']):
   n=p.relative_to(REPO).as_posix();inputs[n]=hashlib.sha256(p.read_bytes()).hexdigest()
   if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'),filename=n)
   if p.name not in ['jobs.jsonl']:runtime[n]=inputs[n]
 seal=dict(version='final-replication-seal-v1',sourceSha='d5fecb05cda3c0a443cbfd5020059a096e98ff23',inputs=inputs,runtime=runtime,paidRequestsBeforeSeal=0)
 (R/'seal.json').write_bytes((json.dumps(seal,ensure_ascii=False,indent=2)+'\n').encode())
 print(json.dumps({'status':'SEALED','files':len(inputs),'runtimeFiles':len(runtime),'paidRequests':0}))
if __name__=='__main__':main()
