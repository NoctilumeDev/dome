"""Build a prospective counterexample layer before observing any new provider output."""
import hashlib,json,random
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core';REPO=R.parents[1]
def write(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def qplan(intent='EQUIPMENT',entity='投影仪',time='CURRENT'):
 return dict(action='QUERY',intent=intent,entity=entity,category=None,timeOption=time,reason=None)
def bplan(intent='FIND_LOCATION',title='Java入门',**args):
 return dict(action='QUERY',intent=intent,title=title,author=None,category=None,publisher=None,keywords=[],availableOnly=None,unreturnedOnly=None,timeOption='ALL',days=None,limit=20,reason=None,**{})|args
def main():
 if (R/'frozen.json').exists():raise SystemExit('Already frozen; no regeneration')
 families=[
 ('current_scope',[['我前天借用过相机，那只是背景；这次请求是投影仪当前库存。','之前的相机借用不查，本次请查询投影仪现在的库存。'],['我前天借阅过《三体》，那只是背景；这次请求是《Java入门》的馆藏位置。','之前的《三体》借阅不查，本次请查询《Java入门》在馆内的位置。']]),
 ('exclusion',[['相机和手机都排除，本次唯一目标为投影仪当前库存。','要查询的是投影仪的当前库存；相机、手机不是我的查询对象。'],['《三体》的位置排除，本次唯一目标为《Java入门》的馆藏位置。','要查询的是《Java入门》的馆藏位置；《三体》不是我的查询对象。']]),
 ('quotation',[['我举一个历史例句：“帮我查相机”。这个例句不执行；实际请求为投影仪当前库存。','“我借了相机”只是转述。请执行的唯一查询是投影仪现在的库存。'],['我举一个历史例句：“帮我查三体”。这个例句不执行；实际请求为《Java入门》的馆藏位置。','“我借了三体”只是转述。请执行的唯一查询是《Java入门》的馆藏位置。']]),
 ('field_list',[['器材备注：相机=此前借用；手机=背景；投影仪=本次唯一查询，当前库存。','记录字段如下：过去借用相机；当前目标投影仪；执行内容查询当前库存。'],['图书备注：三体=此前借阅；Java入门=本次唯一查询，馆藏位置。','记录字段如下：过去借阅三体；当前目标Java入门；执行内容查询馆藏位置。']]),
 ('retained_actions',[['先查投影仪当前库存，然后查我的全部借用记录；两件事都保留。','投影仪库存与我的全部报名记录均需查询，不是改口。'],['先查《Java入门》的馆藏位置，然后查我的全部借阅记录；两件事都保留。','《Java入门》的馆藏位置与我的全部反馈均需查询，不是改口。']]),
 ('private_constraints',[['请查询我借用相机的未归还记录，器材和归还状态都不能省。','仅查询今天我借用的相机记录，日期和器材都不能省。'],['请查询我借阅《三体》的未归还记录，书名和归还状态都不能省。','仅查询今天我借阅的《三体》记录，日期和书名都不能省。']])]
 cases=[]
 for fi,(family,questions) in enumerate(families,1):
  for si,system in enumerate(('qingye','library')):
   for vi,question in enumerate(questions[si],1):
    gold=qplan() if system=='qingye' else bplan()
    if family=='retained_actions' or family=='private_constraints':
     gold={'action':'CLARIFY'}
     if family=='private_constraints' and system=='library' and vi==1:gold=bplan('MY_BORROWS','三体',unreturnedOnly=True)
    cases.append(dict(id=f'{system}-R2-{fi:02}-{vi}',system=system,family=family,variant=vi,question=question,oracle={'allowed':[gold]},stratum='prospective_executor_labels',labelScope='current finite contract, not independent human labeling'))
 # Selection is determined from published SQL/domain, before model calls; no post-outcome filtering.
 source=json.loads((R/'sources/DuSQL-dev.json').read_text(encoding='utf-8'))
 eligible=[x for x in source if x['db_id']=='教材辅助参考书' and any(t in x['query'].lower() for t in ('适用年级','价格','group by','order by','union','intersect','except'))]
 sampled=random.Random(2026100802).sample(sorted(eligible,key=lambda x:x['question_id']),8)
 for x in sampled:
  cases.append(dict(id='library-DuSQL-'+x['question_id'],system='library',family='external_unsupported_sql',variant=1,question=x['question'],oracle={'allowed':[{'action':'CLARIFY'}]},stratum='external_verbatim_capability_boundary',sourceId=x['question_id'],sourceDb=x['db_id'],sourceQuery=x['query'],labelScope='external original question/SQL; executable-plan label mapped by executor because original SQL needs unsupported fields/operators; not independent human blind label'))
 write(R/'cases.json',cases)
 challenges=[]
 for system in ('qingye','library'):
  for family in ('current_scope','retained_actions','private_constraints','exclusion'):
   c=next(x for x in cases if x['system']==system and x['family']==family and x['variant']==1)
   gold=c['oracle']['allowed'][0]
   if gold['action']=='CLARIFY':
    gold=(dict(qplan(),action='CLARIFY',intent=None,entity=None,timeOption=None,reason='MULTIPLE_REQUESTS' if family=='retained_actions' else 'UNSUPPORTED_FILTER') if system=='qingye' else bplan(None,None,action='CLARIFY',reason='MULTIPLE_ACTIONS'))
   bad=qplan(entity='相机') if system=='qingye' else bplan(title='三体')
   if family=='retained_actions':bad=qplan() if system=='qingye' else bplan()
   if family=='private_constraints':bad=qplan('MY_LOANS',None,'ANY') if system=='qingye' else bplan('MY_BORROWS',None)
   for label,plan in [('correct',gold),('wrong',bad)]:challenges.append(dict(id=c['id']+'/'+label,caseId=c['id'],system=system,question=c['question'],candidate=plan,injectedLabel=label,source='synthetic predeclared identical PA=PB; not natural model agreement'))
 write(R/'challenge-plans.json',challenges)
 (R/'prompts').mkdir(exist_ok=True)
 for n in ('qingye','library','review'):(R/f'prompts/{n}.txt').write_bytes((OLD/f'prompts/{n}.txt').read_bytes())
 p=json.loads((OLD/'plan.json').read_text(encoding='utf-8'))
 p.update(version='counterexample-layer-v1',parentSha='60cd5d4ea1fed388609170fe5b72136c49edfab1',seed=2026100802,repetitions=4,coreBlocks=128,coreMaximumCalls=1536,challengeRepetitions=3,challengeMaximumCalls=96,pilotFamilies=[],oraclesAreIndependentHumanLabels=False,budgetCny=6.0,priorEstimatedCny={'deepseek':2.716516,'qwen':0.999630},priorUnknownReserveCny=0.01,hardCumulativePerProviderCny=20)
 p['inputHashes']={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ('cases.json','challenge-plans.json','CONTRACT.md','prompts/qingye.txt','prompts/library.txt','prompts/review.txt')}
 write(R/'plan.json',p)
 print('Prepared:',len(cases),'questions / 4 repeats; 24 author-labelled + 8 external capability boundaries; 16 fixed challenge plans')
if __name__=='__main__':main()
