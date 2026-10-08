"""Control/conclusion bookkeeping; execution state never becomes claim authority."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 ext=ROOT/'extension/results/core/evaluation-v2/report.json';done=ext.exists()
 ext_status='PASS' if done else 'RUNNING'
 rows=[]
 def row(id,family,name,status,evidence,boundary):rows.append(dict(id=id,family=family,name=name,status=status,evidence=evidence,boundary=boundary))
 row('C01',1,'两家单提案基线','PASS','results/core/calls.jsonl; output/model-table.csv','已知题表观察；不是所有输入的厂商排名')
 row('C02',2,'F2/F3/F4 相同调用数重规划','PASS','results/core/evaluation-v2/decisions.json; output/group-table.csv','匹配调用数，未匹配token/金额；各预算共享采样池')
 row('C02-money',2,'同金额/同token因果对照','NOT_APPLICABLE','plan.json; output/group-table.csv','本文不声称同金额或同计算量优势；如提出该结论须另做')
 row('C03',3,'B 一致性与固定PA/PB复用','PASS','core.py; tests/test_core.py; frozen-core-v2.json','完整结构一致；不证明任意SQL语义等价')
 row('C04',4,'自审、单向和双向审查','NEGATIVE_RESULT','output/group-table.csv; output/review-table.csv','核心B/C/D公开正确执行及错误执行相同；结论限定该题表/时段')
 row('C04-extension',4,'后窗口及新组合题的审查增益','NEGATIVE_RESULT' if done else ext_status,'extension/results/core/evaluation-v2/; extension/output/group-table.csv','B/D未增加正确查询；新旧分层，不能用新题不同难度解释成时间效应')
 row('C05',5,'协议格式与语义目标分账','PASS','output/proposal-ledger.csv; output/model-table.csv; output/examples.json','declaredNonNullTargetMatch仅匹配显式非空目标，不补字段、不证明完整原意')
 row('C05-normalize',5,'规范化不补答案、不删条件','PASS','core.py; tests/test_core.py','只比较原完整字段；两个schema不强行统一')
 row('C06',6,'本地权限与固定只读执行','PASS','results/core/native-v2/; results/engineering-qingye.txt; results/engineering-library.txt','H2及已有角色/确认测试；无生产MySQL、多节点证明')
 row('C06-scope',6,'范围确认机制与实际读查询','PASS','native/*.java; results/core/native-v2/','未确认零开放个人查询；模拟接受不等于真人理解')
 row('C06-human',6,'真人能识别/纠正范围遗漏','NOT_RUN','output/paper.md limitations','需要独立真人交互研究；本文不提出这种收益结论')
 row('C06-entry',6,'第一门实际处置','NEGATIVE_RESULT','output/proposal-ledger.csv; output/examples.json','设备题语义预期CLARIFY却入口REJECT；未按模型错误处理、不修产品')
 row('C07',7,'两业务系统分别执行与读回','PASS','output/group-table.csv (qingye/library); results/core/native-v2/','同开发者同仓库，非独立组织复现')
 row('C07-isolate',7,'单独归因业务域而非协议复杂度','CONFOUNDED','plan.json; prompts/; output/model-table.csv','业务域、能力、字段数和输出上限耦合；本文不作纯域效应归因')
 row('C08-history',8,'133+65历史保留题转入当前原生链路','PASS','history/manifest.json; history/native-*.jsonl','396题/厂商对；固定当前actor/fixture，不是原历史环境完整复刻')
 row('C08-supplement',8,'历史两道补充题的原条件重放','NEEDS_REPEAT','history/manifest.json unpreservedSupplementCoordinates','两个输入×两厂商缺原文，留四个坐标；不根据摘要猜原题')
 row('C08-holdout',8,'16道前瞻语法组合留出题',ext_status,'extension/cases.json; extension/CONTRACT.md; extension/results/core/','核心结果后设计、调用前冻结；模型看不到标签，执行者不是盲标者')
 row('C08-independent',8,'独立标注者未知题族盲评','NOT_RUN','extension/CONTRACT.md','不能凭作者自建题升级为独立泛化；需要另一个独立标注/评阅过程')
 row('C08-repeat',8,'核心三次配对重复','PASS','results/core/blocks.jsonl','重复同题不增加独立用户数；temperature=0不等于确定性')
 row('C08-window',8,'原48题后采集窗口',ext_status,'extension/results/core/calls.jsonl; extension/CONTRACT.md','短间隔重复，顺序重平衡；不归因纯时间、不证明跨日稳定')
 row('C08-days',8,'跨日/模型修订长期稳定','NEEDS_REPEAT','model aliases and recorded timestamps','别名底层权重未冻结；本轮不提出长期稳定结论')
 claims=[
  dict(id='K1',text='核心已知表中，D相较B未增加最终查询质量且增加逻辑成本/时延',requires=['C01','C02','C03','C04','C05','C06','C07'],status='QUALIFIED_WITH_BOUNDARY',scope='144核心块；非所有任务'),
  dict(id='K2',text='本轮原生回放未观察到表改变或未确认开放个人读取',requires=['C06','C06-scope'],status='QUALIFIED_WITH_BOUNDARY',scope='固定H2及负控制；不是普遍安全证明'),
  dict(id='K3',text='跨模型审查有稳定、独立、可泛化增益',requires=['C01','C02','C03','C04-extension','C05','C06','C07','C08-holdout','C08-independent','C08-window','C08-days'],status='NOT_QUALIFIED',scope='核心结果未支持增益；独立标注和长期窗口未完成'),
  dict(id='K4',text='范围确认一定能让真实用户发现遗漏条件',requires=['C06-scope','C06-human'],status='NOT_QUALIFIED',scope='未做真人研究'),
  dict(id='K5',text='一厂商普遍优于另一厂商',requires=['C01','C07-isolate','C08-independent','C08-days'],status='NOT_QUALIFIED',scope='题表选择、协议及别名混杂未消除')]
 data=dict(version='control-ledger-v1',statusMeaning='PASS means declared execution/measurement completed; not every answer correct or broad conclusion true',controls=rows,claims=claims,stopLine='Declared experiment cells completed or explicitly classified; no Cartesian-product expansion. New claims require newly frozen evidence.')
 (ROOT/'CONTROL_LEDGER.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 md='# 控制变量总账与结论资格\n\nPASS 表示该声明范围的实验/核对完成，不表示全部答案正确；NEGATIVE_RESULT 也是合法完成。未跑、混杂、未证明不升级为全覆盖。\n\n|ID|控制族|项目|状态|证据|结论边界|\n|---|---|---|---|---|---|\n'
 for r in rows:md+='|'+'|'.join(str(r[k]).replace('|','/') for k in ('id','family','name','status','evidence','boundary'))+'|\n'
 md+='\n## 结论反向绑定\n\n'
 for c in claims:md+=f"- **{c['id']} · {c['status']}**：{c['text']}。依赖 {', '.join(c['requires'])}。{c['scope']}。\n"
 md+='\n停止线：按声明的控制族收口；缺口留坐标，不靠补测数量凑资格。独立盲标、跨日或真人研究若成为新目标，必须另行冻结合同，不把此表当无限测试教条。\n'
 (ROOT/'CONTROL_LEDGER.md').write_text(md,encoding='utf-8');print('Control ledger updated:',len(rows),'rows; broad claims remain NOT_QUALIFIED')
if __name__=='__main__':main()
