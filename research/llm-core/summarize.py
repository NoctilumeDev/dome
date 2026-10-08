"""Descriptive publication outputs from sealed collection and evaluation-v2 only."""
import csv,html,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
from core import parse_plan,score_plan,review
ROOT=Path(__file__).resolve().parent

def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def table(rows,fields):
 return '\n'.join(['|'+'|'.join(fields)+'|','|'+'|'.join('---' for _ in fields)+'|']+['|'+'|'.join(str(r.get(k,'')) for k in fields)+'|' for r in rows])
def write_csv(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 folder=ROOT/'results/core';out=ROOT/'output';out.mkdir(exist_ok=True)
 collection=json.loads((folder/'collection-summary.json').read_text())
 assert collection['completedBlocks']==collection['plannedBlocks']==144 and collection['stop'] is None,'Do not publish an incomplete collection'
 report=json.loads((folder/'evaluation-v2/report.json').read_text(encoding='utf-8'))
 decisions=json.loads((folder/'evaluation-v2/decisions.json').read_text(encoding='utf-8'))
 calls=lines(folder/'calls.jsonl');bycall={c['callId']:c for c in calls};assert len(calls)==1728 and len(bycall)==1728
 cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))}
 native={n['callId']:n for s in ('qingye','library') for n in lines(folder/f'native-v2/native-{s}.jsonl')}
 ledger=[]
 for c in calls:
  if c['role']!='proposal':continue
  case=cases[c['caseId']];plan,fmt=parse_plan(c['system'],c['rawContent']);n=native[c['callId']]
  semantic=c['complete'] and score_plan(plan,case['oracle'])['proposal_correct']
  try:declared=json.loads(c['rawContent'])
  except (ValueError,TypeError):declared=None
  target_match=isinstance(declared,dict) and any(all(declared.get(k)==v for k,v in allowed.items() if v is not None and v!=[]) for allowed in case['oracle']['allowed'])
  status=n['response']['status']
  layer=('TRANSPORT' if not c['complete'] else 'PROTOCOL' if plan is None else 'SEMANTIC' if not semantic else 'NATIVE_ENTRY' if not n['nativePlannerCalled'] else 'NATIVE_POLICY' if not n['nativeQualified'] else 'MATCH')
  ledger.append(dict(callId=c['callId'],system=c['system'],family=case['family'],question=case['question'],provider=c['provider'],primary=c['callId'].endswith('/0'),transport=c['transport'],complete=c['complete'],format=fmt,semanticPlanCorrect=semantic,declaredNonNullTargetMatch=target_match,nativePlannerCalled=n['nativePlannerCalled'],nativeQualified=n['nativeQualified'],nativeStatus=status,pendingScope=status=='CONFIRM_SCOPE',databaseUnchanged=n['databaseUnchanged'],layer=layer,latencyMs=c['elapsedMs'],estimatedCostCny=c['estimatedCostCny']))
 write_csv(out/'proposal-ledger.csv',ledger)
 models=[]
 for system in ('qingye','library'):
  for provider in ('deepseek','qwen'):
   part=[l for l in ledger if l['system']==system and l['provider']==provider];primary=[l for l in part if l['primary']]
   models.append(dict(system=system,provider=provider,n=len(part),httpSuccess=sum(l['transport']=='SUCCESS' for l in part),protocolValid=sum(l['format']=='STRUCTURE_VALID' and l['complete'] for l in part),semanticCorrect=sum(l['semanticPlanCorrect'] for l in part),protocolInvalidTargetMatch=sum(l['complete'] and l['format']!='STRUCTURE_VALID' and l['declaredNonNullTargetMatch'] for l in part),primaryN=len(primary),primarySemanticCorrect=sum(l['semanticPlanCorrect'] for l in primary),entryGateRejected=sum(not l['nativePlannerCalled'] for l in primary),nativeQualified=sum(l['nativeQualified'] for l in part)))
 write_csv(out/'model-table.csv',models)
 costs=[]
 for provider in ('deepseek','qwen'):
  pp=[c for phase in ('pilot','core') for c in lines(ROOT/f'results/{phase}/calls.jsonl') if c['provider']==provider]
  costs.append(dict(provider=provider,attempts=len(pp),http200=sum(c.get('httpStatus')==200 for c in pp),estimatedCostCny=round(sum(c.get('estimatedCostCny') or 0 for c in pp),6),unknownUsage=sum(c.get('estimatedCostCny') is None for c in pp),authorizedCeilingCny=20,actualDebit='NOT_VERIFIED'))
 write_csv(out/'cost-table.csv',costs)
 group_rows=[]
 for s in report['groups']:
  matching=[r for r in decisions if r['group']==s['group'] and (s['system']=='both' or r['system']==s['system'])]
  costvals=[];timevals=[];unknown=0
  for d in matching:
   block=d['block'];g=s['group']
   if g.startswith('A:'):ids=[f'{block}/p/{g[-1]}/0']
   elif g=='B':ids=[f'{block}/p/a/0',f'{block}/p/b/0']
   elif g.startswith('C:'):ids=[f'{block}/p/a/0',f'{block}/p/b/0',f'{block}/r/{"b/a" if g.endswith("a") else "a/b"}']
   elif g=='D':ids=[f'{block}/p/a/0',f'{block}/p/b/0',f'{block}/r/a/b',f'{block}/r/b/a']
   elif g.startswith('E:'):ids=[f'{block}/p/{g[-1]}/0',f'{block}/r/{g[-1]}/{g[-1]}']
   else:ids=[f'{block}/p/{g[-1]}/{i}' for i in range(int(g[1]))]
   selected=[bycall[i] for i in ids]
   if all(c['elapsedMs'] is not None for c in selected):timevals.append(sum(c['elapsedMs'] for c in selected))
   else:unknown+=1
   if all(c['estimatedCostCny'] is not None for c in selected):costvals.append(sum(c['estimatedCostCny'] for c in selected))
  nr=dict(s,expectedQueries=sum(d['expectedQuery'] for d in matching),queryHandlingCorrect=sum(d['handlingCorrect'] and d['expectedQuery'] for d in matching),policyAbstentions=sum(d['actualStatus']=='POLICY_ABSTENTION' for d in matching),entryRejections=sum(d['outcomeOrigin']=='NATIVE_ENTRY_GATE' for d in matching),meanLogicalCostCny=round(statistics.mean(costvals),7) if costvals else None,medianLogicalSerialMs=round(statistics.median(timevals),1) if timevals else None,logicalLatencyUnknown=unknown)
  group_rows.append(nr)
 write_csv(out/'group-table.csv',group_rows)
 reviews=report['review'];review_rows=[]
 for reviewer in ('a','b'):
  for proposer in ('a','b'):
   part=[r for r in reviews if r['reviewer']==reviewer and r['proposer']==proposer]
   query_veto=sum(r['falseKill'] and r['nativeQualified'] and json.loads(bycall[f"{r['block']}/p/{r['proposer']}/0"]['rawContent']).get('action')=='QUERY' for r in part)
   review_rows.append(dict(reviewer=reviewer,proposer=proposer,n=len(part),correctCandidates=sum(r['proposalCorrect'] for r in part),correctPlanNonAccept=sum(r['falseKill'] for r in part),nativeQualifiedCorrect=sum(r['proposalCorrect'] and r['nativeQualified'] for r in part),qualifiedPlanNonAccept=sum(r['falseKill'] and r['nativeQualified'] for r in part),queryFalseKill=query_veto,unavailableCorrect=sum(r['reviewUnavailableCorrect'] for r in part),incorrectCandidates=sum(not r['proposalCorrect'] for r in part),missedError=sum(r['missedError'] for r in part),invalidOrUnavailable=sum(r['verdict'] in ('INVALID_REVIEW','UNAVAILABLE') for r in part)))
 write_csv(out/'review-table.csv',review_rows)
 exemplars=[]
 for predicate,label in [(lambda l:l['layer']=='NATIVE_ENTRY','原生第一门拒绝'),(lambda l:l['format']!='STRUCTURE_VALID','协议失败'),(lambda l:l['complete'] and l['format']=='STRUCTURE_VALID' and not l['semanticPlanCorrect'],'语义偏差'),(lambda l:l['pendingScope'],'个人范围待确认')]:
  item=next((l for l in ledger if predicate(l)),None)
  if item:
   c=bycall[item['callId']];exemplars.append(dict(label=label,callId=item['callId'],question=item['question'],oracle=cases[item['callId'].split('-r')[0]]['oracle'],modelContent=c['rawContent'],native=native[item['callId']]))
 # Include a correct proposal explicitly vetoed by a reviewer, if observed.
 bad=next((r for r in reviews if r['falseKill'] and r['nativeQualified'] and json.loads(bycall[f"{r['block']}/p/{r['proposer']}/0"]['rawContent']).get('action')=='QUERY'),None)
 if bad:
  cid=f"{bad['block']}/p/{bad['proposer']}/0";rid=f"{bad['block']}/r/{bad['reviewer']}/{bad['proposer']}";c=bycall[cid]
  exemplars.append(dict(label='正确提案被审查否决',callId=cid,question=cases[c['caseId']]['question'],modelContent=c['rawContent'],review=bycall[rid]['rawContent'],native=native[cid]))
 dump(out/'examples.json',exemplars)
 primary=[l for l in ledger if l['primary']]
 metrics=dict(models=models,costs=costs,groups=group_rows,reviews=review_rows,primaryLayers=Counter(l['layer'] for l in primary),allProposalLayers=Counter(l['layer'] for l in ledger),uniqueWrongPublicPrimary=sum(r['wrongAutomaticExecution'] for r in decisions if r['group'].startswith('A:')),authorityScope='Replay mutations absent, snapshots unchanged, foreign-user canaries absent; no production or universal guarantee',latency=report['latency'],firstFailure='scorer-first-failure.txt',evaluationVersion='v2',baseSha='dbb32160a811fd06c826a8d9eafbc660a0548219')
 dump(out/'metrics.json',metrics)
 rows=[r for r in group_rows if r['system']=='both']
 md='# 双系统核心实验结果\n\n48 题 × 3 次重复 = 144 配对块；1,728 次请求身份，含 1 次中断后结果未知；另有 96 次先导。a=DeepSeek，b=Qwen。正式原始数据不因错误而删题。\n\n'
 md+='## 模型层\n\n'+table(models,['system','provider','n','httpSuccess','protocolValid','semanticCorrect','primaryN','primarySemanticCorrect','entryGateRejected'])
 md+='\n\n## 决策层\n\n'+table(rows,['group','n','handlingCorrect','expectedQueries','queryHandlingCorrect','publicCompletedCorrect','pendingScope','wrongAutomaticExecution','policyAbstentions','meanLogicalCostCny','medianLogicalSerialMs'])
 md+='\n\nhandlingCorrect 包含期望澄清输入上的离线策略弃权，不是成功完成查询。queryHandlingCorrect 允许正确的范围待确认，不表示个人记录已经读取。publicCompletedCorrect 只表示正确公开计划在固定原生链路执行，不证明真实用户效用或每个返回字段的跨数据库正确性。wrongAutomaticExecution 每组独立计数，不能跨组加总为事故数。\n\n'
 md+='## 审查层\n\n'+table(review_rows,list(review_rows[0]))
 md+='\n\n原 v2 字段 falseKill 保留在原始评分中；派生表纠正为 correctPlanNonAccept/qualifiedPlanNonAccept，表示正确计划未获 ACCEPT 的门控事件，含正确澄清计划。审查提示允许对多请求给 CLARIFY，因此不能把这些全部判为审查错误或丢失需求。queryFalseKill 单列正确 QUERY 被阻断。格式/服务失败另算；未独立真人标注。\n\n## 费用\n\n'+table(costs,list(costs[0]))
 md+='\n\n按官方峰值/缓存未命中单价估算，实际账单未读取。UNKNOWN 不算免费。逻辑延迟是调用耗时串行求和，不是在线部署实测；不同组共享原始请求，费用不能跨组相加。\n\n## 关键反例\n\n'
 for e in exemplars:md+=f"- **{e['label']}** `{e['callId']}`：{e['question']}。见 examples.json 的真实响应及原生见证。\n"
 md+='\n## 边界\n\n两个系统来自同一仓库；题族由执行者提出，三个重复不是三个独立用户。模型别名未冻结权重。未做真人范围识别、微信真机、生产 MySQL、多节点或在线互审部署。新解法只能作为后续假设，不能用本轮数据反复调参后宣称独立验证。\n'
 (out/'RESULTS.md').write_text(md,encoding='utf-8')
 body='<h1>双系统核心实验 · 冻结结果</h1><p class="sub">dbb32160 · evaluation-v2 · 真实供应商响应 + 原生 Java/H2 回放</p><div class="cards"><b>48 题 × 3 次</b><b>1,728 请求身份</b><b>含 1 次 UNKNOWN</b><b>未做真人研究</b></div>'
 body+='<h2>决策结果</h2><p>处置符合合同含策略弃权；公开正确执行和范围待确认单列。a=DeepSeek，b=Qwen。</p><table><tr>'+''.join('<th>'+f+'</th>' for f in ('组','处置符合/144','公开正确执行','待范围确认','错误自动执行','策略弃权'))+'</tr>'
 for r in rows:body+='<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in (r['group'],r['handlingCorrect'],r['publicCompletedCorrect'],r['pendingScope'],r['wrongAutomaticExecution'],r['policyAbstentions']))+'</tr>'
 body+='</table><h2>真实反例与边界</h2>'
 for e in exemplars:
  body+=f'<article><h3>{html.escape(e["label"])}</h3><p>{html.escape(e["question"])}</p><small>{e["callId"]}</small><pre>{html.escape(e["modelContent"])}</pre>'
  if 'review' in e:body+='<pre>'+html.escape(e['review'])+'</pre>'
  body+='<p>原生状态：'+html.escape(e['native']['response']['status'])+'；数据库未改变：'+str(e['native']['databaseUnchanged'])+'</p></article>'
 body+='<p class="sub">本页是冻结记录查看器截图，不是在线生产 UI。原始记录与 CSV 是证据主体；图片是旁证。</p>'
 (out/'dashboard.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>双系统实验结果</title><style>body{font:16px/1.6 system-ui,"Microsoft YaHei";color:#24343a;background:#f6f4ef;margin:0;padding:44px;max-width:1250px}h1{font-size:34px;margin:0}h2{margin-top:32px}.sub{color:#596c71}.cards{display:flex;gap:18px;margin:24px 0}.cards b{background:#e4ebe7;padding:14px 22px;border-radius:8px}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:9px 14px;border-bottom:1px solid #dfe5e2}th{background:#dfe8e4}article{background:white;border:1px solid #d6dfdb;padding:18px 24px;margin:18px 0;border-radius:9px}pre{white-space:pre-wrap;word-break:break-word;font-size:13px;background:#f1f4f3;padding:14px}small{color:#637b78}</style>'+body+'</html>',encoding='utf-8')
 print(json.dumps({'proposalRows':len(ledger),'tables':len(group_rows),'costs':costs,'examples':len(exemplars)},ensure_ascii=False))
if __name__=='__main__':main()
