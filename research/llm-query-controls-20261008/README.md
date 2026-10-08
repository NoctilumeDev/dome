# 查询控制补充包

42个事前问题覆盖实体、主体、模糊目标和时间证据。输入在8cc76dcd4c2512240b8e16250c837cf5bcb2dc6c公开冻结，付费前86条原生preflight/control记录通过，39题实际到达模型，3题入口拦截单列。本包是第一阶段探索，不修改产品或旧证据，不是最终冻结复验。

输入与规则见[CONTRACT.md](CONTRACT.md)、[cases.json](cases.json)、[fixtures.json](fixtures.json)、[seal.json](seal.json)；入口与原生资格见[preflight-labels.json](preflight-labels.json)。生产版本dbb32160，原生回放使用两个research-only支持类及H2，未调用共享MySQL/Redis；模型调用单窗使用deepseek-flash/qwen-plus，固定Clock、系统协议及5秒deadline。

归档只读核对（从仓库根目录，Python标准库，无模型Key）：

```powershell
python -X utf8 -B research/llm-query-controls-20261008/verify.py
```

采集、原生回放和评分工具都拒绝覆写已有输出，不将历史请求重发。源码/输入已封印；测量错误需保留首败并另立版本。原始响应保留usage/模型信息，隐藏推理不存，凭据不落盘。新的完整复验应采用新的证据坐标、身份和事前封印，不能通过删除归档绕过拒绝覆写。

结果区分模型结构、原生资格、事前规则、返回ID与事实、主体读取、范围确认及资源使用。支持或未识别均不冒充真人纠错或学习适配，实际现金与促销抵扣未知时不填零。全局每家¥20预算仍有效。

评分v1因计划title/夹具name映射失败，首败见diagnostics/measurement-v1-failure.json。原脚本不改，v2只修映射并输出到[output-v2/RESULTS.md](output-v2/RESULTS.md)，版本绑定见measurement-v2.json。原始234调用和474原生记录未重跑；可运行verify_measurement_v2.py核对v2来源及计数。
