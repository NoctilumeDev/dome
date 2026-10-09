"""Paired whole-pipeline window description; no new oracle or repaired candidates."""
import json
import statistics
from collections import Counter
from datetime import datetime
from common import R, ORIGIN, read, write, lines, check, budget_state
from core import review


def main():
    check(); out = R / 'comparison'
    assert not out.exists(), 'Preserve previous derived comparison'
    cases = read(R / 'cases.json')
    windows = {}
    for label, root in [('day0', ORIGIN), ('day1', R)]:
        calls = lines(root / 'results/calls.jsonl'); reviews = lines(root / 'review-results/calls.jsonl')
        assert len(calls) == 234 and len(reviews) == 468
        props = read(root / 'output-v2/details.json')
        blocks = read(root / 'review-output/details.json')
        pmap = {p['callId']: p for p in props}
        amap = {(c['caseId'], c['repeat'], c['provider']): c for c in calls}
        dmap = {(d['caseId'], c['repeat'], d['provider']): d for d in props for c in [next(v for v in calls if v['callId'] == d['callId'])]}
        strategies = {}
        for strategy in ('B', 'C:a', 'C:b', 'D'):
            stats = Counter()
            for block in blocks:
                a = amap[(block['caseId'], block['repeat'], 'deepseek')]; d = pmap[a['callId']]
                allowed = block['strategies'][strategy]['allowed']; veto = block['strategies'][strategy]['incrementalVeto']
                stats['remainingWrongPublic'] += block['BwrongQueryOrScopeOpportunity'] and allowed and any(f['status'] == 'QUERY' for f in d['fixtures'])
                stats['remainingWrongPrivateScope'] += block['BwrongQueryOrScopeOpportunity'] and allowed and any(f['status'] == 'CONFIRM_SCOPE' for f in d['fixtures'])
                stats['newWrongBlocked'] += block['BwrongQueryOrScopeOpportunity'] and veto
                stats['newCorrectQueryOrScopeBlocked'] += block['BcorrectQueryOrScope'] and veto
                stats['correctClarifyRevetoed'] += block['BcorrectClarify'] and veto
                stats['correctRejectRevetoed'] += bool(block['nativeAdmissibleAgreement'] and d['plan'] and d['plan']['action'] == 'REJECT' and d['primaryPlanMatch'] and veto)
            source_stats = read(root / 'review-output/metrics.json')['strategies'][strategy]
            assert stats['remainingWrongPublic'] == source_stats.get('wrongPublicAutomaticQuery', 0)
            assert stats['newWrongBlocked'] == source_stats.get('incrementalWrongQueryOrScopeBlocked', 0)
            assert stats['newCorrectQueryOrScopeBlocked'] == source_stats.get('incrementalCorrectQueryOrScopeBlocked', 0)
            strategies[strategy] = dict(stats, logicalSerialMedianMs=source_stats['logicalSerialLatencyMedianMs'], logicalMeanEstimatedCny=source_stats['logicalMeanListPriceEstimateCny'])
        resources = {}
        for provider in ('deepseek', 'qwen'):
            physical = [c for c in calls + reviews if c['provider'] == provider]
            known = [c for c in physical if 'prompt_tokens' in c.get('response', {}).get('usage', {}) and 'completion_tokens' in c.get('response', {}).get('usage', {})]
            resources[provider] = dict(requests=len(physical), transport=dict(Counter(c['transport'] for c in physical)), usageMissing=len(physical)-len(known), inputTokens=sum(c['response']['usage']['prompt_tokens'] for c in known), outputTokens=sum(c['response']['usage']['completion_tokens'] for c in known), apiMedianMs=statistics.median(c['elapsedMs'] for c in physical), responseModels=sorted({str(c.get('response', {}).get('model')) for c in physical}), estimatedNewCny=sum(c['estimatedCostCny'] if c['estimatedCostCny'] is not None else .05 for c in physical))
        windows[label] = dict(proposalCalls=calls, reviewCalls=reviews, proposalMap=dmap, blocks=blocks,
                              strategies=strategies, resources=resources,
                              primaryPlanMatches={p:sum(d['primaryPlanMatch'] for d in props if d['provider']==p) for p in ('deepseek','qwen')},
                              nativeQualifiedProposals={p:sum(all(f['nativeQualified'] for f in d['fixtures']) for d in props if d['provider']==p) for p in ('deepseek','qwen')},
                              reviewerFormats=dict(Counter(review(c['rawContent']) if c['complete'] else 'UNAVAILABLE' for c in reviews)),
                              proposalSummary=read(root / 'results/summary.json'), reviewSummary=read(root / 'review-results/summary.json'))
    paired=[]
    for key, d0 in windows['day0']['proposalMap'].items():
        d1=windows['day1']['proposalMap'][key]
        paired.append(dict(caseId=key[0],repeat=key[1],provider=key[2],
                           day0=dict(primaryPlanMatch=d0['primaryPlanMatch'],structure=d0['structureStatus'],qualified=all(f['nativeQualified'] for f in d0['fixtures'])),
                           day1=dict(primaryPlanMatch=d1['primaryPlanMatch'],structure=d1['structureStatus'],qualified=all(f['nativeQualified'] for f in d1['fixtures']))))
    gap={stage:(datetime.fromisoformat(windows['day1'][stage+'Summary']['startedAt'])-datetime.fromisoformat(windows['day0'][stage+'Summary']['finishedAt'])).total_seconds() for stage in ('proposal','review')}
    assert min(gap.values()) >= 86400
    out.mkdir()
    write(out/'paired-proposals.json',paired)
    compact={k:{n:v for n,v in w.items() if n not in ['proposalCalls','reviewCalls','proposalMap','blocks']} for k,w in windows.items()}
    write(out/'metrics.json',dict(status='COMPLETE_ACTUAL_CROSSDAY_PIPELINE',questions=42,modelReachableQuestions=39,pairedProposalObservations=234,pairedBlocks=117,families=4,gapSeconds=gap,windows=compact,budget=budget_state(),human='PENDING_HUMAN_STUDY',scope='Whole-pipeline service-window comparison, same cases/prompts/parameters; changed new proposals prevent isolating reviewer-time effects'))
    text=['# 新查询包逐题跨日对照','','固定42题，每家每题3重复；39题进入模型。匹配为冻结primaryPlanMatch代理规则，不替代原生资格、实际返回集或用户原意。重复和多夹具不是独立用户。','','| 题ID | 题族 | DeepSeek day0→day1 | 千问 day0→day1 |','|---|---|---:|---:|']
    for c in cases:
        values=[]
        for provider in ('deepseek','qwen'):
            pp=[p for p in paired if p['caseId']==c['id'] and p['provider']==provider]
            values.append(f"{sum(p['day0']['primaryPlanMatch'] for p in pp)}/3 → {sum(p['day1']['primaryPlanMatch'] for p in pp)}/3" if pp else '入口未达模型')
        text.append('| '+ ' | '.join([c['id'],c['family']]+values)+' |')
    (out/'CASE_TABLE.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    report=['# 新查询与全提案审查：真实跨日重复','','234新提案、468新审查，474原生多夹具/主体回放。冻结v2与review_measure逐字节复用；以下只是同一执行者构造分布的两个服务窗口。','','| 窗口 | 模型 | 冻结计划匹配/117 | 原生资格/117 | input / output token |','|---|---|---:|---:|---|']
    for label,w in windows.items():
        for p in ('deepseek','qwen'):
            u=w['resources'][p];report.append(f"| {label} | {p} | {w['primaryPlanMatches'][p]} | {w['nativeQualifiedProposals'][p]} | {u['inputTokens']} / {u['outputTokens']} |")
    report+=['','| 窗口/策略 | 剩余错误公开 | 剩余错误私人范围 | 新增拦错 | 新挡正确QUERY/范围 | 正确REJECT再否决 | 逻辑串行中位ms |','|---|---:|---:|---:|---:|---:|---:|']
    for label,w in windows.items():
        for s,v in w['strategies'].items():report.append('| '+ ' | '.join(str(x) for x in [label+'/'+s,v['remainingWrongPublic'],v['remainingWrongPrivateScope'],v['newWrongBlocked'],v['newCorrectQueryOrScopeBlocked'],v['correctRejectRevetoed'],v['logicalSerialMedianMs']])+' |')
    report+=['','一致性和审查仍不是语义真值；D只有否决权。正确CLARIFY再澄清、正确REJECT再否决及正确QUERY误挡分别见metrics，不给未定义权重的总体净效用结论。跨窗审查使用新的候选，不能单独归因reviewer时间效应。未增加本分布等预算重规划。','', '资源表是实际物理调用，两家各351；策略逻辑量复用提案，不能累加成实付。Token不是FLOPs；金额仅预算估价，现金/赠送未核。真实起止时间、响应alias、usage缺失和预算见metrics。模拟确认不等于真人收益，IR/CRUD/分布式与最终全量复刻未实施。']
    (out/'RESULTS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='COMPARISON_PASS',gaps=gap,summary={k:dict(matches=w['primaryPlanMatches'],native=w['nativeQualifiedProposals'],strategies=w['strategies'],resources=w['resources']) for k,w in windows.items()},budget=budget_state()),ensure_ascii=False))


if __name__=='__main__':
    main()
