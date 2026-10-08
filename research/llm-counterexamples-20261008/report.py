"""Read-only summaries of frozen scores, with transport and verdict causes separate."""
import csv, html, json, statistics, sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R.parent / 'llm-core'))
from core import review, parse_plan

def rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]

def table(data, columns):
    def fmt(v):
        if v is None: return '—'
        if isinstance(v, float): return f'{v:.6f}'
        return str(v).replace('|', '\\|')
    return '\n'.join(['|'+'|'.join(label for key,label in columns)+'|',
                      '|'+'|'.join('---' for _ in columns)+'|']+
                     ['|'+'|'.join(fmt(d.get(key)) for key,label in columns)+'|' for d in data])

def main():
    out = R / 'output'
    m = json.loads((out / 'metrics.json').read_text(encoding='utf-8'))
    plan = json.loads((R / 'plan.json').read_text(encoding='utf-8'))
    natural = rows(R / 'results/core/calls.jsonl')
    challenge = rows(R / 'results/challenge/calls.jsonl')
    diag = json.loads((R / 'diagnostics/transport-result.json').read_text(encoding='utf-8'))
    diagnostic = [x for x in diag['records'] if x.get('callId')]
    calls = {x['callId']:x for x in natural}
    cases = {x['id']:x for x in json.loads((R / 'cases.json').read_text(encoding='utf-8'))}
    native = {x['callId']:x for s in ('qingye','library') for x in rows(R/f'results/core/native-v2/native-{s}.jsonl')}
    qualifications = []
    for stratum in dict.fromkeys(x['stratum'] for x in cases.values()):
        for provider in ('deepseek','qwen'):
            cc=[x for x in natural if x['role']=='proposal' and x['provider']==provider and cases[x['caseId']]['stratum']==stratum]
            qualifications.append(dict(stratum=stratum,provider=provider,n=len(cc),complete=sum(x['complete'] for x in cc),structureValid=sum(x['complete'] and parse_plan(x['system'],x['rawContent'])[0] is not None for x in cc),nativeQualified=sum(native[x['callId']]['nativeQualified'] for x in cc),nativeEntryBlocked=sum(native[x['callId']].get('nativePlannerCalled') is False for x in cc)))
    decisions = json.loads((R / 'results/core/evaluation-v2/decisions.json').read_text(encoding='utf-8'))
    by = {(x['block'],x['group']):x for x in decisions}
    breakdown = []
    opportunities = []
    for stratum in dict.fromkeys(x['stratum'] for x in cases.values()):
        bb = [x for x in decisions if x['group']=='B' and cases[x['caseId']]['stratum']==stratum]
        queryable = [x for x in bb if x['selectedPlan'] is not None and x['selectedPlan']['action']=='QUERY' and x['actualStatus'] in ('QUERY','CONFIRM_SCOPE')]
        opportunities.append(dict(stratum=stratum,wrongQueryableOpportunities=sum(not x['semanticPlanCorrect'] for x in queryable),correctQueryableOpportunities=sum(x['semanticPlanCorrect'] for x in queryable),correctClarifyCandidates=sum(x['selectedPlan'] is not None and x['selectedPlan']['action']=='CLARIFY' and x['semanticPlanCorrect'] for x in bb)))
        for group in ('C:a','C:b','D'):
            count = Counter()
            for b in [x for x in decisions if x['group']=='B' and cases[x['caseId']]['stratum']==stratum]:
                d = by[(b['block'],group)]
                if b['selectedPlan'] is None or d['selectedPlan'] is not None: continue
                ids = ['b/a'] if group=='C:a' else ['a/b'] if group=='C:b' else ['a/b','b/a']
                verdicts = [review(calls[b['block']+'/r/'+i]['rawContent']) if calls[b['block']+'/r/'+i]['complete'] else 'UNAVAILABLE' for i in ids]
                veto = any(v in ('CLARIFY','REJECT') for v in verdicts)
                unavailable = any(v not in ('ACCEPT','CLARIFY','REJECT') for v in verdicts)
                cause = 'mixed' if veto and unavailable else 'explicit' if veto else 'unavailable'
                count[cause] += 1
                if b['selectedPlan']['action']=='QUERY' and b['actualStatus'] in ('QUERY','CONFIRM_SCOPE'):
                    key = 'correct' if b['semanticPlanCorrect'] else 'wrong'
                    count[cause+'_'+key] += 1
            breakdown.append(dict(stratum=stratum,group=group,**{k:count[k] for k in ['explicit','unavailable','mixed','explicit_wrong','explicit_correct','unavailable_wrong','unavailable_correct','mixed_wrong','mixed_correct']}))
    with (out / 'review-cause-breakdown.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(breakdown[0]));w.writeheader();w.writerows(breakdown)
    transport = []
    for stage,data in [('natural',natural),('injected_review',challenge),('diagnostic',diagnostic)]:
        for provider in ('deepseek','qwen'):
            pp=[x for x in data if x.get('provider')==provider]
            if pp: transport.append(dict(stage=stage,provider=provider,n=len(pp),**dict(Counter(x['transport'] for x in pp)),knownCost=sum(x.get('estimatedCostCny') or 0 for x in pp),unknown=sum(x.get('estimatedCostCny') is None for x in pp)))
    all_calls=natural+challenge+diagnostic
    budget=[]
    for provider in ('deepseek','qwen'):
        cc=[x for x in all_calls if x.get('provider')==provider]
        known=sum(x.get('estimatedCostCny') or 0 for x in cc)
        unknown=sum(x.get('estimatedCostCny') is None for x in cc)
        budget.append(dict(provider=provider,newRequestIdentities=len(cc),newKnownEstimatedCny=known,newUnknownReserveCny=.01*unknown,priorEstimatedCny=plan['priorEstimatedCny'][provider],cumulativeKnownEstimate=plan['priorEstimatedCny'][provider]+known,cumulativeWithConservativeReserves=plan['priorEstimatedCny'][provider]+known+.01*unknown+plan['priorUnknownReserveCny'],ceiling=20,actualBilling='NOT_VERIFIED'))
    assert all(x['cumulativeWithConservativeReserves']<=20 for x in budget)
    (out / 'accounting-complete.json').write_text(json.dumps(dict(transport=transport,budget=budget,naturalAndInjectedDenominatorsSeparate=True,diagnosticExcluded=True,unknownReserveIsNotAnInvoice=True),ensure_ascii=False,indent=2),encoding='utf-8')
    dependence=[]
    for d in m['dependence']:
        dependence.append(dict(stratum=d['stratum'],endpoint=d['endpoint'],n=d['pooled']['n'],pooledJoint=d['pooled']['observedJoint'],pooledIndependent=d['pooled']['independentMarginalProduct'],caseConditionedExcess=d['caseConditionedExcess'],permutationP=d['permutation']['oneSidedExploratoryP'],familyLow=d['familyInterval']['low'],familyHigh=d['familyInterval']['high']))
    texts=['# 第二证据层：控制变量与反例记录',
           '父层60cd5d4与原论文原样保留。本层为32题×4重复、128配对块；自然1,536请求，固定计划审查96请求。题集分为24道执行者标注题与8道DuSQL原文能力边界题；不混成单一总体准确率。原生证据来自固定Java/H2回放，不代表生产部署或真人实验。读回后的资格修正见OBSERVATIONS.md：冻结分数是严格计划标签端点，不自动等于事实答案对错；外部题有入口/拒绝标签冲突，不作为合格外部泛化证明。',
           '第一块六次DeepSeek超时原样纳入；另一次认证GET与一条延迟诊断单列。诊断上限30秒，正式期限仍是5秒；只有一次有界恢复窗口，没有替换难看结果。',
           '## 一致性风险信号',
           table(qualifications,[('stratum','输入层'),('provider','厂商'),('n','提案请求'),('complete','完整返回'),('structureValid','全字段结构合格'),('nativeQualified','原生计划资格'),('nativeEntryBlocked','原生入口未调用planner')]),
           '真实模型调用发生在组件采集层；Java/H2用原始响应回放原生路径，未在线连接模型。若原生入口不调用planner，组件提案不能越过该入口作为产品结果。',
           table(m['risk'], [('stratum','输入层'),('n','配对块'),('bothCorrect','两家正确'),('aOnlyCorrect','仅A正确'),('bOnlyCorrect','仅B正确'),('bothWrong','两家错误'),('agreementN','结构一致'),('pCorrectGivenAgreement','P正确｜一致'),('pWrongGivenAgreement','P错误｜一致'),('disagreementN','不一致'),('pEitherCorrectGivenDisagreement','P至少一家正确｜不一致')]),
           '一致要求完整字段结构相等，仅消除JSON字段顺序/空白表示差异；不补字段、不忽略筛选或reason。结构不一致可含协议/传输不可用，不能全部称为语义分歧。预冻结oracle对QUERY匹配全部指定字段，对CLARIFY仅判action；澄清处理正确不证明reason解释完整或正确。metrics.json另保留原生资格及共同遗漏代理标签。',
           '## 联合错误与同题比较',
           table(dependence,[('stratum','输入层'),('endpoint','端点'),('n','样本'),('pooledJoint','联合错误'),('pooledIndependent','混合边际乘积'),('caseConditionedExcess','逐题平均差'),('permutationP','探索性置换P'),('familyLow','题族区间下界'),('familyHigh','上界')]),
           '混合边际乘积受题目难度影响；主要比较保留同题重复，按题族整体bootstrap。每题只有四次重复，探索性量不建立普遍统计依赖或独立用户推断；常量共同错误的同题差可为零，不能因此宣布不存在稳定偏置。',
           '## 自审、互审与等调用预算',
           table(m['groups'], [('stratum','输入层'),('group','组'),('n','块'),('expectedQueries','应查询'),('semanticPlanCorrect','计划匹配oracle'),('correctQueryOrScope','匹配的查询/范围提议'),('correctPublic','匹配的公开执行'),('pendingScope','待范围确认'),('wrongAutomatic','公开执行但计划不匹配'),('abstentions','策略弃权'),('meanLogicalCost','逻辑均价¥'),('medianLogicalSerialMs','逻辑串行中位ms')]),
           '正确处理包含合法澄清/策略弃权，不能冒充任务执行成功；个人确认仍是控制入口，模拟接受不代表真人识别。B/C/D复用同一PA/PB，C/D只有否决权，不能新增正确答案；成本/延迟是从共享原始调用复算的逻辑策略成本，不是在线部署端到端耗时。',
           '## B后审查的净效应',
           table(opportunities,[('stratum','输入层'),('wrongQueryableOpportunities','B放行的错误查询机会'),('correctQueryableOpportunities','B放行的正确查询'),('correctClarifyCandidates','B的正确澄清候选')]),
           table(m['reviewNet'], [('stratum','输入层'),('group','组'),('newWrongQueryablePlansVetoed','新增阻断错误查询候选'),('newCorrectQueriesBlocked','新增阻断正确查询'),('correctClarifyRejudged','正确澄清再判'),('newAbstentions','新增弃权'),('netCountUnweighted','错误阻断−正确阻断')]),
           table(breakdown,[('stratum','输入层'),('group','组'),('explicit_wrong','明确否决错误'),('explicit_correct','明确否决正确'),('unavailable_wrong','仅不可用阻断错误'),('unavailable_correct','仅不可用阻断正确'),('mixed','否决与不可用并存')]),
           '先看B留下多少错误机会，再解释审查增益；零机会不能被解释为reviewer没有抓错能力。净计数没有把不同错误赋予等同现实损失的资格；不可用导致弃权也不算reviewer成功识别语义错误。正确CLARIFY再次收到CLARIFY不记为正确查询误杀。',
           '## 固定错误挑战（不混入自然一致率）',
           table(m['challenge'], [('provider','审核者'),('label','注入标签'),('n','调用'),('nativeQualifiedCandidates','候选原生资格'),('accept','ACCEPT'),('clarify','CLARIFY'),('reject','REJECT'),('unavailable','不可用/非法审查'),('correctQueryBlocked','正确QUERY明确阻断')]),
           '16个正确/错误计划在调用前冻结并经原生回放；PA=PB是实验注入，不是两模型自然共同误解。此表衡量审查对指定错误的敏感性，不估计这些错误的自然发生率。',
           '## 全部调用与费用',
           table(transport,[('stage','阶段'),('provider','厂商'),('n','请求身份'),('SUCCESS','SUCCESS'),('TIMEOUT','TIMEOUT'),('knownCost','已知保守估价¥'),('unknown','缺用量')]),
           table(budget,[('provider','厂商'),('newRequestIdentities','新请求身份'),('cumulativeKnownEstimate','累计已知估价¥'),('cumulativeWithConservativeReserves','含未知reserve¥'),('ceiling','累计上限¥')]),
           '实际账单NOT_VERIFIED；按公开最高输入价保守估算，未知每次另留¥0.01，这是预算reserve而非实际扣款保证。认证GET无生成用量，不计生成请求。',
           '## 结论边界与后续',
           '本层只增加冻结分布的描述性/探索性证据。不同模型档位、跨日稳定、独立盲标均NOT_RUN；真人为PENDING_HUMAN_STUDY；生产MySQL、真实部署、真实用户收益仍NOT_PROVEN。新结果无论支持、推翻或无法判断，都不回写原观察记录。控制项与替代解释见CONTROL-LEDGER.md。']
    (out / 'RESULTS.md').write_text('\n\n'.join(texts)+'\n',encoding='utf-8')
    # A compact evidence screen; numerical tables are the primary record.
    risk_html=''.join('<tr>'+''.join('<td>'+html.escape(str(d.get(k)))+'</td>' for k in ['stratum','n','agreementN','pCorrectGivenAgreement','pWrongGivenAgreement'])+'</tr>' for d in m['risk'])
    review_html=''.join('<tr>'+''.join('<td>'+html.escape(str(d.get(k)))+'</td>' for k in ['stratum','group','newWrongQueryablePlansVetoed','newCorrectQueriesBlocked','correctClarifyRejudged'])+'</tr>' for d in m['reviewNet'])
    page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>第二证据层 · 控制变量</title><style>body{font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif;background:#f5f2eb;color:#23312e;margin:36px auto;max-width:1180px}h1{font-size:34px;margin-bottom:4px}h2{font-size:23px}.muted{color:#64716d}.cards{display:flex;gap:16px;margin:24px 0}.card,section{background:#fff;border:1px solid #dcded6;border-radius:12px;padding:20px}.card{flex:1}.value{font-size:32px;font-weight:700}section{margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #e4e7e0;text-align:left;padding:9px}.note{border-left:4px solid #a34e3f;padding:12px 18px;background:#f5ece3}small{color:#66736d}</style><h1>第二证据层 · 控制变量与反例</h1><div class="muted">开放解释 → 完整协议 → 一致性 / 审查 → 有限能力 → 范围确认 → 事实</div><div class="cards"><div class="card"><div class="value">128</div>配对块 · 32题 × 4重复</div><div class="card"><div class="value">1,536 + 96</div>自然请求 + 固定计划审查</div><div class="card"><div class="value">6</div>首批超时保留 · 未替换</div></div><section><h2>一致性作为风险信号</h2><table><tr><th>输入层</th><th>配对块</th><th>结构一致</th><th>P正确｜一致</th><th>P错误｜一致</th></tr>'''+risk_html+'''</table><small>执行者标签题与DuSQL原文能力边界题分开；不是独立真人样本。</small></section><section><h2>B一致性筛选后的审查净效应</h2><table><tr><th>输入层</th><th>策略</th><th>新增阻断错误查询候选</th><th>新增阻断正确QUERY</th><th>正确CLARIFY再判</th></tr>'''+review_html+'''</table><small>仅否决，不修计划；不可用与明确审查判决另列原始表。</small></section><div class="note">一致性是筛选信号；审查也是可错判断源；范围确认是执行控制点。没有一层证明“这一定就是用户原意”。</div><section><h2>资格边界</h2><p>固定Java/H2原生回放 · 原论文60cd5d4不改 · 诊断不混入语义分母</p><p>跨日 / 不同档位 / 独立盲标：NOT_RUN<br>真人范围确认：PENDING_HUMAN_STUDY<br>生产环境与真人纠错收益：NOT_PROVEN</p><small>完整表、费用及失败记录以RESULTS.md、CSV、JSON和原始请求为准。截图只是旁证。</small></section></html>'''
    page=page.replace('执行者标签题与DuSQL原文能力边界题分开；不是独立真人样本。','DuSQL外部控制存在入口/标签冲突：CONFOUNDED，不作泛化结论。表中正确率是严格计划标签匹配，不是事实答案准确率。')
    page=page.replace('P正确｜一致','P匹配oracle｜一致').replace('P错误｜一致','P不匹配｜一致')
    challenge_html=''
    for provider in ('deepseek','qwen'):
        wrong=next(x for x in m['challenge'] if x['provider']==provider and x['label']=='wrong')
        good=next(x for x in m['challenge'] if x['provider']==provider and x['label']=='correct')
        challenge_html+=f'<tr><td>{provider}</td><td>{wrong["clarify"]+wrong["reject"]}/{wrong["n"]}</td><td>{wrong["accept"]}</td><td>{good["correctQueryBlocked"]}</td></tr>'
    challenge_section='<section><h2>给审查留下真实错误机会</h2><table><tr><th>审核者</th><th>固定错误非ACCEPT</th><th>漏过错误</th><th>正确QUERY明确误杀</th></tr>'+challenge_html+'</table><small>八种固定错误计划各三次；人为设置一致错误，不估计自然共错频率。千问三次漏过同一“相机且未归还 → 全部MY_LOANS”条件遗漏；执行层仍停在范围确认。</small></section>'
    page=page.replace('<div class="note">',challenge_section+'<div class="note">')
    (out / 'dashboard.html').write_text(page,encoding='utf-8')
    print('Result tables and accounting written; old paper untouched')

if __name__ == '__main__': main()
