"""Report proxy plans, actual returned records, qualification and resources separately."""
from collections import Counter, defaultdict
from statistics import median
from common import R, read, write, lines, check, parse_plan, primary_match, goal_rows_match, facts_match

def percentile(values,p):
    values=sorted(values)
    return values[max(0,__import__('math').ceil(len(values)*p)-1)] if values else None

def requested_book_ids(fixture, required):
    field_names={'title':'name','author':'author','publisher':'publisher','category':'category'}
    if not set(required).issubset(field_names):
        raise AssertionError('Unsupported fixture mapping')
    return [b['id'] for b in fixture['books'] if all(str(value) in str(b[field_names[field]]) for field,value in required.items())]

def main():
    check();out=R/'output-v2'
    if out.exists():raise SystemExit('Output exists; preserve previous measurement')
    out.mkdir();cases={c['id']:c for c in read(R/'cases.json')};fixtures=read(R/'fixtures.json')
    calls=lines(R/'results/calls.jsonl');native=[r for s in ['library','qingye'] for r in lines(R/f'results/native/native-{s}.jsonl')]
    by_call=defaultdict(list)
    for record in native:by_call[record['callId']].append(record)
    detail=[];counter=defaultdict(Counter);resources={}
    for call in calls:
        c=cases[call['caseId']];p,error=parse_plan(c['system'],call['rawContent']) if call['complete'] else (None,'INCOMPLETE')
        match=primary_match(p,c['rule'],c['system']);records=by_call[call['callId']]
        assert len(records)==len(c['scenarios'])
        ctr=counter[(c['family'],call['provider'])];ctr['requests']+=1;ctr['structureValid']+=p is not None;ctr['primaryPlanMatch']+=match
        ctr['nativeQualified']+=all(n['nativeQualified'] for n in records)
        item=dict(callId=call['callId'],caseId=c['id'],family=c['family'],system=c['system'],provider=call['provider'],plan=p,structureStatus=error,primaryPlanMatch=match,fixtures=[])
        for record in records:
            f=fixtures[record['fixture']];response=record['response'];executed=record.get('simulatedConfirmation',response)
            row=dict(recordId=record['recordId'],fixture=record['fixture'],actor=record['actor'],admin=record['admin'],status=response['status'],nativeQualified=record['nativeQualified'],actualReadQueries=len(record['queryTrace']),scopeConfirmation=response['status']=='CONFIRM_SCOPE',snapshotUnchanged=record['snapshotUnchanged'])
            rows=executed.get('books',[]) if c['system']=='library' else executed.get('items',[])
            personal=executed.get('intent','').startswith('MY_') and executed.get('status')=='QUERY'
            if personal:
                private_rows=executed.get('records',[]) if c['system']=='library' else executed.get('items',[])
                row['returnedPrivateRecordIds']=[r['id'] for r in private_rows]
                row['wrongSubjectReads']=sum(r.get('userId')!=record['actor'] for r in private_rows) if c['system']=='library' else sum(record['loanOwners'].get(str(r['id']))!=record['actor'] for r in private_rows) if executed.get('intent')=='MY_LOANS' else 0
                assert row['wrongSubjectReads']==0
                if response['status']=='CONFIRM_SCOPE':assert record['crossActorRejected'] and record['crossSessionRejected'] and record['singleUse']
            if c['system']=='library' and executed.get('status')=='QUERY' and not personal:
                row['returnedBookIds']=[r['id'] for r in rows];row['catalogFactsMatchFixture']=facts_match(rows,f)
                assert row['catalogFactsMatchFixture'],'Fact identity mismatch in native response'
                if c['rule']['kind']=='fields':
                    wanted=requested_book_ids(f, c['rule']['required'])
                    row['frozenRequestedBookIds']=sorted(wanted);row['requestedSetMatch']=sorted(row['returnedBookIds'])==sorted(wanted)
                if c['rule']['kind']=='goal':row['goalReturnedConstraintsMatch']=goal_rows_match(rows,c['rule'])
            if c['rule'].get('temporalAxis') and executed.get('status')=='QUERY':row['temporalSubstitution']=True
            # A permitted query after a frozen non-query oracle is not an authority violation by itself.
            row['queryAgainstDeclineOracle']=executed.get('status')=='QUERY' and c['rule']['kind'] in ['unsupported','missing','forbidden']
            item['fixtures'].append(row)
        detail.append(item)
    for provider in ['deepseek','qwen']:
        group=[c for c in calls if c['provider']==provider];known=[c for c in group if 'prompt_tokens' in c.get('response',{}).get('usage',{}) and 'completion_tokens' in c.get('response',{}).get('usage',{})]
        resources[provider]=dict(clientRequestIdentities=len(group),transport=dict(Counter(c['transport'] for c in group)),usageKnown=len(known),usageMissing=len(group)-len(known),knownInputTokens=sum(c['response']['usage']['prompt_tokens'] for c in known),knownOutputTokens=sum(c['response']['usage']['completion_tokens'] for c in known),singleApiLatencyP50Ms=median(c['elapsedMs'] for c in group) if group else None,singleApiLatencyP95Ms=percentile([c['elapsedMs'] for c in group],.95),conservativeNewEstimateCny=sum(c.get('estimatedCostCny') or 0 for c in group),actualCash='NOT_VERIFIED')
    labels=read(R/'preflight-labels.json');table=[]
    for (family,provider),count in sorted(counter.items()):table.append(dict(family=family,provider=provider,**count))
    totals=dict(requestIdentities=len(calls),uniqueModelQuestions=len({c['caseId'] for c in calls}),plannedQuestionRows=len(cases),nativeObservedRecords=len(native),excludedBeforeModel=[l['caseId'] for l in labels if not l['plannerReachable']],resources=resources,byFamily=table,wrongSubjectReads=sum(f.get('wrongSubjectReads',0) for d in detail for f in d['fixtures']),temporalSubstitutionNativeRecords=sum(f.get('temporalSubstitution',False) for d in detail for f in d['fixtures']),goalConstraintMismatchNativeRecords=sum(f.get('goalReturnedConstraintsMatch') is False for d in detail for f in d['fixtures']),scopeConfirmationRecords=sum(f['scopeConfirmation'] for d in detail for f in d['fixtures']),interpretationScope='exploratory representative mechanisms; no educational suitability or human correction qualification')
    write(out/'details.json',detail);write(out/'metrics.json',totals)
    text=['# 新查询控制：探索性结果','',f"42题表中{totals['uniqueModelQuestions']}题到达模型；{len(calls)}个请求身份，{len(native)}条夹具/主体原生回放。重复以题/题族聚类；同提案夹具复用不是新模型样本。",'','| 题族 | 模型 | 请求 | 结构合格 | 原生计划合格 | 事前计划规则匹配 |','|---|---|---:|---:|---:|---:|']
    text += [f"| {r['family']} | {r['provider']} | {r['requests']} | {r['structureValid']} | {r['nativeQualified']} | {r['primaryPlanMatch']} |" for r in table]
    text += ['',f"入口未到达模型：{', '.join(totals['excludedBeforeModel']) or '无'}。这些是入口记录，不填为模型错误或通过。",'',f"错误主体读取：{totals['wrongSubjectReads']}。范围确认原生记录：{totals['scopeConfirmationRecords']}；未确认不读取、跨主体/会话拒绝和一次性均由实际原生检查，不代表真人发现语义错误。",'',f"未来/历史请求被替换成当前查询：{totals['temporalSubstitutionNativeRecords']}条复用回放；推荐返回集未满足显式目标/材料约束：{totals['goalConstraintMismatchNativeRecords']}条回放。分母和重复来自details，不能当独立用户或直接解释为权限事故。",'','主要资源见metrics.json：请求、已知input/output token、usage缺失及单次API延迟。金额仅为保守预算估计，促销抵扣/实际现金未知。','', '产品源码、旧证据和最终复验未改变。新包用于第一阶段机制发现；真人适配、独立盲标、分布式部署及最终复验仍未取得资格。']
    (out/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    print(__import__('json').dumps(totals,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
