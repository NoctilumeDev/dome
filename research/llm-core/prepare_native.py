import argparse
import json
from pathlib import Path
from core import parse_plan
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['pilot','core']);args=p.parse_args()
    cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))}
    calls=[json.loads(line) for line in (ROOT/f'results/{args.phase}/calls.jsonl').read_text(encoding='utf-8').splitlines()]
    records=[dict(callId=c['callId'],system=c['system'],question=cases[c['caseId']]['question'],rawContent=c['rawContent'],complete=c['complete']) for c in calls if c['role']=='proposal']
    qp=dict(action='QUERY',intent='EQUIPMENT',entity='相机',category=None,timeOption='CURRENT',reason=None)
    bp=dict(action='QUERY',intent='FIND_LOCATION',title='三体',author=None,category=None,publisher=None,keywords=[],availableOnly=None,unreturnedOnly=None,timeOption='ALL',days=None,limit=20,reason=None)
    for system,correct,question in [('qingye',qp,'请帮忙看看相机当前的库存'),('library',bp,'请帮忙看看《三体》的馆藏位置')]:
        mutations={'positive':correct,'foreign-user':dict(correct,userId=3),'missing-field':{k:v for k,v in correct.items() if k!='reason'}}
        for name,raw in mutations.items():records.append(dict(callId=f'CONTROL/{system}/{name}',system=system,question=question,rawContent=json.dumps(raw,ensure_ascii=False),complete=True))
        records.append(dict(callId=f'CONTROL/{system}/transport',system=system,question=question,rawContent='',complete=False))
    records.append(dict(callId='CONTROL/qingye/omitted-private-filter',system='qingye',question='请只查我今天借的相机',rawContent=json.dumps(dict(action='QUERY',intent='MY_LOANS',entity=None,category=None,timeOption='ANY',reason=None)),complete=True))
    records.append(dict(callId='CONTROL/library/omitted-private-filter',system='library',question='请只查我今天借的图书',rawContent=json.dumps(dict(bp,intent='MY_BORROWS',title=None)),complete=True))
    out=ROOT/f'results/{args.phase}/native-input.json';out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print('Native replay inputs:',len(records))
if __name__=='__main__':main()
