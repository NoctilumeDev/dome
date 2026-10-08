# 第二证据层：控制变量与反例记录

父层60cd5d4与原论文原样保留。本层为32题×4重复、128配对块；自然1,536请求，固定计划审查96请求。题集分为24道执行者标注题与8道DuSQL原文能力边界题；不混成单一总体准确率。原生证据来自固定Java/H2回放，不代表生产部署或真人实验。读回后的资格修正见OBSERVATIONS.md：冻结分数是严格计划标签端点，不自动等于事实答案对错；外部题有入口/拒绝标签冲突，不作为合格外部泛化证明。

第一块六次DeepSeek超时原样纳入；另一次认证GET与一条延迟诊断单列。诊断上限30秒，正式期限仍是5秒；只有一次有界恢复窗口，没有替换难看结果。

## 一致性风险信号

|输入层|厂商|提案请求|完整返回|全字段结构合格|原生计划资格|原生入口未调用planner|
|---|---|---|---|---|---|---|
|prospective_executor_labels|deepseek|384|380|380|380|0|
|prospective_executor_labels|qwen|384|384|383|321|0|
|external_verbatim_capability_boundary|deepseek|128|128|128|48|80|
|external_verbatim_capability_boundary|qwen|128|128|97|7|80|

真实模型调用发生在组件采集层；Java/H2用原始响应回放原生路径，未在线连接模型。若原生入口不调用planner，组件提案不能越过该入口作为产品结果。

|输入层|配对块|两家正确|仅A正确|仅B正确|两家错误|结构一致|P正确｜一致|P错误｜一致|不一致|P至少一家正确｜不一致|
|---|---|---|---|---|---|---|---|---|---|---|
|prospective_executor_labels|96|67|28|1|0|67|1.000000|0.000000|29|1.000000|
|external_verbatim_capability_boundary|32|0|0|0|32|5|0.000000|1.000000|27|0.000000|

一致要求完整字段结构相等，仅消除JSON字段顺序/空白表示差异；不补字段、不忽略筛选或reason。结构不一致可含协议/传输不可用，不能全部称为语义分歧。预冻结oracle对QUERY匹配全部指定字段，对CLARIFY仅判action；澄清处理正确不证明reason解释完整或正确。metrics.json另保留原生资格及共同遗漏代理标签。

## 联合错误与同题比较

|输入层|端点|样本|联合错误|混合边际乘积|逐题平均差|探索性置换P|题族区间下界|上界|
|---|---|---|---|---|---|---|---|---|
|prospective_executor_labels|all_plan_errors|96|0.000000|0.003038|0.000000|1.000000|0.000000|0.000000|
|prospective_executor_labels|semantic_errors_among_valid_pairs|95|0.000000|0.000000|0.000000|1.000000|0.000000|0.000000|
|external_verbatim_capability_boundary|all_plan_errors|32|1.000000|1.000000|0.000000|1.000000|0.000000|0.000000|
|external_verbatim_capability_boundary|semantic_errors_among_valid_pairs|23|1.000000|1.000000|0.000000|1.000000|0.000000|0.000000|

混合边际乘积受题目难度影响；主要比较保留同题重复，按题族整体bootstrap。每题只有四次重复，探索性量不建立普遍统计依赖或独立用户推断；常量共同错误的同题差可为零，不能因此宣布不存在稳定偏置。

## 自审、互审与等调用预算

|输入层|组|块|应查询|计划匹配oracle|匹配的查询/范围提议|匹配的公开执行|待范围确认|公开执行但计划不匹配|策略弃权|逻辑均价¥|逻辑串行中位ms|
|---|---|---|---|---|---|---|---|---|---|---|---|
|prospective_executor_labels|A:a|96|68|95|67|63|4|0|0|0.001996|719.000000|
|prospective_executor_labels|A:b|96|68|68|64|60|5|12|0|0.000730|1461.000000|
|prospective_executor_labels|B|96|68|67|63|59|4|0|29|0.002728|2312.000000|
|prospective_executor_labels|C:a|96|68|63|63|59|4|0|33|0.003601|3406.500000|
|prospective_executor_labels|C:b|96|68|67|63|59|4|0|29|0.005064|2984.000000|
|prospective_executor_labels|D|96|68|63|63|59|4|0|33|0.005938|4063.500000|
|prospective_executor_labels|E:a|96|68|95|67|63|4|0|1|0.004364|1484.500000|
|prospective_executor_labels|E:b|96|68|64|64|60|5|4|27|0.001602|2594.000000|
|prospective_executor_labels|F2:a|96|68|95|67|63|4|0|1|0.003993|1453.000000|
|prospective_executor_labels|F3:a|96|68|95|67|63|4|0|1|0.005989|2148.000000|
|prospective_executor_labels|F4:a|96|68|95|67|63|4|0|1|0.007986|2875.000000|
|prospective_executor_labels|F2:b|96|68|64|64|60|4|11|21|0.001462|2882.500000|
|prospective_executor_labels|F3:b|96|68|66|64|60|4|12|18|0.002192|4273.500000|
|prospective_executor_labels|F4:b|96|68|66|64|60|4|12|18|0.002923|5663.500000|
|external_verbatim_capability_boundary|A:a|32|0|0|0|0|0|0|0|0.002196|773.500000|
|external_verbatim_capability_boundary|A:b|32|0|0|0|0|0|0|0|0.000812|1804.500000|
|external_verbatim_capability_boundary|B|32|0|0|0|0|0|0|12|0.003008|2664.500000|
|external_verbatim_capability_boundary|C:a|32|0|0|0|0|0|0|12|0.003932|3695.500000|
|external_verbatim_capability_boundary|C:b|32|0|0|0|0|0|0|12|0.005472|3437.000000|
|external_verbatim_capability_boundary|D|32|0|0|0|0|0|0|12|0.006397|4444.500000|
|external_verbatim_capability_boundary|E:a|32|0|0|0|0|0|0|5|0.004612|1554.000000|
|external_verbatim_capability_boundary|E:b|32|0|0|0|0|0|0|12|0.001747|2977.000000|
|external_verbatim_capability_boundary|F2:a|32|0|0|0|0|0|0|0|0.004392|1687.000000|
|external_verbatim_capability_boundary|F3:a|32|0|0|0|0|0|0|0|0.006589|2499.500000|
|external_verbatim_capability_boundary|F4:a|32|0|0|0|0|0|0|0|0.008785|3234.000000|
|external_verbatim_capability_boundary|F2:b|32|0|0|0|0|0|0|12|0.001622|3594.000000|
|external_verbatim_capability_boundary|F3:b|32|0|0|0|0|0|0|11|0.002434|5413.000000|
|external_verbatim_capability_boundary|F4:b|32|0|0|0|0|0|0|11|0.003245|7250.000000|

