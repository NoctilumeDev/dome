# 双系统实验维护入口

本目录保存一次有界研究。业务源码冻结在 `dbb32160a811fd06c826a8d9eafbc660a0548219`，没有为了新题继续修改产品。a=DeepSeek/deepseek-flash，b=Qwen/qwen-plus；别名不等于固定权重。

直接阅读：[论文正文](output/paper.md)、[PDF](output/pdf/双系统有限能力实验论文.pdf)、[核心结果表](output/RESULTS.md)、[补充结果表](extension/output/RESULTS.md)、[控制与结论总账](CONTROL_LEDGER.md)。逐题数据在 CSV/JSON，不靠截图裁决。截图是冻结记录查看器，不能冒充线上产品界面。

## 已执行及保留边界

|批次|数量|用途|
|---|---:|---|
|先导|8 块 / 96 请求|工具自检，不进正式分母|
|核心|48 题 × 3 / 1,728 请求|A、B、C、D、E、F2/F3/F4 受控对照|
|原题后窗口|48 块 / 576 请求|同题描述性重测，不证明纯时间或跨日效应|
|前瞻组合题|16 块 / 192 请求|新语法组合；同执行者标签，不是独立盲评|
|历史转移|396 题/厂商对 + 10 控制|旧保留计划在当前原生夹具执行，不重新计入模型分母|

全部真实调用共 2,592 个请求身份，2,591 次 HTTP 200，一次 `UNKNOWN_INTERRUPTED` 不重发、不插补。DeepSeek 保守估算 ¥2.716516，Qwen ¥0.999630，另留未知调用 ¥0.01；实际扣费未核对，每家授权上限 ¥20。所有批次的原生负控制及事实快照核对通过；固定 H2 回放不证明生产 MySQL、微信真机或多节点。

核心、后窗口和新题分别观察到：D 没有比 B 多完成正确公开查询；新题中两家也有共同失败，保守弃权没有恢复正确答案。这里只能报告指定表与采集窗口中的结果，不能宣布互审普遍无用、模型普遍排名或用户一定看懂确认。

八个控制族均有状态。独立标注者盲评、真人范围识别及跨日稳定未执行；纯业务域与协议复杂度存在混杂；同金额/同 token 收益未提出。历史 X01/X02 原文缺失，四个厂商坐标留在 `history/manifest.json`，不可用摘要补造。缺口是研究边界，不是隐藏的成功项。

## 唯一复核路径

在本目录用 Python 3 运行（离线，无凭据）：

```powershell
python -B -m unittest discover -s tests -v
python -B verify.py
```

需要重新生成派生表时依次运行：

```powershell
python -B analyze.py core
python -B summarize.py
python -B extension/evaluate.py
python -B extension/summarize.py
python -B control_ledger.py
```

`verify.py` 核对冻结研究文件、Git 源坐标、请求哈希、身份数量、原生见证和凭据残留；不调用模型，也不把已声明未证明项升级为通过。研究文件按字节保留，源码仅容许 Git checkout 的 CRLF/LF 差异；原始 Windows 字节哈希仍在旧冻结清单中。生成论文需 ReportLab 与可用中文字体，`paper.py` 目前使用 Windows 微软雅黑；其他机器应明确调整报告环境，不能声称复用了同一 PDF 字节身份。

若确需重新执行原生回放，使用 `prepare_native.py`、`native_replay.ps1` 或 `extension/replay.py`，先核对 JDK/Maven 路径及独立 H2 夹具。脚本不创建 MySQL/Redis/MQ，临时测试 helper 仅从 `native/` 复制到两模块 test 目录；回放结束删除自己复制的两份 helper，避免进入普通测试发现。原 raw/native 输出不可覆盖；新执行写新目录并取得新证据身份。

若确需新增真实调用，另建批次合同：冻结题表/标签/策略/预算后才收集。新凭据只存在于内存，绝不放进文件、命令文本、Git 或截图。`run.py` 的自动恢复仅属于尚未闭合的采集批次；本轮已闭合，不得用原目录继续增题。未知请求不自动补发。

## 版本与收尾

`README.md` 是原冻结合同，不滚动改写。`MEASUREMENT_V2.md` 与 `results/scorer-first-failure.txt` 记录一次评分器错误及原条件修复；原 v1 工具和证据保留。旧核心论文首次版本保存在 Git 提交历史，不额外复制“最终-final”文件。

首次独立 LF checkout 的核对曾因 Git 索引在 byte-preserving 属性生效前转换换行而失败，见 `results/git-readback-first-failure.txt`。修复只重新索引原保留字节，不修改冻结哈希、题目或提示；原失败提交保留在 Git 历史中，资格只授予重新检出后实际通过的候选。

留存原始响应/发出账本、冻结输入、首败、最终原生见证、最终表/论文和关键截图。临时记录浏览器、服务器及本轮 JVM 已退出。临时 Maven target、渲染 QA 图片、复制 helper 的批量删除命令被自动审批拒绝，未执行；用户随后指定先保留，待最后一轮集中清理。这些材料不提交，恢复普通测试前先移除复制 helper。共享 Maven、MySQL、Redis 和用户其他工作树不属于本轮清理权。Git diff 自身保存文档修订，不再制造清理 SHA 大清单。
