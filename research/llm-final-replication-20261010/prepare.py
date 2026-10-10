"""Offline compilation of the complete retained experimental matrix; no API access."""
import collections, copy, hashlib, json, pathlib, subprocess

R = pathlib.Path(__file__).resolve().parent
REPO = R.parents[1]
BASE = 'd5fecb05cda3c0a443cbfd5020059a096e98ff23'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def digest(v): return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())

SOURCES = [
 ('core','llm-core','results/core/calls.jsonl','paired',None),
 ('extension','llm-core/extension','results/core/calls.jsonl','paired',None),
 ('counterexamples','llm-counterexamples-20261008','results/core/calls.jsonl','paired',None),
 ('challenge','llm-counterexamples-20261008','results/challenge/calls.jsonl','fixed_review',None),
 ('formal','llm-controls-layer3-20261008','results/formal/calls.jsonl','paired',None),
 ('external','llm-controls-layer3-20261008','results/external/calls.jsonl','proposal',None),
 ('tier','llm-controls-layer3-20261008','results/tier/calls.jsonl','proposal',None),
 ('time-day0','llm-controls-layer3-20261008','results/day0/calls.jsonl','proposal',None),
 ('query-day0','llm-query-controls-20261008','results/calls.jsonl','proposal',None),
 ('query-review-day0','llm-query-controls-20261008','review-results/calls.jsonl','pool_review',None),
 ('time-day1','llm-controls-layer3-20261008','results/day1/calls.jsonl','proposal','time-day0'),
 ('query-day1','llm-query-crossday-20261009','results/calls.jsonl','proposal','query-day0'),
 ('query-review-day1','llm-query-crossday-20261009','review-results/calls.jsonl','pool_review','query-review-day0'),
]

def main():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO).decode().strip()==BASE
 assert not (R/'matrix.json').exists(), 'Do not rewrite an existing candidate'
 jobs=[]; suites=[]; old_by={}; lineage={}; estimated=collections.defaultdict(float)
 for name,folder,raw,kind,guard in SOURCES:
  origin=REPO/'research'/folder; plan=read(origin/'plan.json'); rr=rows(origin/raw)
  by={x['callId']:x for x in rr}; assert len(by)==len(rr)
  old_by[name]=by
  for pos,x in enumerate(rr):
   old=x['callId']; cid='FR1/'+name+'/'+old
   assert 'request' in x, (name,old,'missing payload')
   body=copy.deepcopy(x['request']); dependency=None
   if kind=='paired' and x.get('role')=='review':
    block,_,rev,prop=old.rsplit('/',3); dependency='FR1/'+name+'/'+block+'/p/'+prop+'/0'
   elif kind=='pool_review':
    source='query-day1' if name.endswith('day1') else 'query-day0'
    dependency='FR1/'+source+'/'+x['candidateCallId']
   if dependency:
    assert dependency in lineage, ('Review predecessor missing',dependency)
    content=json.loads(body['messages'][-1]['content'])
    assert set(content)=={'question','candidate'}
    assert content['candidate']==lineage[dependency]['rawContent'], ('Original candidate binding differs',cid)
   role='review' if kind in ('fixed_review','pool_review') else x.get('role','proposal')
   slot=next(k for k,v in plan['providers'].items() if v['name']==x['provider'] and v['model']==body['model'])
   job=dict(callId=cid, legacyCallId=old, suite=name, sourceFolder=folder, sourceRaw=raw,
            sourcePosition=pos, sourceRequestHash=digest(body), request=body,
            candidateDependency=dependency, provider=x['provider'], providerSpec=plan['providers'][slot],
            caseId=x['caseId'], system=x['system'], role=role, sourceMetadata={k:v for k,v in x.items() if k in ('repeat','phase','modelSlot','reviewer','challengeId','candidateCallId')},
            deadlineMs=plan['deadlineMs'])
   jobs.append(job); lineage[cid]=x; estimated[x['provider']]+=x.get('estimatedCostCny') or 0
  suites.append(dict(id=name,sourceFolder=folder,sourceRaw=raw,kind=kind,requests=len(rr),
                     sourceSha256=hashlib.sha256((origin/raw).read_bytes()).hexdigest(),
                     guardAfterFinishedSuite=guard, minimumGapSeconds=86400 if guard else 0,
                     sourceTransportCounts=dict(collections.Counter(x['transport'] for x in rr))))
 assert len(jobs)==8220 and len({x['callId'] for x in jobs})==8220
 baseline={'deepseek':9.067387,'qwen':3.19357625}
 manifest=dict(version='final-replication-v1',boundSourceSha=BASE,
   suites=suites,physicalRequests=8220,providerRequests=dict(collections.Counter(x['provider'] for x in jobs)),
   historicalConservativeCny=baseline,hardCumulativePerProviderCny=20,
   forecastFromOriginalObservedCny=dict(estimated),forecastWith15PercentMarginCny={k:v*1.15 for k,v in estimated.items()},
   reserveBeforeEachRequestCny=.10,unknownUsageReserveCny=.05,maximumMissingUsageBeforeStop=3,
   transportStopMinimum=5,transportStopFraction=.2,authenticationStopStatuses=[401,403],automaticRetries=0,
   human='PENDING_HUMAN_STUDY',aliasWeightsFrozen=False,
   exclusions=[{'item':'pilot and transport diagnostics','reason':'Exploration/setup, not final hypothesis comparisons; retained in development workload'},
               {'item':'historical X01/X02 four provider coordinates','reason':'Original input unavailable; NOT_PROVEN_INPUT, no reconstruction from summaries'},
               {'item':'human participants / independent human labels','reason':'PENDING_HUMAN_STUDY'},
               {'item':'IR / CRUD / distributed execution','reason':'Unimplemented future work'}],
   offlineHistoryTransfer=dict(source='research/llm-core/history/native-input.json',records=396,notFreshApiCalls=True),
   moneyQualification='Frozen 2026-10-08 conservative rates; auxiliary budget estimates, not current tariff/cash/promotional allocation',
   resources='Requests, transport/usage missing, input/output tokens and measured API latency separately from logical reuse strategies')
 for k in baseline: assert baseline[k]+estimated[k]*1.15+.10<20, ('Forecast exceeds original budget',k)
 write(R/'matrix.json',manifest)
 (R/'jobs.jsonl').write_bytes((''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in jobs)).encode())
 for s in suites:
  origin=REPO/'research'/s['sourceFolder']; dest=R/'views'/s['id']
  for file in ['cases.json','external-cases.json','plan.json','challenge-plans.json','fixtures.json']:
   if (origin/file).exists(): (dest/file).parent.mkdir(parents=True,exist_ok=True); (dest/file).write_bytes((origin/file).read_bytes())
 write(R/'OFFLINE_PREFLIGHT.json',dict(status='PASS',paidRequests=0,requests=8220,
    allSourcePayloadsAndOrderPreserved=True,allReviewDependenciesBound=True,
    noProtocolRepair=True,sourceRowsIncludeOriginalFailures=True,forecast=manifest['forecastWith15PercentMarginCny']))
 print(json.dumps({'status':'OFFLINE_PASS','requests':8220,'suites':len(suites),'forecast':dict(estimated),'forecastPlusHistorical':{k:baseline[k]+estimated[k] for k in baseline}},ensure_ascii=False))

if __name__=='__main__': main()
