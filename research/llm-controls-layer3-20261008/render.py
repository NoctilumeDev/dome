"""Present frozen measurements without altering raw outputs, scoring, or prior paper."""
import html,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def table(rows,fields):
 return '| '+' | '.join(label for key,label in fields)+' |\n|'+ '|'.join('---' for _ in fields)+'|\n'+'\n'.join('| '+' | '.join(str(row.get(key,'')) for key,label in fields)+' |' for row in rows)
def main():
 out=R/'output';m=json.loads((out/'metrics.json').read_text(encoding='utf-8'));raw={r['phase']+'/'+r['callId']:r for p in (R/'results').glob('*/calls.jsonl') for r in lines(p)};decisions=json.loads((out/'decision-ledger.json').read_text(encoding='utf-8'));logical=[]
 for group in sorted({r['group'] for r in decisions}):
  rr=[r for r in decisions if r['group']==group];lat=[];cost=[];input_tokens=[];output_tokens=[]
  for row in rr:
   b='formal/'+row['block'];g=group
   if g.startswith('A:'):ids=[f'{b}/p/{g[-1]}/0']
   elif g=='B':ids=[f'{b}/p/a/0',f'{b}/p/b/0']
   elif g.startswith('C:'):ids=[f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/'+('b/a' if g.endswith('a') else 'a/b')]
   elif g=='D':ids=[f'{b}/p/a/0',f'{b}/p/b/0',f'{b}/r/a/b',f'{b}/r/b/a']
   elif g.startswith('E:'):ids=[f'{b}/p/{g[-1]}/0',f'{b}/r/{g[-1]}/{g[-1]}']
   else:ids=[f'{b}/p/{g[-1]}/{i}' for i in range(int(g[1]))]
   calls=[raw[k] for k in ids];lat.append(sum(c['elapsedMs'] for c in calls))
   if all(c['estimatedCostCny'] is not None for c in calls):
    cost.append(sum(c['estimatedCostCny'] for c in calls));input_tokens.append(sum(c['response']['usage']['prompt_tokens'] for c in calls));output_tokens.append(sum(c['response']['usage']['completion_tokens'] for c in calls))
  logical.append(dict(group=group,serialMedianMs=round(statistics.median(lat),3),meanEstimatedCny=round(statistics.mean(cost),8) if cost else None,meanInputTokens=round(statistics.mean(input_tokens),3) if input_tokens else None,meanOutputTokens=round(statistics.mean(output_tokens),3) if output_tokens else None,knownCostBlocks=len(cost)))
 (out/'logical-cost-latency.json').write_bytes((json.dumps(logical,ensure_ascii=False,indent=2)+'\n').encode())
 variation=m['dependence'];risk=m['risk'];review=m['reviewNet'];summ=m['summary'];cost=m['costs']
 proposals=json.loads((out/'proposal-ledger.json').read_text(encoding='utf-8'))
 for row in summ:
  dd=[p for p in proposals if (p['phase'],p['stratum'],p['slot'])==(row['phase'],row['stratum'],row['slot'])]
  row['nativeQualified']=sum(p['nativeQualified'] for p in dd)
 phases={r['phase'] for r in raw.values()};day1='COMPLETE' if 'day1' in phases else 'WAITING_REAL_NEXT_DAY';claims=[dict(claim='逐题联合误差最低识别条件',status=variation['status']),dict(claim='B后自然审查机会',status=review[0]['status']),dict(claim='原文外部兼容泛化',status='NOT_ESTABLISHED'),dict(claim='适配外部题/边界入口',status='COMPLETE_SEPARATE_STRATA'),dict(claim='同窗口档位',status='COMPLETE' if 'tier' in phases else 'NOT_RUN'),dict(claim='真实跨日',status=day1),dict(claim='独立真人盲标/真人范围确认',status='PENDING_HUMAN_STUDY')]
 intro=f'# 第三证据层结果\n\n本页仅描述本轮冻结分布。旧论文与第二层不改；新增 {len(raw)} 个请求身份，实际账单未核。pilot与正式、外部原文与适配、档位与跨日分别记账。\n\n结构字段合格只检查完整字段及类型；有限枚举、权限和参数资格由原生层另行检验，不能把结构合格当成完整能力协议合格。澄清子原因差异仍按严格标签计分，不能直接升级成任务事实错误。\n\n'
 report=intro+'## 资格账本\n\n'+table(claims,[('claim','问题'),('status','资格')])+'\n\n## 正式主提案\n\n'+table([risk],[(k,k) for k in risk])+'\n\n## B后的审查\n\n'+table(review,[(k,k) for k in review[0]])+'\n\n## 单模型与各层\n\n'+table(summ,[('phase','包'),('stratum','分层'),('slot','模型槽位'),('n','调用'),('questions','题数'),('valid','结构字段合格'),('nativeQualified','原生资格合格'),('match','严格计划匹配'),('public','公开执行'),('wrongPublicPlan','公开执行但计划不匹配'),('scope','范围确认'),('entryBlocked','入口拦截')])+'\n\n## 费用\n\n'+table(cost,[('provider','厂商'),('requestIdentities','身份'),('knownEstimate','本轮估价'),('unknown','未知usage'),('cumulativeConservative','累计含余量'),('ceiling','上限')])+'\n\n## 逻辑成本/延迟\n\n'+table(logical,[('group','策略'),('serialMedianMs','串行逻辑中位ms'),('meanEstimatedCny','逻辑均价'),('meanInputTokens','输入token均量'),('meanOutputTokens','输出token均量'),('knownCostBlocks','有usage块')])+'\n\n不能把逻辑延迟当成线上端到端延迟；等调用次数不等于等金额。\n\n## 边界\n\n重复块不是独立用户样本。缺少同题错误变异时，置换P=1不证明误差独立。严格intent/字段标签错误不自动等于事实错误；PRIVATE范围确认不等于语义修复或真人识别成功。外部adapted compatible进行了公开的操作替换，不是DuSQL原题泛化成绩。八道原文边界按事前原生入口确定拒绝/澄清标签，没有事后挑题。档位是实际model ID对照，权重未冻结。跨日只在真实相隔24小时且日期不同后取得资格。Java/H2回放不是生产MySQL。\n'
 (out/'RESULTS.md').write_bytes(report.encode())
 content=['<h1>第三层 · 非人工控制实验</h1><p>冻结输入与评分；所有结论以各证据包的资格为准。</p><p>a = DeepSeek flash；b = Qwen plus；ds_pro = DeepSeek v4 pro；q_flash = Qwen flash。</p>']
 for title,rows,fields in [('资格账本',claims,[('claim','问题'),('status','资格')]),('B后自然审查',review,[('group','策略'),('bWrongQueryableOpportunity','剩余错误机会'),('explicitNewErrorCatch','明确新增拦错'),('correctQueryBlocked','正确QUERY拦截'),('correctClarifyRejudged','正确澄清再审')]),('分包结果',summ,[('phase','包'),('stratum','分层'),('slot','模型'),('n','调用'),('match','计划匹配'),('wrongPublicPlan','公开执行计划不匹配'),('scope','确认')]),('预算',cost,[('provider','厂商'),('requestIdentities','本轮身份'),('cumulativeConservative','累计含余量')])]:
  content.append('<h2>'+title+'</h2><table><thead><tr>'+''.join('<th>'+label+'</th>' for k,label in fields)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(row.get(k,'')))+'</td>' for k,label in fields)+'</tr>' for row in rows)+'</tbody></table>')
 cases={c['id']:c for c in json.loads((R/'cases.json').read_text(encoding='utf-8'))}
 for witness in json.loads((out/'review-net-ledger.json').read_text(encoding='utf-8')):
  if witness['group']=='D' and witness['correctQueryBlocked']:
   block=witness['block'];candidate=raw['formal/'+block+'/p/b/0']['rawContent'];judgment=witness['reviewReasons']['a:b']
   content.append('<h2>保留反例 · 正确查询被审查误拦</h2><p>'+html.escape(cases[witness['caseId']]['question'])+'</p><p>候选：<code>'+html.escape(candidate)+'</code></p><p>DeepSeek 审查：<code>'+html.escape(judgment)+'</code></p><small>'+html.escape(block)+'；不改原始输出、不补修产品。</small>')
   break
 content.append('<p class="limit">重复不等于独立样本；结构字段不等于完整能力资格；公开计划不匹配不等于事实错误；外部改写不等于原文泛化。真人仍待测，跨日等真实下一窗口。</p>')
 doc='<!doctype html><html lang="zh"><meta charset="utf-8"><title>第三层控制实验</title><style>body{font:16px system-ui,"Microsoft YaHei";max-width:1120px;margin:36px auto;background:#f6f4ef;color:#283631}h1{color:#385347}h2{margin-top:30px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d9ded9;padding:8px 10px;text-align:left;font-size:13px}th{background:#e6ede6}.limit{font-size:14px;padding:18px;background:#fff0d8}p{line-height:1.7}</style><body>'+''.join(content)+'</body></html>'
 (out/'dashboard.html').write_bytes(doc.encode());print('Presentation generated; raw/scoring unchanged')
if __name__=='__main__':main()
