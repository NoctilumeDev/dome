# 补充控制实验结果

64 配对块、768 次调用；原 48 题后窗口与 16 道新语法组合题分层报告。a=DeepSeek，b=Qwen。固定源 SHA、协议、夹具、时钟、评分器均保持不变。

## same frozen core question, later window · 48 块

|group|n|handlingCorrect|expectedQueries|queryHandlingCorrect|publicCompletedCorrect|pendingScope|wrongAutomaticExecution|policyAbstentions|
|---|---|---|---|---|---|---|---|---|
|A:a|48|44|34|34|26|11|0|0|
|A:b|48|37|34|34|26|10|1|0|
|B|48|45|34|34|26|10|0|8|
|C:a|48|45|34|34|26|10|0|10|
|C:b|48|45|34|34|26|10|0|8|
|D|48|45|34|34|26|10|0|10|
|E:a|48|45|34|34|26|10|0|1|
|E:b|48|45|34|34|26|10|0|10|
|F2:a|48|43|34|33|25|11|0|1|
|F3:a|48|43|34|33|25|11|0|0|
|F4:a|48|43|34|33|25|11|0|1|
|F2:b|48|44|34|34|26|10|1|7|
|F3:b|48|44|34|34|26|10|1|7|
|F4:b|48|44|34|34|26|10|1|7|

## prospective-held-out-from-core; executor labels, no independent human blindness · 16 块

|group|n|handlingCorrect|expectedQueries|queryHandlingCorrect|publicCompletedCorrect|pendingScope|wrongAutomaticExecution|policyAbstentions|
|---|---|---|---|---|---|---|---|---|
|A:a|16|15|12|11|11|0|0|0|
|A:b|16|13|12|11|11|0|2|0|
|B|16|15|12|11|11|0|0|3|
|C:a|16|15|12|11|11|0|0|5|
|C:b|16|15|12|11|11|0|0|3|
|D|16|15|12|11|11|0|0|5|
|E:a|16|15|12|11|11|0|0|0|
|E:b|16|15|12|11|11|0|0|5|
|F2:a|16|15|12|11|11|0|0|0|
|F3:a|16|15|12|11|11|0|0|0|
|F4:a|16|15|12|11|11|0|0|1|
|F2:b|16|14|12|11|11|0|2|2|
|F3:b|16|14|12|11|11|0|2|1|
|F4:b|16|14|12|11|11|0|2|2|

## 模型/协议层

|stratum|system|provider|n|httpSuccess|protocolValid|semanticCorrect|primaryN|primarySemanticCorrect|entryRejected|
|---|---|---|---|---|---|---|---|---|---|
|same frozen core question, later window|qingye|deepseek|96|96|96|84|24|21|1|
|same frozen core question, later window|qingye|qwen|96|96|96|80|24|20|1|
|same frozen core question, later window|library|deepseek|96|96|96|94|24|24|0|
|same frozen core question, later window|library|qwen|96|96|96|72|24|18|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|qingye|deepseek|32|32|32|32|8|8|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|qingye|qwen|32|32|32|32|8|8|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|library|deepseek|32|32|32|30|8|7|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|library|qwen|32|32|32|20|8|5|0|

## 审查门控

|stratum|reviewer|proposer|n|qualifiedCorrectNonAccept|queryFalseKill|missedError|
|---|---|---|---|---|---|---|
|same frozen core question, later window|a|a|48|0|0|2|
|same frozen core question, later window|a|b|48|0|0|2|
|same frozen core question, later window|b|a|48|9|0|2|
|same frozen core question, later window|b|b|48|2|0|2|
|prospective-held-out-from-core; executor labels, no independent human blindness|a|a|16|0|0|1|
|prospective-held-out-from-core; executor labels, no independent human blindness|a|b|16|0|0|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|b|a|16|4|0|0|
|prospective-held-out-from-core; executor labels, no independent human blindness|b|b|16|2|0|0|

## 全轮累计费用

|provider|attempts|http200|estimatedCostCny|unknownUsage|authorizedCeilingCny|actualDebit|
|---|---|---|---|---|---|---|
|deepseek|1296|1296|2.716516|0|20|NOT_VERIFIED|
|qwen|1296|1295|0.99963|1|20|NOT_VERIFIED|

金额为官方单价保守估算，含先导、核心、扩展；1 次历史中断费用未知，另留 ¥0.01 余量。实际扣费未读取。

## 失败坐标

- same frozen core question, later window / library-06-1 / A:b：请只查我今天借阅的图书记录 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / library-09-2 / A:b：帮我查那个图书的位置，没有说是哪一本 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-05-2 / A:b：相机库存与我报名了什么都查一下 → QUERY；错误自动执行=True。原计划及冻结标签见 failures.json。
- same frozen core question, later window / library-06-2 / A:b：仅看昨天我的借阅记录，不要全部历史 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-06-1 / A:a：请只查我今天借用的器材记录 → CONFIRM_SCOPE；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-06-1 / A:b：请只查我今天借用的器材记录 → CLARIFY；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / library-05-1 / A:b：请同时查《三体》的位置和我的借阅，两项都需要 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-08-1 / A:a：请只看我尚未归还的相机借用记录 → CONFIRM_SCOPE；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-08-1 / A:b：请只看我尚未归还的相机借用记录 → CONFIRM_SCOPE；错误自动执行=False。原计划及冻结标签见 failures.json。
- prospective-held-out-from-core; executor labels, no independent human blindness / library-H03-1 / A:b：先查询《三体》的位置；如果找不到，再查询《Java入门》的位置，需要按这个条件完成两步。 → QUERY；错误自动执行=True。原计划及冻结标签见 failures.json。
- prospective-held-out-from-core; executor labels, no independent human blindness / library-H04-2 / A:a：三体|历史背景；Java入门|本次唯一请求：馆藏位置。 → CLARIFY；错误自动执行=False。原计划及冻结标签见 failures.json。
- prospective-held-out-from-core; executor labels, no independent human blindness / library-H04-2 / A:b：三体|历史背景；Java入门|本次唯一请求：馆藏位置。 → QUERY；错误自动执行=True。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-09-2 / A:a：帮我看看那个设备，没有具体名称 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-09-2 / A:b：帮我看看那个设备，没有具体名称 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / library-05-2 / A:b：馆藏位置和我个人反馈都查一下 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- prospective-held-out-from-core; executor labels, no independent human blindness / library-H03-2 / A:b：如果找不到《三体》就查《Java入门》的位置，找得到就查我的借阅；帮我按这个分支办理查询。 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / library-09-1 / A:b：那本书放哪里，我没有提供书名 → REJECT；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-08-2 / A:a：我的相机借用，仅查询未归还的 → CONFIRM_SCOPE；错误自动执行=False。原计划及冻结标签见 failures.json。
- same frozen core question, later window / qingye-08-2 / A:b：我的相机借用，仅查询未归还的 → CONFIRM_SCOPE；错误自动执行=False。原计划及冻结标签见 failures.json。

后窗口只对原题作描述性配对，采集时间与重平衡顺序共同变化，不能识别纯时间因果。新题由同一执行者在核心后设计、扩展前冻结，模型不可见标签，执行者不是独立盲标者。历史回放仅转移既有计划，不重新归入模型语义分母。各组共享调用，错误数不能横向累加为独立事件。
