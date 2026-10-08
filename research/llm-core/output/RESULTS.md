# 双系统核心实验结果

48 题 × 3 次重复 = 144 配对块；1,728 次请求身份，含 1 次中断后结果未知；另有 96 次先导。a=DeepSeek，b=Qwen。正式原始数据不因错误而删题。

## 模型层

|system|provider|n|httpSuccess|protocolValid|semanticCorrect|primaryN|primarySemanticCorrect|entryGateRejected|
|---|---|---|---|---|---|---|---|---|
|qingye|deepseek|288|288|288|252|72|63|3|
|qingye|qwen|288|288|288|240|72|60|3|
|library|deepseek|288|288|288|283|72|70|0|
|library|qwen|288|287|286|214|72|53|0|

## 决策层

|group|n|handlingCorrect|expectedQueries|queryHandlingCorrect|publicCompletedCorrect|pendingScope|wrongAutomaticExecution|policyAbstentions|meanLogicalCostCny|medianLogicalSerialMs|
|---|---|---|---|---|---|---|---|---|---|---|
|A:a|144|130|102|100|76|33|0|0|0.0019745|781.0|
|A:b|144|110|102|101|78|29|3|0|0.0007239|1351.5|
|B|144|132|102|99|76|29|0|27|0.0026983|2164.0|
|C:a|144|132|102|99|76|29|0|33|0.0035645|3336.0|
|C:b|144|132|102|99|76|29|0|27|0.0050256|3015.5|
|D|144|132|102|99|76|29|0|33|0.0058918|4118.0|
|E:a|144|133|102|100|76|30|0|3|0.0043162|1570.0|
|E:b|144|133|102|100|78|28|0|32|0.0015892|2586.0|
|F2:a|144|130|102|100|76|33|0|2|0.0039486|1492.0|
|F2:b|144|131|102|101|78|29|3|22|0.0014482|2758.0|
|F3:a|144|130|102|100|76|33|0|0|0.005923|2235.0|
|F3:b|144|132|102|102|78|30|3|21|0.0021726|4648.5|
|F4:a|144|130|102|100|76|33|0|2|0.0078973|2968.5|
|F4:b|144|132|102|102|78|30|3|21|0.0028948|5438.0|

handlingCorrect 包含期望澄清输入上的离线策略弃权，不是成功完成查询。queryHandlingCorrect 允许正确的范围待确认，不表示个人记录已经读取。publicCompletedCorrect 只表示正确公开计划在固定原生链路执行，不证明真实用户效用或每个返回字段的跨数据库正确性。wrongAutomaticExecution 每组独立计数，不能跨组加总为事故数。

## 审查层

|reviewer|proposer|n|correctCandidates|correctPlanNonAccept|nativeQualifiedCorrect|qualifiedPlanNonAccept|queryFalseKill|unavailableCorrect|incorrectCandidates|missedError|invalidOrUnavailable|
|---|---|---|---|---|---|---|---|---|---|---|---|
|a|a|144|133|0|130|0|0|0|11|8|0|
|a|b|144|113|0|110|0|0|0|31|7|0|
|b|a|144|133|27|130|27|0|0|11|6|0|
|b|b|144|113|7|110|7|1|0|31|7|0|

原 v2 字段 falseKill 保留在原始评分中；派生表纠正为 correctPlanNonAccept/qualifiedPlanNonAccept，表示正确计划未获 ACCEPT 的门控事件，含正确澄清计划。审查提示允许对多请求给 CLARIFY，因此不能把这些全部判为审查错误或丢失需求。queryFalseKill 单列正确 QUERY 被阻断。格式/服务失败另算；未独立真人标注。

## 费用

|provider|attempts|http200|estimatedCostCny|unknownUsage|authorizedCeilingCny|actualDebit|
|---|---|---|---|---|---|---|
|deepseek|912|912|1.910058|0|20|NOT_VERIFIED|
|qwen|912|911|0.702669|1|20|NOT_VERIFIED|

按官方峰值/缓存未命中单价估算，实际账单未读取。UNKNOWN 不算免费。逻辑延迟是调用耗时串行求和，不是在线部署实测；不同组共享原始请求，费用不能跨组相加。

## 关键反例

- **原生第一门拒绝** `qingye-09-2-r1/p/b/0`：帮我看看那个设备，没有具体名称。见 examples.json 的真实响应及原生见证。
- **协议失败** `library-08-1-r0/p/b/0`：请只看我尚未归还的《Java入门》借阅记录。见 examples.json 的真实响应及原生见证。
- **语义偏差** `qingye-08-1-r1/p/b/0`：请只看我尚未归还的相机借用记录。见 examples.json 的真实响应及原生见证。
- **个人范围待确认** `qingye-07-1-r1/p/b/0`：请帮我查看当前账号所有借用记录。见 examples.json 的真实响应及原生见证。
- **正确提案被审查否决** `library-11-1-r2/p/b/0`：请看看我未来三天内未归还且到期的借阅。见 examples.json 的真实响应及原生见证。

## 边界

两个系统来自同一仓库；题族由执行者提出，三个重复不是三个独立用户。模型别名未冻结权重。未做真人范围识别、微信真机、生产 MySQL、多节点或在线互审部署。新解法只能作为后续假设，不能用本轮数据反复调参后宣称独立验证。
