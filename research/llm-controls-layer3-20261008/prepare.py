"""Prospective generator: no provider outputs inspected to choose formal cases."""
import hashlib,json,random
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'llm-core';R2=R.parent/'llm-counterexamples-20261008';REPO=R.parents[1]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def q(entity='相机',intent='EQUIPMENT',time='CURRENT'):
 return dict(action='QUERY',intent=intent,entity=entity,category=None,timeOption=time,reason=None)
def b(title='三体',intent='SEARCH_BOOK',**extra):
 return dict(action='QUERY',intent=intent,title=title,author=None,category=None,publisher=None,keywords=[],availableOnly=None,unreturnedOnly=None,timeOption='ALL',days=None,limit=20,reason=None)|extra
def decline(system,reason):
 return dict(q(None,None,None),action='CLARIFY',reason=reason) if system=='qingye' else dict(b(None,None),action='CLARIFY',reason=reason)
def main():
 if (R/'seal.json').exists():raise SystemExit('Frozen: no regeneration')
 families=['nested_negation','reference_binding','conditional_branch','cancel_retained','long_business_list','constraint_composition']
 cases=[]
 for stage in ('pilot','formal'):
  for system in ('qingye','library'):
   for fi,f in enumerate(families):
    for v in (range(1) if stage=='pilot' else range(2)):
     x,y=('手机','摄像机') if stage=='pilot' and system=='qingye' else ('馆藏3','馆藏4') if stage=='pilot' else ('相机','投影仪') if system=='qingye' else ('三体','Java入门')
     label='器材库存' if system=='qingye' else '馆藏搜索';verb='借用' if system=='qingye' else '借阅';my='我的全部借用记录' if system=='qingye' else '我的全部借阅记录'
     gold=q(x) if system=='qingye' else b(x)
     if f=='nested_negation':
      text=[f'不是不查{x}，是不查{y}；请查询前者的{label}。',f'我没有说“不要查询{x}”，不要查询的是{y}；本次只查{x}的{label}。'][v]
     elif f=='reference_binding':
      text=[f'甲设备是{x}，乙设备是{y}。乙先不查，只查甲的{label}。',f'第一项{x}，第二项{y}；我说的“它”明确指第一项。第二项是背景，请查它的{label}。'][v] if system=='qingye' else [f'甲书是《{x}》，乙书是《{y}》。乙先不查，只查甲的{label}。',f'第一项《{x}》，第二项《{y}》；“它”明确指第一项，第二项只是背景，请查它的{label}。'][v]
     elif f=='conditional_branch':
      text=[f'先查询{x}的{label}，若没有，再查询{y}的{label}；两个条件步骤都保留。',f'如果我{verb}过{x}就查它的{label}，否则查询{y}的{label}；目前我没有提供该条件的真假。'][v];gold=decline(system,'MULTIPLE_REQUESTS' if system=='qingye' else 'MULTIPLE_ACTIONS')
     elif f=='cancel_retained':
      text=[f'先查{x}的{label}，再查{my}。我撤销的只是“撤销第二项”这句话，不是第二个查询，两项查询仍然都保留。',f'先查{x}的{label}，再查{my}；第二项已经撤销，第一项未撤销，现在只执行第一项。'][v]
      if v==0:gold=decline(system,'MULTIPLE_REQUESTS' if system=='qingye' else 'MULTIPLE_ACTIONS')
     elif f=='long_business_list':
      entries=[f'{i:03d} 项：此前{verb}过{y}，这是历史，不执行。' for i in range(1,15)]
      active=f'015项：本次唯一保留的查询是{x}的{label}。'
      text='\n'.join(([active]+entries) if v==0 else (entries[:7]+[active]+entries[7:]))+'\n以上各项按“是否执行”解释，不按出现先后覆盖。'
     else:
      text=[f'请查{x}的{label}，并且只保留价格低于100元的结果；价格条件不能省。',f'请查我{verb}《{x}》的未归还记录，书名和未归还条件都保留。' if system=='library' else f'请查我{verb}{x}的未归还记录，器材和未归还条件都保留。'][v]
      gold=b(x,'MY_BORROWS',unreturnedOnly=True) if system=='library' and v==1 else decline(system,'UNSUPPORTED_FILTER')
     cases.append(dict(id=f'{system}-R3-{stage}-{fi+1:02}-{v+1}',system=system,family=f,variant=v+1,stage=stage,stratum='prospective_executor_labels',question=text,oracle={'allowed':[gold]},labelScope='executor rule-generated; no independent human labels'))
 write(R/'cases.json',cases)
 for name in ('qingye','library','review'):
  p=R/f'prompts/{name}.txt';p.parent.mkdir(exist_ok=True);p.write_bytes((OLD/f'prompts/{name}.txt').read_bytes())
 base=json.loads((R2/'plan.json').read_text());providers=base['providers']
 providers['ds_pro']=dict(providers['a'],model='deepseek-v4-pro',inputCnyPerMillion=9,outputCnyPerMillion=27)
 providers['q_flash']=dict(providers['b'],model='qwen-flash',inputCnyPerMillion=.15,outputCnyPerMillion=1.5)
 plan=dict(version='layer3-v1',parentSha='e3e4934a10b0284b3c7d4deb6c0eeb8a101fb082',productSha=base['baseSha'],seed=2026100803,clock=base['clock'],providers=providers,deadlineMs=5000,temperature=0,thinking='disabled',automaticRetries=0,maxTokens=base['maxTokens'],reviewMaxTokens=250,repetitions={'pilot':2,'formal':8,'external':3,'tier':3,'day0':3,'day1':3},newBudgetCny=7,hardCumulativePerProviderCny=20,priorConservativeCny={'deepseek':4.543270,'qwen':1.6633456},unknownReserveCny=.05,priceSources=['https://api-docs.deepseek.com/zh-cn/quick_start/pricing/','https://help.aliyun.com/zh/model-studio/qwen-plus','https://help.aliyun.com/zh/model-studio/qwen-flash'],priceAsOf='2026-10-08',human='PENDING_HUMAN_STUDY')
 write(R/'plan.json',plan);print('Generated 12 pilot +24 disjoint formal questions; all six mechanisms included')
if __name__=='__main__':main()
