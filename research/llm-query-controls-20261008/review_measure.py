"""Same-proposal veto ablation, actual residual-query opportunities and false vetoes."""
from collections import Counter
from statistics import median
from common import R, read, write, lines, parse_plan
from review_collect import review_check
from core import canonical, review

def main():
    review_check();out=R/'review-output'
    if out.exists():raise SystemExit('Review measurement coordinate exists')
    out.mkdir();props=lines(R/'results/calls.jsonl');reviews=lines(R/'review-results/calls.jsonl');d={x['callId']:x for x in read(R/'output-v2/details.json')}
    pmap={x['callId']:x for x in props};rmap={(x['candidateCallId'],x['reviewer']):x for x in reviews};blocks={}
    for p in props:blocks.setdefault((p['caseId'],p['repeat']),{})[p['provider']]=p
    strategies={s:Counter() for s in ['B','C:a','C:b','D']};latencies={s:[] for s in strategies};costs={s:[] for s in strategies};details=[];self_counts={'deepseek':Counter(),'qwen':Counter()}
    def usable(cid):return all(f['nativeQualified'] for f in d[cid]['fixtures'])
    def candidate_query(cid):return usable(cid) and d[cid]['plan'] is not None and d[cid]['plan']['action']=='QUERY' and any(f['status'] in ['QUERY','CONFIRM_SCOPE'] for f in d[cid]['fixtures'])
    def quality(cid):return d[cid]['primaryPlanMatch'] and all(f.get('requestedSetMatch',True) and f.get('goalReturnedConstraintsMatch',True) for f in d[cid]['fixtures'])
    def decision(cid,slot):
        r=rmap[(cid,slot)];return review(r['rawContent']) if r['complete'] else 'UNAVAILABLE'
    for (case,repeat),pool in sorted(blocks.items()):
        a=pool['deepseek'];b=pool['qwen'];pa=d[a['callId']]['plan'];pb=d[b['callId']]['plan']
        eq=pa is not None and pb is not None and canonical(pa)==canonical(pb)
        admissible=eq and usable(a['callId']) and usable(b['callId'])
        query=admissible and candidate_query(a['callId']);correct=query and quality(a['callId']);wrong=query and not correct
        correct_clarify=admissible and pa['action']=='CLARIFY' and quality(a['callId'])
        jobs={'C:a':[(a['callId'],'b')],'C:b':[(b['callId'],'a')],'D':[(a['callId'],'b'),(b['callId'],'a')],'B':[]}
        row=dict(caseId=case,repeat=repeat,structuralAgreement=eq,nativeAdmissibleAgreement=admissible,BqueryOpportunity=query,BwrongQueryOrScopeOpportunity=wrong,BcorrectQueryOrScope=correct,BcorrectClarify=correct_clarify,reviewDecisions={cid+'/'+slot:decision(cid,slot) for cid,slot in [(a['callId'],'a'),(a['callId'],'b'),(b['callId'],'a'),(b['callId'],'b')]},strategies={})
        for s,jobs_s in jobs.items():
            allow=admissible and all(decision(cid,slot)=='ACCEPT' for cid,slot in jobs_s);veto=admissible and not allow;count=strategies[s]
            count['blocks']+=1;count['admissibleCandidates']+=allow;count['correctQueryOrScopePassed']+=correct and allow;count['wrongQueryOrScopePassed']+=wrong and allow
            count['incrementalWrongQueryOrScopeBlocked']+=wrong and veto;count['incrementalCorrectQueryOrScopeBlocked']+=correct and veto;count['correctClarifyVetoed']+=correct_clarify and veto
            count['publicCorrectAutomaticExecution']+=correct and allow and any(f['status']=='QUERY' for f in d[a['callId']]['fixtures'])
            count['wrongPublicAutomaticQuery']+=wrong and allow and any(f['status']=='QUERY' for f in d[a['callId']]['fixtures'])
            latencies[s].append(a['elapsedMs']+b['elapsedMs']+sum(rmap[(cid,slot)]['elapsedMs'] for cid,slot in jobs_s))
            costs[s].append((a.get('estimatedCostCny') or 0)+(b.get('estimatedCostCny') or 0)+sum(rmap[(cid,slot)].get('estimatedCostCny') or 0 for cid,slot in jobs_s))
            row['strategies'][s]=dict(allowed=allow,incrementalVeto=veto)
        for provider,p,slot in [('deepseek',a,'a'),('qwen',b,'b')]:
            cid=p['callId'];allow=decision(cid,slot)=='ACCEPT';sc=self_counts[provider];sc['candidates']+=1
            if candidate_query(cid):
                good=quality(cid);sc['wrongQueryOrScopeBaseline']+=not good;sc['correctQueryOrScopeBaseline']+=good
                sc['wrongQueryOrScopeBlocked']+=not good and not allow;sc['correctQueryOrScopeBlocked']+=good and not allow
        details.append(row)
    metrics=dict(pairedBlocks=len(blocks),uniqueQuestions=len({k[0] for k in blocks}),proposalRequestIdentities=len(props),reviewRequestIdentities=len(reviews),structuralAgreementBlocks=sum(d['structuralAgreement'] for d in details),admissibleAgreementBlocks=sum(d['nativeAdmissibleAgreement'] for d in details),BresidualWrongOpportunities=sum(d['BwrongQueryOrScopeOpportunity'] for d in details),BcorrectQueryOrScope=sum(d['BcorrectQueryOrScope'] for d in details),strategies={s:dict(c,logicalSerialLatencyMedianMs=median(latencies[s]),logicalMeanListPriceEstimateCny=sum(costs[s])/len(costs[s])) for s,c in strategies.items()},selfReview={s:dict(c) for s,c in self_counts.items()},scope='Exploratory add-on on all retained new questions, sealed after proposal collection; clustered repeated blocks, veto-only review, no deployment utility or independent blind evaluation')
    write(out/'metrics.json',metrics);write(out/'details.json',details)
    text=['# 全提案审查对照','',f"全部{metrics['uniqueQuestions']}题、{metrics['pairedBlocks']}配对重复块复用234原提案；468次新审查。结构一致{metrics['structuralAgreementBlocks']}块、原生合格一致{metrics['admissibleAgreementBlocks']}块。",'',f"B留出的错误QUERY/范围提议机会：{metrics['BresidualWrongOpportunities']}，属于当前探索性分布，不能从全体调用数推部署错误基率。",'','| 策略 | 新增拦错误QUERY/范围提议 | 新增挡正确QUERY/范围提议 | 正确CLARIFY被再次弃权 | 剩余错误 | 逻辑串行中位ms |','|---|---:|---:|---:|---:|---:|']
    for s,c in metrics['strategies'].items():text.append(f"| {s} | {c.get('incrementalWrongQueryOrScopeBlocked',0)} | {c.get('incrementalCorrectQueryOrScopeBlocked',0)} | {c.get('correctClarifyVetoed',0)} | {c.get('wrongQueryOrScopePassed',0)} | {c['logicalSerialLatencyMedianMs']} |")
    text+=['','审查只有否决权，不改答案。私有范围提议被拦与错误自动公开查询被拦分开看；未确认不读的机制仍独立成立。正确CLARIFY再弃权不是正确QUERY误杀。此处串行时延由独立调用测值相加，仅是策略逻辑量，不是在线端到端测试。共享提案只在实际采集账计一次，策略逻辑成本不可累加成真实现金。','', '加测在完整提案冻结后事前封印，所有39题都纳入，没有选错题子集；仍由同一执行者设计/评分，具有探索性。原单模型结果与首败不回写。本包未加新的等预算重规划，不能把此分布的审查筛选结果写成总体采样优势。']
    (out/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    print(__import__('json').dumps(metrics,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
