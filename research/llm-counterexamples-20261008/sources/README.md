# 外部输入来源

DuSQL原文/SQL来自[官方数据发布](https://dataset-bj.cdn.bcebos.com/qianyan/DuSQL.zip)，论文为[DuSQL: A Large-Scale and Pragmatic Chinese Text-to-SQL Dataset](https://aclanthology.org/2020.emnlp-main.562/)。本轮仅使用开发集教材辅助参考书域的8条问题；sourceId/sourceDb/sourceQuery保存在cases.json，原压缩包与条目校验保存在DuSQL-source.json。

选择过程在prepare.py：按数据库及预定义SQL字段/运算筛选、ID排序、固定seed抽8条。原问题未重写，但执行标签由本轮执行者按产品能力映射；不能称为独立人类盲标，不能宣称代表全部DuSQL分布或查询成功任务。

全集是本地可重取来源缓存，未提交；原发布附研究使用协议，不标成MIT。SeSQL原作者仓库也曾用于核对外部输入，但本轮取得样例不是目标业务域，未纳入；不为了“外部样本数”强行映射。
