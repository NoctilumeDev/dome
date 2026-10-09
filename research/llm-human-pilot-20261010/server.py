"""Loopback-only task UI; participant alone submits answers, append-only records."""
import hashlib,http.server,json,os,pathlib,secrets,time
from datetime import datetime,timezone
R=pathlib.Path(__file__).resolve().parent
TOKEN=secrets.token_hex(24); TASKS=json.loads((R/'tasks.json').read_text(encoding='utf-8'))
STATE={'started':False,'index':0,'presentedAt':None,'monotonic':None}
def now():return datetime.now(timezone.utc).isoformat()
def append(v):
 d=R/'results';d.mkdir(exist_ok=True)
 with (d/'responses.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
def public():
 task=TASKS[STATE['index']] if STATE['started'] and STATE['index']<len(TASKS) else None
 if task and STATE['presentedAt'] is None:STATE['presentedAt']=now();STATE['monotonic']=time.monotonic()
 return dict(started=STATE['started'],completed=STATE['index'],total=len(TASKS),task={k:v for k,v in task.items() if k in ['id','system','question','interpretation','scope']} if task else None,token=TOKEN)
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,value,status=200):
  b=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path=='/state':self.send(public());return
  if self.path!='/':self.send({'error':'Unknown route'},404);return
  b=(R/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_POST(self):
  try:
   assert self.headers.get('Origin') in [None,'http://127.0.0.1:8762','http://localhost:8762']
   length=int(self.headers.get('Content-Length','0'));assert 0<length<=3000
   body=json.loads(self.rfile.read(length));assert body.get('token')==TOKEN
   if self.path=='/start':
    assert not STATE['started'];STATE['started']=True
    append(dict(event='START',participant='P01',at=now(),protocolSha256=hashlib.sha256((R/'seal.json').read_bytes()).hexdigest()))
   elif self.path=='/answer':
    assert STATE['started'] and STATE['index']<len(TASKS)
    task=TASKS[STATE['index']];assert body['taskId']==task['id']
    assert body['choice'] in ['ACCEPT','CORRECT','UNSURE']
    ms=body.get('elapsedMs');assert isinstance(ms,(int,float)) and 0<=ms<86400000
    append(dict(event='ANSWER',participant='P01',taskId=task['id'],index=STATE['index'],presentedAt=STATE['presentedAt'],submittedAt=now(),choice=body['choice'],note=str(body.get('note',''))[:240],clientElapsedMs=ms,serverElapsedMs=(time.monotonic()-STATE['monotonic'])*1000))
    STATE['index']+=1;STATE['presentedAt']=None;STATE['monotonic']=None
   else:raise AssertionError('Unknown route')
   self.send(public())
  except Exception:self.send({'error':'Submission rejected; existing records retained'},400)
def main():
 seal=json.loads((R/'seal.json').read_text())
 for n,h in seal['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 path=R/'results/responses.jsonl'
 if path.exists():
  prior=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
  STATE['started']=any(x['event']=='START' for x in prior);STATE['index']=sum(x['event']=='ANSWER' for x in prior)
 print('PILOT_READY http://127.0.0.1:8762 ; participant answers='+str(STATE['index']),flush=True)
 http.server.HTTPServer(('127.0.0.1',8762),Handler).serve_forever()
if __name__=='__main__':main()
