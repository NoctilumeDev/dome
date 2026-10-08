# 第三证据层：非人工控制

父层 e3e4934、第一层 60cd5d4、产品 dbb32160 原样冻结。真人确认与独立真人盲标最后进行，本轮 PENDING_HUMAN_STUDY。产品、两个完整协议、review prompt、Clock、H2 fixture 不变。不修产品、不覆写旧证据/论文。

三个证据包分别记账：误差变异、自然 B 后审查、外部输入能力适配。六个事前机制是嵌套否定、指代绑定、条件分支、撤销与保留、长业务列表、支持/不支持条件组合。每机制两系统；pilot 使用独立词项，每题两次两模型，只检验生成机制可运行，不进入正式分母。正式各机制两变体、两系统，共24题，每题8个重复块，每块各模型4提案和4审查，共2304调用。所有机制都进入正式集，禁止按 pilot 模型表现挑题；正式文本在正式输出出现前冻结。B/C/D复用同一PA/PB，审查只否决、不修复。

联合误差主要端点只用协议有效且原生可达的主提案对。逐题边际/联合率、同题置换、整题族bootstrap；至少4道题且至少2个题族，两模型各自均有同题0/1变化，且有效重复不少于6，才认为此分布提供了最低识别条件。未达到则NOT_IDENTIFIABLE，不把P=1解释为独立。达到了也只是探索性条件关联，不宣称因果依赖。

自然review端点：B放行的错误QUERY/CONFIRM_SCOPE计划数量、明确审查新增拦错、正确QUERY误拦、正确CLARIFY再澄清、传输/格式不可用、逻辑延迟与费用。零机会即NOT_IDENTIFIABLE_ON_THIS_DISTRIBUTION。冻结严格oracle与完整结构一致性；intent标签不匹配不能自动当作事实错误。任务遗漏、协议错误、权限事故分别列示。共同错误频率与挑战集 sensitivity 不混同。

外部包：保留DuSQL原文与SQL及适配操作。original boundary与adapted compatible分别标注；适配过的题不是原benchmark泛化证据。先用原生stub检查入口与完整候选资格、核对oracle；能力无法表达/入口与oracle不一致的条目单列CONFOUNDED，不偷偷重标签。标注仍由同一执行者完成，不冒充独立盲审。

档位独立包：事前选每机制每系统第一个变体，共12题，3重复；同窗口交错调用deepseek-flash/deepseek-v4-pro及qwen-plus/qwen-flash，144提案。只改变模型ID；temperature0、thinking关闭、5s、max_tokens相同。型号不意味着冻结权重；记录响应model。不跨日混做档位。额外设置同12题同配置baseline today/next day，各72提案；跨日必须真实相隔至少24小时且上海日期不同，题、prompt、payload、Clock保持一致，真实采集日期才改变。

本轮最多¥7新增估价（含pilot/正式/外部/档位/两日），每家累计仍不得超过¥20。此前保守累计DeepSeek¥4.543270、Qwen¥1.6633456。计价全部输入按未命中高峰；每个unknown先留¥0.05预算余量，余量不是实际账单。请求前按保守块余量拒绝超预算。鉴权失败、三个unknown、显著传输异常、冻结文件改变、原生不变量击穿立即停止；已开始请求不重发。新收集采用逐请求停止，不把错误凑到整块才停。

仅工具错误允许留下首败并版本化修复；产品失败登记，不改。跨日需真实等到下一窗口，不伪造时间；机器/凭据不可用留ENVIRONMENT_BLOCK。每项均允许SUPPORTED/REFUTED/NOT_IDENTIFIABLE/CONFOUNDED/NOT_RUN。执行成功不意味着结论支持。
