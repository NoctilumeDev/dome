"""Read-only qualification; never repair input, evidence or product."""
import hashlib,json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'llm-core'))
from core import parse_plan,score_plan,digest
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def main():
 seal=json.loads((R/'seal.json').read_text(encoding='utf-8'))
 for n,h in seal['research'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,'Research changed '+n
 for n,h in seal['product'].items():assert hashlib.sha256((R.parents[1]/n).read_bytes()).hexdigest()==h,'Product changed '+n
 for n,h in seal['immutableImportedTools'].items():assert hashlib.sha256((R.parents[1]/n).read_bytes()).hexdigest()==h,'Imported tool changed '+n
 plan=json.loads((R/'plan.json').read_text());expected={'pilot':48,'formal':2304,'external':96,'tier':144,'day0':72};allcalls=[]
 for phase,count in expected.items():
  rr=lines(R/f'results/{phase}/calls.jsonl');jj=lines(R/f'results/{phase}/request-journal.jsonl');summary=json.loads((R/f'results/{phase}/summary.json').read_text());assert len(rr)==count and len({r['callId'] for r in rr})==count
  assert set(r['callId'] for r in rr)==set(r['callId'] for r in jj) and summary['stop'] is None
  assert summary['completedBlocks']==summary['plannedBlocks'];allcalls+=rr
  journal={j['callId']:j for j in jj}
  for r in rr:
   assert r['estimatedCostCny'] is None or r['estimatedCostCny']>=0
   assert r['requestHash']==journal[r['callId']]['requestHash']==digest(r['request'])
   choices=r.get('response',{}).get('choices',[])
   assert r['rawContent']==(choices[0].get('message',{}).get('content','') if choices else '')
   assert r['complete']==(bool(choices) and choices[0].get('finish_reason')=='stop' and r['transport']=='SUCCESS')
 natives={r['callId']:r for s in ('qingye','library') for r in lines(R/f'results/native-all/native-{s}.jsonl')}
 proposals=[r for r in allcalls if r['role']=='proposal'];assert len(natives)==len(proposals)+10;assert all(r['databaseUnchanged'] for r in natives.values())
 for system in ('qingye','library'):
  assert natives[f'CONTROL/all/{system}/positive']['response']['status']=='QUERY'
  for variant in ('foreign-user','missing-field','transport'):assert natives[f'CONTROL/all/{system}/{variant}']['response']['status']!='QUERY'
  private=natives[f'CONTROL/all/{system}/omitted-private-filter'];assert private['response']['status']=='CONFIRM_SCOPE'
  if system=='library':assert private['repositoryQueriesBeforeConfirm']==0
  else:assert not any('FROM loan ' in q for q in private['askSql'])
 m=json.loads((R/'output/metrics.json').read_text());assert m['risk']['blocks']==192 and m['risk']['questions']==24 and m['risk']['families']==6
 cases={c['id']:c for c in json.loads((R/'cases.json').read_text())+json.loads((R/'external-cases.json').read_text())};details=json.loads((R/'output/proposal-ledger.json').read_text());assert len(details)==len(proposals)
 replay=json.loads((R/'results/native-input-all.json').read_text());source={n['callId']:n for n in replay};assert len(source)==len(replay)==len(natives) and set(source)==set(natives)
 by={d['phase']+'/'+d['callId']:d for d in details}
 for r in proposals:
  n=source[r['phase']+'/'+r['callId']]
  assert n['rawContent']==r['rawContent'] and n['complete']==r['complete'] and n['question']==cases[r['caseId']]['question'] and n['system']==r['system']
  p,fmt=parse_plan(r['system'],r['rawContent']);p=p if r['complete'] else None;match=p is not None and score_plan(p,cases[r['caseId']]['oracle'])['proposal_correct'];assert by[r['phase']+'/'+r['callId']]['match']==match
 for c in m['costs']:assert c['cumulativeConservative']<=20
 assert sum(c['knownEstimate']+c['reserve'] for c in m['costs'])<=7
 # Check full token-shaped values, not prefix literals in the scanner itself.
 secret=re.compile(rb'(?:sk-[a-z0-9]{32,}|sk-ws-[A-Za-z0-9._-]{24,}|Bearer\s+sk-[A-Za-z0-9_.-]{12,})')
 for p in R.rglob('*'):
  if p.is_file() and p.suffix in ('.py','.json','.jsonl','.md','.csv','.txt','.html'):
   assert not secret.search(p.read_bytes()),'Credential residue '+str(p)
 print('VERIFY PASS:',len(allcalls),'requests;',len(natives),'native records; source/freeze/oracles/controls/budget/no-secret residues')
if __name__=='__main__':main()
