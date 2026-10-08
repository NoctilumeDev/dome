# 一次有界恢复窗口

原冻结版本 ae0d410 的首块 12 请求保留：DeepSeek 六次 TIMEOUT、千问六次 HTTP 200。已触发 USAGE_UNAVAILABLE，原 summary 逐字节保存为 collection-summary-window1.json。停止发生在完成配对块后；不声称每次请求后即时停止。

单独诊断 GET /models 返回200，一次新诊断请求约1.234秒成功。诊断采用30秒上限，但不进入正式语义分母；不能据此断定之前故障根因。

此窗口只继续128块中的未执行块，不重发已保留 callId，不排除首块失败，不变更题集、oracle、模型、prompt/schema、5秒期限、fixture、评分器或业务源码。run-window2.py 与原 collector 的差异仅为传输/未知 usage 停止计数以本窗口起点计数，并记录起点；费用和未知 reserve 继续累计。原 run.py 与冻结 manifest 保持原样。

只允许一次恢复窗口；再触发停止即收口为阻断，不自动开第三次窗口。总费用包括诊断；原始首次失败不删，不改，不另挑更好答案。此恢复资格来自当前认证/响应观察，不表示全部正式请求必定恢复。
