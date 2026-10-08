# 第三证据层：非人工控制

父层固定 [e3e4934](https://github.com/NoctilumeDev/dome/commit/e3e4934a10b0284b3c7d4deb6c0eeb8a101fb082)。产品、旧论文、前两层原始数据原样保留。

- `CONTRACT.md`：事前机制/端点/预算/停止线。
- `seal.json`：事前15个工具/输入及165个产品文件；父层Git内容与本轮本地换行字节分别绑定。
- `cases.json`：12 pilot与24正式题；不按pilot输出挑选正式题。
- `external-provenance.json`、`external-cases.json`：8原文边界与8显式适配兼容题。
- `diagnostics/native-preflight`：先检查入口、候选资格与事前标签，非模型成绩。
- `results/<phase>`：请求前journal、真实原始response、usage、时间、停止状态。
- `output/RESULTS.md`、`metrics.json`：资格、分包结果与严格标签；不把代理指标当事实事故。
- `BILLING_NOTE.md`：千问新用户赠送额度的事后补充；费用表是未抵扣赠送额度的公开价理论成本，实际扣款仍未核。
- `NEXT_CONTROLS.md`：对象消歧、同名主体绑定、模糊目标三组后续草稿；`DRAFT_NOT_SEALED / NOT_RUN`，不改变本轮封印或day1窗口。

只读核对入口 `python -X utf8 -B verify.py`。本轮收集入口是历史施工工具，归档后不原地覆盖结果。各阶段分别是pilot/formal/external/tier/day0/day1；新的正式回放应有新输出坐标。真人确认、独立真人盲标最后实施，当前PENDING_HUMAN_STUDY。

原始失败见 `diagnostics/seal-first-failure.txt`。第一准备提交不是封印成功；最终封印修复仅处理Windows换行与二进制字节对照，付费调用之前完成。

跨日只允许在day0完成后真实间隔至少24小时且上海日期不同；不能修改Clock或冒充另一天。任务后续只跑已冻结的day1窗口，不扩题、不改产品，不重复旧调用。
