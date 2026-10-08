"""Stratify the frozen extension; never pool new questions with the original table."""
import csv,html,json,statistics,sys
from collections import Counter
from pathlib import Path
E=Path(__file__).resolve().parent;R=E.parent
sys.path.insert(0,str(R))
from core import parse_plan,score_plan

def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csvout(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def table(rows,fields):return '\n'.join(['|'+'|'.join(fields)+'|','|'+'|'.join('---' for _ in fields)+'|']+['|'+'|'.join(str(r[k]) for k in fields)+'|' for r in rows])
def callids(d):
 b=d['block'];g=d['group']
 if g.startswith('A:'):return [f'{b}/p/{g[-1]}/0']
 if g=='B':return [f'{b}/p/a/0',f'{b}/p/b/0']
 if g.startswith('C:'):return [f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/{"b/a" if g.endswith("a") else "a/b"}']
 if g=='D':return [f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/a/b',f'{b}/r/b/a']
 if g.startswith('E:'):return [f'{b}/p/{g[-1]}/0',f'{b}/r/{g[-1]}/{g[-1]}']
 return [f'{b}/p/{g[-1]}/{i}' for i in range(int(g[1]))]

def summarize_decisions(ds,calls):
 rows=[]
 for system in ('qingye','library','both'):
  for group in dict.fromkeys(d['group'] for d in ds):
   part=[d for d in ds if d['group']==group and (system=='both' or d['system']==system)]
   times=[];costs=[]
   for d in part:
    cc=[calls[x] for x in callids(d)]
    if all(c['elapsedMs'] is not None for c in cc):times.append(sum(c['elapsedMs'] for c in cc))
    if all(c['estimatedCostCny'] is not None for c in cc):costs.append(sum(c['estimatedCostCny'] for c in cc))
   rows.append(dict(system=system,group=group,n=len(part),handlingCorrect=sum(d['handlingCorrect'] for d in part),expectedQueries=sum(d['expectedQuery'] for d in part),queryHandlingCorrect=sum(d['handlingCorrect'] and d['expectedQuery'] for d in part),publicCompletedCorrect=sum(d['publicCompletedCorrect'] for d in part),pendingScope=sum(d['pendingScope'] for d in part),wrongAutomaticExecution=sum(d['wrongAutomaticExecution'] for d in part),policyAbstentions=sum(d['actualStatus']=='POLICY_ABSTENTION' for d in part),meanLogicalCostCny=round(statistics.mean(costs),7),medianLogicalSerialMs=statistics.median(times)))
 return rows

def main():
 out=E/'output';out.mkdir(exist_ok=True)
 cases={c['id']:c for c in json.loads((E/'cases.json').read_text(encoding='utf-8'))}
 raw=lines(E/'results/core/calls.jsonl');calls={c['callId']:c for c in raw}
 assert len(raw)==len(calls)==768
 decisions=json.loads((E/'results/core/evaluation-v2/decisions.json').read_text(encoding='utf-8'))
 report=json.loads((E/'results/core/evaluation-v2/report.json').read_text(encoding='utf-8'))
 native={n['callId']:n for s in ('qingye','library') for n in lines(E/f'results/core/native-v2/native-{s}.jsonl')}
 strata=Counter(c['stratum'] for c in cases.values());print('Strata:',strata)
 groups=[];models=[];reviews=[]
 for stratum in strata:
  ds=[d for d in decisions if cases[d['caseId']]['stratum']==stratum]
  groups.extend(dict(stratum=stratum,**r) for r in summarize_decisions(ds,calls))
  for system in ('qingye','library'):
   for provider in ('deepseek','qwen'):
    cc=[c for c in raw if c['role']=='proposal' and c['system']==system and c['provider']==provider and cases[c['caseId']]['stratum']==stratum]
    primary=[c for c in cc if c['callId'].endswith('/0')]
    def correct(c):return c['complete'] and score_plan(parse_plan(system,c['rawContent'])[0],cases[c['caseId']]['oracle'])['proposal_correct']
    models.append(dict(stratum=stratum,system=system,provider=provider,n=len(cc),httpSuccess=sum(c['httpStatus']==200 for c in cc),protocolValid=sum(c['complete'] and parse_plan(system,c['rawContent'])[0] is not None for c in cc),semanticCorrect=sum(correct(c) for c in cc),primaryN=len(primary),primarySemanticCorrect=sum(correct(c) for c in primary),entryRejected=sum(not native[c['callId']]['nativePlannerCalled'] for c in primary)))
  for reviewer in ('a','b'):
   for proposer in ('a','b'):
    rr=[x for x in report['review'] if x['reviewer']==reviewer and x['proposer']==proposer and cases[x['block'].rsplit('-r',1)[0]]['stratum']==stratum]
    reviews.append(dict(stratum=stratum,reviewer=reviewer,proposer=proposer,n=len(rr),qualifiedCorrectNonAccept=sum(x['falseKill'] and x['nativeQualified'] for x in rr),queryFalseKill=sum(x['falseKill'] and x['nativeQualified'] and json.loads(calls[f"{x['block']}/p/{proposer}/0"]['rawContent']).get('action')=='QUERY' for x in rr),missedError=sum(x['missedError'] for x in rr)))
 # Compare the same question, not an aggregate of different strata or independent users.
 previous=json.loads((R/'results/core/evaluation-v2/decisions.json').read_text(encoding='utf-8'))
 oldcaseids={d['caseId'] for d in previous}
 assert sum(c['id'] in oldcaseids for c in cases.values())==48
 pairs=[]
 for case in cases.values():
  if case['id'] not in oldcaseids:continue
  for group in dict.fromkeys(d['group'] for d in decisions):
   old=[d for d in previous if d['caseId']==case['id'] and d['group']==group]
   new=next(d for d in decisions if d['caseId']==case['id'] and d['group']==group)
   pairs.append(dict(caseId=case['id'],system=case['system'],group=group,coreRepetitions=len(old),coreHandlingCorrect=sum(d['handlingCorrect'] for d in old),laterHandlingCorrect=int(new['handlingCorrect']),coreQueryHandling=sum(d['handlingCorrect'] and d['expectedQuery'] for d in old),laterQueryHandling=int(new['handlingCorrect'] and new['expectedQuery']),coreWrongAutomatic=sum(d['wrongAutomaticExecution'] for d in old),laterWrongAutomatic=int(new['wrongAutomaticExecution']),laterStatus=new['actualStatus']))
 assert len(pairs)==48*14 and all(p['coreRepetitions']==3 for p in pairs)
 failures=[]
 for d in decisions:
  if not d['group'].startswith('A:') or d['handlingCorrect']:continue
  c=calls[f"{d['block']}/p/{d['group'][-1]}/0"]
  failures.append(dict(stratum=cases[d['caseId']]['stratum'],caseId=d['caseId'],group=d['group'],question=cases[d['caseId']]['question'],actualStatus=d['actualStatus'],wrongAutomatic=d['wrongAutomaticExecution'],raw=c['rawContent'],oracle=cases[d['caseId']]['oracle']))
 costs=[]
 for provider in ('deepseek','qwen'):
  cc=[c for stage in (R/'results/pilot',R/'results/core',E/'results/core') for c in lines(stage/'calls.jsonl') if c['provider']==provider]
  costs.append(dict(provider=provider,attempts=len(cc),http200=sum(c.get('httpStatus')==200 for c in cc),estimatedCostCny=round(sum(c.get('estimatedCostCny') or 0 for c in cc),6),unknownUsage=sum(c.get('estimatedCostCny') is None for c in cc),authorizedCeilingCny=20,actualDebit='NOT_VERIFIED'))
 data=dict(strata=dict(strata),groups=groups,models=models,reviews=reviews,cumulativeCosts=costs,pairedWindow=pairs,failures=failures,scope='Later-window known questions and prospective author-labeled questions reported separately; no independent blind labels, human trial, or cross-day stability')
 dump(out/'metrics.json',data);csvout(out/'group-table.csv',groups);csvout(out/'model-table.csv',models);csvout(out/'review-table.csv',reviews);csvout(out/'paired-window.csv',pairs);csvout(out/'cumulative-costs.csv',costs);dump(out/'failures.json',failures)
 fields=['group','n','handlingCorrect','expectedQueries','queryHandlingCorrect','publicCompletedCorrect','pendingScope','wrongAutomaticExecution','policyAbstentions']
 md='# 补充控制实验结果\n\n64 配对块、768 次调用；原 48 题后窗口与 16 道新语法组合题分层报告。a=DeepSeek，b=Qwen。固定源 SHA、协议、夹具、时钟、评分器均保持不变。\n\n'
 for stratum in strata:
  md+=f'## {stratum} · {strata[stratum]} 块\n\n'+table([g for g in groups if g['stratum']==stratum and g['system']=='both'],fields)+'\n\n'
 md+='## 模型/协议层\n\n'+table(models,list(models[0]))+'\n\n## 审查门控\n\n'+table(reviews,list(reviews[0]))
 md+='\n\n## 全轮累计费用\n\n'+table(costs,list(costs[0]))+'\n\n金额为官方单价保守估算，含先导、核心、扩展；1 次历史中断费用未知，另留 ¥0.01 余量。实际扣费未读取。\n'
 md+='\n## 失败坐标\n\n'
 for f in failures:md+=f"- {f['stratum']} / {f['caseId']} / {f['group']}：{f['question']} → {f['actualStatus']}；错误自动执行={f['wrongAutomatic']}。原计划及冻结标签见 failures.json。\n"
 md+='\n后窗口只对原题作描述性配对，采集时间与重平衡顺序共同变化，不能识别纯时间因果。新题由同一执行者在核心后设计、扩展前冻结，模型不可见标签，执行者不是独立盲标者。历史回放仅转移既有计划，不重新归入模型语义分母。各组共享调用，错误数不能横向累加为独立事件。\n'
 (out/'RESULTS.md').write_text(md,encoding='utf-8')
 controls=json.loads((R/'CONTROL_LEDGER.json').read_text(encoding='utf-8'))['controls']
 def htmltable(rows,fields,labels):
  return '<table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in labels)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(row[k]))+'</td>' for k in fields)+'</tr>' for row in rows)+'</tbody></table>'
 coremetrics=json.loads((R/'output/metrics.json').read_text(encoding='utf-8'))
 show=('A:a','A:b','B','D','E:a','E:b','F2:a','F2:b','F4:a','F4:b')
 f=['group','n','queryHandlingCorrect','publicCompletedCorrect','pendingScope','wrongAutomaticExecution','policyAbstentions']
 labels=['组','配对块','正确查询/范围','公开正确执行','待范围确认','错误自动执行','策略弃权']
 page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>双系统 · 控制变量总账</title><style>body{margin:0;background:#f2f5f1;color:#243c43;font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1160px;margin:32px auto;padding:0 28px}h1{font-size:34px;margin:4px 0}h2{font-size:20px;margin-top:28px}p{margin:10px 0}.meta{color:#526969}.stats{display:flex;gap:18px;margin:24px 0}.stats div{background:white;border:1px solid #d4ded6;border-radius:10px;padding:14px 24px;flex:1}.stats strong{display:block;font-size:30px}section{background:white;border:1px solid #d4ded6;border-radius:12px;padding:20px;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;border-bottom:1px solid #dde5df;padding:7px 10px}th{background:#e6eeea}.note{border-left:4px solid #986a4e;background:#f5eee8;padding:12px 18px}.end{font-size:12px;color:#617672}</style><main><div class="meta">冻结记录查看器 · 2026-10-08 · a=DeepSeek / b=Qwen</div><h1>双系统 · 控制变量总账</h1><p>核心、后窗口、新组合题分开报告。测量完成 ≠ 结论普遍成立。</p>'
 page+=f'<div class="stats"><div>全部请求身份<strong>2,592</strong>1 次中断未知保留</div><div>核心 + 补充配对块<strong>144 + 64</strong>另有 8 块先导</div><div>控制族 / 总账项<strong>8 / 21</strong>未证明项仍有坐标</div><div>累计保守估算<strong>¥{sum(c["estimatedCostCny"] for c in costs):.4f}</strong>实际扣费未核对</div></div>'
 page+='<p class="note">本轮三层表中，B 与 D 的正确公开执行相同；双向审查未增加查询收益。保守弃权能挡错，不能当成恢复答案。独立盲标、真人识别与跨日稳定未证明。</p>'
 allparts=[('核心已知题 · 48 题 × 3 次',[g for g in coremetrics['groups'] if g['system']=='both'])]+[(('原 48 题 · 后窗口' if i==0 else '16 道前瞻组合题 · 扩展前冻结'),[g for g in groups if g['system']=='both' and g['stratum']==stratum]) for i,stratum in enumerate(strata)]
 for label,part in allparts:page+='<section><h2>'+label+'</h2>'+htmltable([g for g in part if g['group'] in show],f,labels)+'</section>'
 page+='<section><h2>控制族逐项状态</h2>'+htmltable(controls,['id','family','name','status'],['ID','族','控制项','状态'])+'</section><p class="end">只读离线记录展示；不是产品现场。源 SHA dbb32160a811fd06c826a8d9eafbc660a0548219。H2 原生见证、原始 JSONL、CSV 与冻结合同负责证据；截图仅为旁证。</p></main></html>'
 (R/'output/control-dashboard.html').write_text(page,encoding='utf-8')
 print('Extension strata summarized; broad generalization remains NOT_QUALIFIED')
if __name__=='__main__':main()
