"""Paired actual-time readback; preserve day0 and all earlier derived evidence."""
import hashlib,json,statistics,sys
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'llm-core'))
from core import parse_plan,score_plan,digest
from collect import check

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def write(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())

def main():
 check();out=R/'output-day1'
 if out.exists():raise SystemExit('Preserve existing cross-day output; do not overwrite')
 s0=read(R/'results/day0/summary.json');s1=read(R/'results/day1/summary.json')
 start=datetime.fromisoformat(s1['startedAt']);finish=datetime.fromisoformat(s0['finishedAt'])
 assert (start-finish).total_seconds()>=86400
 shanghai=timezone(timedelta(hours=8))
 assert start.astimezone(shanghai).date()>finish.astimezone(shanghai).date()
 raw={phase:lines(R/f'results/{phase}/calls.jsonl') for phase in ('day0','day1')}
 for phase,s in [('day0',s0),('day1',s1)]:
  assert s['stop'] is None and s['requestIdentities']==72 and len(raw[phase])==72
  assert s['completedBlocks']==s['plannedBlocks']==36
  assert len({c['callId'] for c in raw[phase]})==72
  assert {c['callId'] for c in raw[phase]}=={j['callId'] for j in lines(R/f'results/{phase}/request-journal.jsonl')}
 native={phase:{n['callId']:n for system in ('qingye','library') for n in lines(R/f'results/{folder}/native-{system}.jsonl')} for phase,folder in [('day0','native-all'),('day1','native-day1')]}
 assert len(native['day1'])==82 and all(n['databaseUnchanged'] for n in native['day1'].values())
 for system in ('qingye','library'):
  n=native['day1'];assert n[f'CONTROL/day1/{system}/positive']['response']['status']=='QUERY'
  for v in ('foreign-user','missing-field','transport'):assert n[f'CONTROL/day1/{system}/{v}']['response']['status']!='QUERY'
  private=n[f'CONTROL/day1/{system}/omitted-private-filter'];assert private['response']['status']=='CONFIRM_SCOPE'
  if system=='library':assert private['repositoryQueriesBeforeConfirm']==0
  else:assert not any('FROM loan ' in q for q in private['askSql'])
  assert (R/f'results/native-all/snapshot-{system}.json').read_bytes()==(R/f'results/native-day1/snapshot-{system}.json').read_bytes()
 cases={c['id']:c for c in read(R/'cases.json')};a={c['callId']:c for c in raw['day0']};paired=[]
 for c1 in raw['day1']:
  c0=a[c1['callId']]
  assert c0['requestHash']==c1['requestHash']==digest(c0['request'])==digest(c1['request'])
  assert c0['requestedModel']==c1['requestedModel'] and c0['caseId']==c1['caseId']
  entry=dict(callId=c1['callId'],caseId=c1['caseId'],family=cases[c1['caseId']]['family'],slot=c1['modelSlot'])
  for phase,c in [('day0',c0),('day1',c1)]:
   p,fmt=parse_plan(c['system'],c['rawContent']);p=p if c['complete'] else None;n=native[phase][phase+'/'+c['callId']]
   entry[phase]=dict(transport=c['transport'],structure=fmt,match=bool(p is not None and score_plan(p,cases[c['caseId']]['oracle'])['proposal_correct']),nativeQualified=n['nativeQualified'],entryReachable=n['nativePlannerCalled'],status=n['response']['status'],responseModel=c.get('response',{}).get('model'),latencyMs=c['elapsedMs'],cost=c['estimatedCostCny'])
  paired.append(entry)
 assert [c['callId'] for c in raw['day0']]==[c['callId'] for c in raw['day1']],'Order changed'
 totals=[];plan=read(R/'plan.json');allraw=[c for p in (R/'results').glob('*/calls.jsonl') for c in lines(p)]
 for provider in ('deepseek','qwen'):
  cc=[c for c in allraw if c['provider']==provider];unknown=sum(c['estimatedCostCny'] is None for c in cc);value=sum(c['estimatedCostCny'] or 0 for c in cc)+unknown*plan['unknownReserveCny']
  assert value+plan['priorConservativeCny'][provider]<=20
  totals.append(dict(provider=provider,newConservative=value,cumulativeConservative=value+plan['priorConservativeCny'][provider],unknownUsage=unknown))
 assert sum(c['newConservative'] for c in totals)<=7
 summary=[]
 for slot in ('a','b'):
  pp=[p for p in paired if p['slot']==slot];row=dict(slot=slot,pairedObservations=len(pp),questions=len({p['caseId'] for p in pp}))
  row['transitions']={str(key):value for key,value in Counter((p['day0']['match'],p['day1']['match']) for p in pp).items()}
  for phase in ('day0','day1'):
   row[phase]=dict(match=sum(p[phase]['match'] for p in pp),qualified=sum(p[phase]['nativeQualified'] for p in pp),transportSuccess=sum(p[phase]['transport']=='SUCCESS' for p in pp),medianLatencyMs=statistics.median(p[phase]['latencyMs'] for p in pp),responseModels=sorted({str(p[phase]['responseModel']) for p in pp}),statuses=dict(Counter(p[phase]['status'] for p in pp)))
  summary.append(row)
 out.mkdir();write(out/'paired-ledger.json',paired);write(out/'metrics.json',dict(status='COMPLETE_ACTUAL_NEXT_DAY',gapSeconds=(start-finish).total_seconds(),summary=summary,costs=totals,human='PENDING_HUMAN_STUDY',reporterSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
 text='# 真实跨日配对结果\n\n72个配对观测来自12道题、6个题族；重复不是独立用户。输入payload、模型alias、顺序、业务Clock和H2快照一致。实际间隔 '+str(round((start-finish).total_seconds()))+' 秒，上海日期不同。\n\n| 模型槽位 | 题数 | 配对数 | day0严格匹配 | day1严格匹配 | day0原生合格 | day1原生合格 |\n|---|---|---|---|---|---|---|\n'
 for s in summary:text+='| '+ ' | '.join(str(v) for v in [s['slot'],s['questions'],s['pairedObservations'],s['day0']['match'],s['day1']['match'],s['day0']['qualified'],s['day1']['qualified']])+' |\n'
 text+='\n仅说明两个真实服务窗口的观察。alias未冻结权重；严格计划不匹配不等于错误事实。真人收益和独立盲标仍待测，实际账单未核。千问账号具有新用户赠送额度，费用数字为未抵扣赠送额度的理论估价；详见 ../BILLING_NOTE.md。今天及历史结果未覆盖。\n'
 (out/'RESULTS.md').write_bytes(text.encode());print('DAY1 VERIFY PASS: exact payload/order, real gap, frozen files, native controls, snapshots and budget; 72 paired observations')

if __name__=='__main__':main()
