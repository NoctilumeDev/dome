"""External provenance and prespecified compatible adaptation, never hidden relabeling."""
import argparse,hashlib,json,sys
from pathlib import Path
from prepare import R,write,b
def main():
 if (R/'seal.json').exists():raise SystemExit('Frozen: refuse generation')
 p=argparse.ArgumentParser();p.add_argument('source');a=p.parse_args();src=Path(a.source)
 assert hashlib.sha256(src.read_bytes()).hexdigest()=='5033c54318d5221a2532bc7c7388245e14ce1979ae9c79e928d4e21ec245c860'
 allrows=json.loads(src.read_text(encoding='utf-8'));by={r['question_id']:r for r in allrows};old=json.loads((R.parent/'llm-counterexamples-20261008/cases.json').read_text())
 cases=[]
 for i,c in enumerate([c for c in old if c['stratum']=='external_verbatim_capability_boundary']):
  s=by[c['sourceId']]
  cases.append(dict(id='R3-boundary-'+s['question_id'],stage='external',system='library',family='external_original_boundary',variant=i+1,question=s['question'],oracle={'allowed':[{'action':'CLARIFY'}]},stratum='external_original_boundary',sourceId=s['question_id'],sourceQuestion=s['question'],sourceSql=s['query'],mapping='Original unchanged. Unsupported SQL capability. Final entry label fixed by pre-model native reachability.',labelScope='executor capability mapping, not independent semantic oracle'))
  title=('Java入门','三体')[i%2]
  # Explicit operation substitution: preserve a request-list construction, replace unsupported source predicate.
  text=[f'给出书名包含“{title}”的馆藏图书及其分类。',f'哪些馆藏图书的书名包含“{title}”？只按该书名条件搜索。',f'在馆藏图书中，给出书名包含“{title}”的图书。',f'找到书名包含“{title}”的馆藏图书并给出书名。'][i%4]
  cases.append(dict(id='R3-adapted-'+s['question_id'],stage='external',system='library',family='external_adapted_literal_search',variant=i+1,question=text,oracle={'allowed':[b(title)]},stratum='external_adapted_compatible',sourceId=s['question_id'],sourceQuestion=s['question'],sourceSql=s['query'],mapping={'operations':['replace source database with local catalog','replace unsupported numeric/group/set predicate with supported literal title-contains predicate','replace output projection with fixed book renderer'],'insertedTitle':title,'removedOriginalConstraintsAreExplicit':True},labelScope='author-adapted source construction; not external original benchmark or independent generalization'))
 write(R/'external-cases.json',cases)
 write(R/'external-provenance.json',dict(source='DuSQL development / 教材辅助参考书',url='https://dataset-bj.cdn.bcebos.com/qianyan/DuSQL.zip',paper='https://aclanthology.org/2020.emnlp-main.562/',originalDataSha256=hashlib.sha256(src.read_bytes()).hexdigest(),originalBoundaryCount=8,adaptedCompatibleCount=8,unadaptedCompatibleClaim='NOT_ESTABLISHED',licenseBoundary='Research source retained in old local cache; full corpus not redistributed. Tiny cited excerpts only.',blindLabels=False))
 inputs=[]
 for c in json.loads((R/'cases.json').read_text())+cases:
  gold=c['oracle']['allowed'][0]
  if 'intent' not in gold:gold=dict(b(None,None),action='CLARIFY',reason='UNSUPPORTED_FILTER')
  inputs.append(dict(callId='PREFLIGHT/'+c['id'],system=c['system'],question=c['question'],rawContent=json.dumps(gold,ensure_ascii=False),complete=True))
 write(R/'diagnostics/preflight-input.json',inputs)
 print('External: 8 unchanged boundary +8 visibly adapted compatible; 52 pre-model entry checks')
if __name__=='__main__':main()
