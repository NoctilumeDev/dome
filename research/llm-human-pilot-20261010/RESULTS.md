# 单人范围确认 pilot 记录

P01为已了解研究背景的发起者；12条受控情境，错误比例50%，本地原型，无模型/数据库调用。不是独立盲评或普通用户效果估计。

| 任务 | 系统 | 条件 | 实际选择 | 控制任务匹配 | 客户端用时秒 |
|---|---|---|---|---|---:|
| Q-camera-omitted | 青野 | omitted | CORRECT | True | 41.31 |
| L-title-omitted | 图书馆 | omitted | CORRECT | True | 58.15 |
| L-unreturned-preserved | 图书馆 | preserved | ACCEPT | True | 20.36 |
| L-title-preserved | 图书馆 | preserved | ACCEPT | True | 13.04 |
| L-unreturned-omitted | 图书馆 | omitted | ACCEPT | False | 69.07 |
| Q-today-preserved | 青野 | preserved | ACCEPT | True | 17.57 |
| L-date-preserved | 图书馆 | preserved | ACCEPT | True | 21.21 |
| L-date-omitted | 图书馆 | omitted | CORRECT | True | 23.23 |
| Q-cancel-preserved | 青野 | preserved | ACCEPT | True | 23.33 |
| Q-camera-preserved | 青野 | preserved | ACCEPT | True | 13.77 |
| Q-today-omitted | 青野 | omitted | CORRECT | True | 12.97 |
| Q-cancel-omitted | 青野 | omitted | CORRECT | True | 32.43 |

条件遗漏的6条选择：{'CORRECT': 5, 'ACCEPT': 1}；保留范围的6条选择：{'ACCEPT': 6}。

只报告该知情参与者在这些任务中的判断；重复结构、既有背景和练习效应限制解释。原始点击及可选说明私有保存，未用模型补答。正式真人研究仍PENDING_HUMAN_STUDY。
