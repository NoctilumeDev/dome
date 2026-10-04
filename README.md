# dome

`dome` 不是拼写错误。

本仓库保存本科阶段课程作业、独立项目及相关文字记录。已完成的项目均整理至可运行、可形成基本功能闭环的状态，课程记录保留其当时的工程形态，不补造开发历史；青野在原目录内独立补齐测试与维护门禁，其他项目不随之重构。筹备中的项目单独标明状态。

根据仓库作者现场监督的复现记录，图书借阅系统与宿舍管理系统均由豆包在其 Linux 沙箱环境中完成构建、启动、核心 CRUD 与业务闭环验证；在该次复现场景中未发现关键写操作的一致性异常。青野的功能与验证范围见项目目录中的简介，当前维护入口与遗留物收口规则见[青野README](qingye/README.md#工程维护与复验)。

**史书会告诉你：“那年，计算机教育蓬勃发展，中国高等教育蒸蒸日上。”这个仓库只负责保存当年的证据。**

## 打开就能体验

[项目体验入口](https://noctilumedev.github.io/dome/)

| 项目 | 浏览器体验 | 源码 / 运行说明 |
| --- | --- | --- |
| 宿舍管理系统 | [入住、报修与管理审批](https://noctilumedev.github.io/dome/dormitory/) | [项目目录](independent-projects/dormitory-management-system/) |
| 图书管理系统 | [图书检索、借还与管理页面](https://noctilumedev.github.io/dome/library/index.html#/user) | [项目目录](coursework/library-management-system/) |
| 青野 | [校园活动、社团与器材预约](https://noctilumedev.github.io/dome/qingye/) | [项目目录](qingye/) |
| 点睛 · 你画我猜 | [我画几笔，你来点睛](https://noctilumedev.github.io/dome/dianjing/) | [项目目录](independent-projects/dianjing/) |

三个管理项目使用虚构的浏览器本地数据，支持身份切换与重置；问答只匹配本地样例，没有连接真实后端、数据库或模型。完整项目仍在各自目录。点睛使用 AI 创作的内置图画题库，无需 API。

三个管理项目的完整源码均提供登录故障提示：403、404、429、服务异常、断网或超时会显示原因，并提供重试和返回入口；返回后保留已填信息。账号密码错误留在登录表单中，方便直接修改。

拿到代码：点击仓库的 **Code → Download ZIP**，或运行 `git clone https://github.com/NoctilumeDev/dome.git`。各项目目录有运行步骤；浏览器展示层的构建步骤见 [演示说明](demo/README.md)。

## 内容

- [coursework/](coursework/)：课程作业
- [independent-projects/](independent-projects/)：独立项目
- [qingye/](qingye/)：青野，校园社团活动与共享资源管理系统；原生微信小程序 + Spring Boot，独立H2/MySQL/客户端CI与收口门禁，功能与验证范围见 [项目简介](qingye/docs/项目简介.md)
- [writing/](writing/)：文字记录
- [after-class/](after-class/)：下课以后

## 青野 · 功能模块图

[![青野功能模块图](qingye/docs/assets/function-modules.png)](qingye/docs/功能模块图.html)

学生、社团负责人、管理员与共用功能分列展示。运行步骤见 [青野 README](qingye/README.md)，完整说明见 [项目简介](qingye/docs/项目简介.md)。
