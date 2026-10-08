# 第二证据层 · 控制变量与反例

父层及论文冻结于60cd5d4；本目录独立留证，不改旧论文、不改产品。问题是：一致性风险信号、B后审查的净增益、重复采样误差结构。

- [合同](CONTRACT.md)与[frozen-core-v2.json](frozen-core-v2.json)：事前输入/工具/产品绑定。
- [控制变量总账](CONTROL-LEDGER.md)：每项控制排除什么解释，哪些仍未测。
- [一次恢复窗口](WINDOW2.md)：第一块超时、诊断与原样续行；首败不删，诊断不混入正式分母。
- [读回观察与资格](output/OBSERVATIONS.md)：区分计划标签不匹配、真实任务遗漏、外部控制冲突。
- [结果](output/RESULTS.md)、[CSV/JSON](output/)与[旁证屏](output/dashboard.html)：只有正式采集与原生回放完成后生成，不把预回放当完整实验。
- [自然原始请求](results/core/calls.jsonl)与[固定计划审查](results/challenge/calls.jsonl)：分别1,536和96个身份，分母不混。

运行顺序：冻结 → 自然收集 → 原生回放 → 固定计划审查 → evaluate.py → analysis.py → report.py → verify.py。新窗口使用run-window2.py；原入口不改。replay-final.py只复用逐字节相同的预回放helper，先将预回放输入/输出留存后再执行，不覆盖首败。

工具边界：原13项测试与统计5项测试；使用固定Java/H2回放，不依赖共享MySQL服务。密钥仅非回显会话输入，不入文件/Git。费用包含原累计、所有新生成请求及独立诊断；实际账单NOT_VERIFIED。

未测：不同档位、跨日稳定、独立盲标；真人PENDING_HUMAN_STUDY。完整闭合控制矩阵不等于支持预设结论。下一项实验必须绑定一个替代解释，否则不增加。

当前状态：采集与本轮冻结验证完成；[收尾](CLOSEOUT.md)的人工删除仍待处理。外部控制CONFOUNDED，误差依赖无法裁决。归档只读入口为`python -X utf8 -B closeout.py`；模型采集与原生回放脚本是历史施工入口，任何新复验必须用新输出坐标，不原地覆盖归档。
