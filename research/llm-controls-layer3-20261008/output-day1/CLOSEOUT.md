# 原12题跨日窗口收尾

状态：COMPLETE_ACTUAL_NEXT_DAY。2026年10月9日19:11:15至19:12:49（上海时间）新增72次物理请求，36次/家，全部HTTP200且usage可得。距day0结束87014.339059秒；逐请求payload、顺序、模型alias、固定业务Clock与H2快照一致。

82条Java/H2原生回放包括72候选和原10项控制；两个Maven入口均通过。未确认的私人集合不读取，外来userId控制无查询，业务快照无变化。机制测试的模拟确认不构成真人收益证据。旧源码、题表、oracle、评分器、原始响应、论文和前两证据层未改。

调用前提交b445ae2封存独立预算守卫及来源记录。守卫只补入旧查询包全局费用和上海日期检查，不改变冻结collector、模型payload或分析。新增物理资源为DeepSeek输入30348/输出1800 token，Qwen输入30573/输出1623 token。完整全局保守累计为8.437669元、2.97314145元，各低于20元；原第三层自身新增仍低于7元。实付及赠送抵扣仍NOT_VERIFIED。旧reporter的costs不含后来的查询包，不作为完整全局累计。

原verify.py通过：2664旧请求、1906旧原生记录；新增verify_day1.py只读核对72/82的原始对应关系、冻结评分、控制、实际间隔、usage、预算和凭据残留。复核入口：在仓库根目录执行python -B research/llm-controls-layer3-20261008/verify_day1.py。回执见VERIFICATION.json。

汇总首败：初版OBSERVATIONS及截图错误地把千问价格题的被拒候选写成实际执行。首版及FIRST_FAILURE.json保存在../diagnostics/day1-summary-first-failure/。修正只涉及衍生文字与旁证截图；原数值和评分不变。最终读回明确：DeepSeek该题实际查询；千问该题INVALID_PLAN拒绝且repository查询数为0。

模型collector、两个Maven/JVM、临时浏览器页与8771本地截图服务器已退出；HOST_READBACK.json记录主机读回。共享MySQL 7408、Redis 3392保持运行，未操作它们。collector/JVM中的凭据副本已随进程退出；线程内凭据仅保留给用户已授权的今晚23:40新查询包重复，不写文件、环境或调度配置。

Residual Hygiene: DEFERRED_UNTIL_QUERY_DAY1。按用户“最后一轮再删”，可重建target及两份旧研究helper暂留到晚间窗口；不声称LOCAL_DORMANCY。唯一原始数据、首败、Git及最终记录继续保留。

原72请求自动化已暂停，防止重复调用。独立42题/702调用的新查询包跨日重复仍待23:40及实际24小时检查；本结果不能替它取得资格。真人与独立盲标PENDING_HUMAN_STUDY，最终全矩阵复刻PLANNED_NOT_SEALED。PR #10继续draft，无产品合并或后续IR/CRUD/分布式施工。
