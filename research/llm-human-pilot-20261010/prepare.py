"""Freeze a controlled UI pilot, never simulate a participant."""
import hashlib,json,pathlib,random
R=pathlib.Path(__file__).resolve().parent
def main():
 assert not (R/'tasks.json').exists(),'Keep the first candidate'
 tasks=[]
 conditions=[
 ('Q-camera','青野','请查当前账号最多10条借用记录，不按器材、日期或状态筛选。','只查当前账号相机的借用记录，最多10条。','我的全部借用记录','当前账号的全部借用记录，最多展示10条。不会按器材、日期或状态筛选。'),
 ('Q-today','青野','请查当前账号最多10条借用记录，所有日期和器材都包含。','只查当前账号今天的借用记录，最多10条。','我的全部借用记录','当前账号的全部借用记录，最多展示10条。不会按器材、日期或状态筛选。'),
 ('Q-cancel','青野','请查当前账号未取消的报名记录，最多10条，不需要额外筛选。','只查当前账号已经取消的报名记录，最多10条。','我的未取消报名记录','当前账号未取消的报名记录，最多展示10条。不接受额外的活动名称、日期或状态筛选。'),
 ('L-unreturned','图书馆','查当前账号的借阅记录，不限书名、日期或归还状态，最多20条。','只查当前账号尚未归还的借阅记录，最多20条。','我的借阅记录','当前账号的借阅记录 · 全部日期 · 全部图书 · 全部归还状态 · 最多20条'),
 ('L-title','图书馆','查当前账号所有图书的借阅记录，不限日期或归还状态，最多20条。','只查当前账号《程序基础》的借阅记录，最多20条。','我的借阅记录','当前账号的借阅记录 · 全部日期 · 全部图书 · 全部归还状态 · 最多20条'),
 ('L-date','图书馆','查当前账号的借阅记录，各日期都包含，不限书名或归还状态，最多20条。','只查当前账号今天的借阅记录，最多20条。','我的借阅记录','当前账号的借阅记录 · 全部日期 · 全部图书 · 全部归还状态 · 最多20条'),
 ]
 for family,system,good,bad,label,scope in conditions:
  for kind,q in [('preserved',good),('omitted',bad)]:
   tasks.append(dict(id=family+'-'+kind,family=family,system=system,question=q,interpretation=label,scope=scope,oracle='ACCEPT' if kind=='preserved' else 'CORRECT',condition=kind))
 random.Random(20261010).shuffle(tasks)
 (R/'tasks.json').write_bytes((json.dumps(tasks,ensure_ascii=False,indent=2)+'\n').encode())
 files={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in ['tasks.json','CONTRACT.md','prepare.py','server.py','index.html']}
 (R/'seal.json').write_bytes((json.dumps(dict(version='human-pilot-v1',participant='P01',n=1,tasks=12,orderSeed=20261010,files=files,independentHumanStudy=False,realDbOrApiAccess=False),ensure_ascii=False,indent=2)+'\n').encode())
 print('Human pilot sealed; 12 tasks, 0 participant responses, 0 API calls')
if __name__=='__main__':main()
