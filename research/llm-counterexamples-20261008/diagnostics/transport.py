"""Bounded transport diagnosis; excluded from semantic experiment denominators."""
import getpass, warnings, sys, json, hashlib, http.client, ssl, time
from pathlib import Path
from datetime import datetime, timezone
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R.parent/'llm-core'))
from run import request,estimate_cost,append
if not sys.stdin.isatty():raise SystemExit('Non-echo console required')
warnings.simplefilter('error',getpass.GetPassWarning)
keys=json.loads(getpass.getpass('CREDENTIAL_INPUT: '))
plan=json.loads((R/'plan.json').read_text())
out=R/'diagnostics/transport-result.json'
assert not out.exists(),'Never overwrite a diagnostic observation'
records=[]
try:
 p=plan['providers']['a'];t=time.monotonic()
 c=http.client.HTTPSConnection('api.deepseek.com',timeout=5,context=ssl.create_default_context())
 try:
  c.request('GET','/models',headers={'Authorization':'Bearer '+keys['deepseek']})
  res=c.getresponse();body=json.loads(res.read())
  records.append(dict(id='diagnostic/auth/1',method='GET /models',httpStatus=res.status,elapsedMs=round((time.monotonic()-t)*1000),models=[x.get('id') for x in body.get('data',[])],errorCode=body.get('error',{}).get('code')))
 except Exception as e:records.append(dict(id='diagnostic/auth/1',errorClass=type(e).__name__,elapsedMs=round((time.monotonic()-t)*1000)))
 finally:c.close()
 if records[-1].get('httpStatus')==200:
  first=json.loads((R/'results/core/calls.jsonl').read_text().splitlines()[0]);body=first['request']
  observed=request(p['url'],keys['deepseek'],body,30000)
  rec=dict(callId='diagnostic/latency/1',requestHash=first['requestHash'],request=body,provider='deepseek',deadlineMs=30000,formalDeadlineMs=5000,scope='TRANSPORT_ONLY_NOT_SEMANTIC_DENOMINATOR',**observed)
  rec['estimatedCostCny']=estimate_cost(rec,p);records.append(rec)
  print(json.dumps({k:rec.get(k) for k in ['callId','transport','httpStatus','errorCode','errorClass','elapsedMs','estimatedCostCny']},ensure_ascii=False),flush=True)
finally:
 keys.clear();out.write_text(json.dumps(dict(observedAt=datetime.now(timezone.utc).isoformat(),purpose='Separate transport diagnosis, not resume or replacement of timed-out request identities',records=records),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records[0],ensure_ascii=False),flush=True)