正确处理包含合法澄清/策略弃权，不能冒充任务执行成功；个人确认仍是控制入口，模拟接受不代表真人识别。B/C/D复用同一PA/PB，C/D只有否决权，不能新增正确答案；成本/延迟是从共享原始调用复算的逻辑策略成本，不是在线部署端到端耗时。

## B后审查的净效应

|输入层|B放行的错误查询机会|B放行的正确查询|B的正确澄清候选|
|---|---|---|---|
|prospective_executor_labels|0|63|4|
|external_verbatim_capability_boundary|0|0|0|

|输入层|组|新增阻断错误查询候选|新增阻断正确查询|正确澄清再判|新增弃权|错误阻断−正确阻断|
|---|---|---|---|---|---|---|
|prospective_executor_labels|C:a|0|0|4|4|0|
|prospective_executor_labels|C:b|0|0|0|0|0|
|prospective_executor_labels|D|0|0|4|4|0|
|external_verbatim_capability_boundary|C:a|0|0|0|0|0|
|external_verbatim_capability_boundary|C:b|0|0|0|0|0|
|external_verbatim_capability_boundary|D|0|0|0|0|0|

|输入层|组|明确否决错误|明确否决正确|仅不可用阻断错误|仅不可用阻断正确|否决与不可用并存|
|---|---|---|---|---|---|---|
|prospective_executor_labels|C:a|0|0|0|0|0|
|prospective_executor_labels|C:b|0|0|0|0|0|
|prospective_executor_labels|D|0|0|0|0|0|
|external_verbatim_capability_boundary|C:a|0|0|0|0|0|
|external_verbatim_capability_boundary|C:b|0|0|0|0|0|
|external_verbatim_capability_boundary|D|0|0|0|0|0|

先看B留下多少错误机会，再解释审查增益；零机会不能被解释为reviewer没有抓错能力。净计数没有把不同错误赋予等同现实损失的资格；不可用导致弃权也不算reviewer成功识别语义错误。正确CLARIFY再次收到CLARIFY不记为正确查询误杀。

## 固定错误挑战（不混入自然一致率）

|审核者|注入标签|调用|候选原生资格|ACCEPT|CLARIFY|REJECT|不可用/非法审查|正确QUERY明确阻断|
|---|---|---|---|---|---|---|---|---|
|deepseek|correct|24|24|24|0|0|0|0|
|deepseek|wrong|24|24|0|8|16|0|0|
|qwen|correct|24|24|15|9|0|0|0|
|qwen|wrong|24|24|3|9|12|0|0|

16个正确/错误计划在调用前冻结并经原生回放；PA=PB是实验注入，不是两模型自然共同误解。此表衡量审查对指定错误的敏感性，不估计这些错误的自然发生率。

## 全部调用与费用

|阶段|厂商|请求身份|SUCCESS|TIMEOUT|已知保守估价¥|缺用量|
|---|---|---|---|---|---|---|
|natural|deepseek|768|762|6|1.642744|6|
|natural|qwen|768|768|—|0.611392|0|
|injected_review|deepseek|48|48|—|0.112252|0|
|injected_review|qwen|48|48|—|0.042324|0|
|diagnostic|deepseek|1|1|—|0.001758|0|

|厂商|新请求身份|累计已知估价¥|含未知reserve¥|累计上限¥|
|---|---|---|---|---|
|deepseek|817|4.473270|4.543270|20|
|qwen|816|1.653346|1.663346|20|

实际账单NOT_VERIFIED；按公开最高输入价保守估算，未知每次另留¥0.01，这是预算reserve而非实际扣款保证。认证GET无生成用量，不计生成请求。

## 结论边界与后续

本层只增加冻结分布的描述性/探索性证据。不同模型档位、跨日稳定、独立盲标均NOT_RUN；真人为PENDING_HUMAN_STUDY；生产MySQL、真实部署、真实用户收益仍NOT_PROVEN。新结果无论支持、推翻或无法判断，都不回写原观察记录。控制项与替代解释见CONTROL-LEDGER.md。
