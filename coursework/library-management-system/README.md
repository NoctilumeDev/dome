# 图书借阅管理系统

本科短学期课程作业。系统包含读者查书、借书、还书与个人记录，以及管理员对图书、分类、书架和用户的管理功能。在课程脚手架基础上补充了权限、库存一致性、书架关联和数据库约束下的图书问答。

[原版脚手架](../original-scaffold/脚手架.zip)

## 技术栈

- 后端：Spring Boot 2.7、JDK 17、MyBatis、MySQL 8
- 前端：Vue 2、Element UI
- 登录：JWT、BCrypt
- 图书问答：本地范围判断、DeepSeek 语义解析、参数化 SQL、数据库事实回答

## 运行

### 初始化数据库

`sql/library_management.sql` 是唯一的数据库初始化入口。它会创建 `library_management` 数据库，重新建立项目数据表，并写入演示数据。

在项目根目录可以直接执行：

```bash
mysql -u your_mysql_admin -p < sql/library_management.sql
```

也可以在 MySQL 客户端或 Navicat 中打开该文件并完整执行。重复导入会重建本项目的数据表，请先确认其中没有需要保留的数据。

### 启动后端

根据本机环境设置数据库连接信息。需要使用 DeepSeek 进行语义解析时，再设置对应的 API 密钥。

```powershell
$env:DB_USERNAME = "你的应用数据库账号"
$env:DB_PASSWORD = "你的数据库密码"
$env:JWT_SECRET = [Convert]::ToBase64String([Guid]::NewGuid().ToByteArray() + [Guid]::NewGuid().ToByteArray())
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API 密钥"
cd backend
mvn spring-boot:run
```

应用不内置数据库账号、密码或 JWT 密钥。运行账号只需拥有 `library_management` 数据库所需的查询与增删改权限，不应使用 MySQL `root` 超级用户。

启动后打开 `http://localhost:22090/api/book-manage-sys-api/v1.0/`。默认演示账号为 `admin`、`zhangsan`、`lisi`，密码均为 `123456`。JWT 签名密钥至少需要 32 字节，上面的命令会生成随机密钥。

### 前端开发模式

如需单独调试前端，在 `frontend` 中执行：

```bash
npm install
npm run serve
```

开发服务器地址为 `http://localhost:22091`。

后端默认允许本机 `localhost:22091` 与 `127.0.0.1:22091` 的开发请求；自定义前端地址可用 `CORS_ORIGINS` 设置，多个地址用逗号分隔。

读者页面支持回车搜索、无结果后重置、查看零余量馆藏，以及借阅和归还确认。当前没有收藏、预约的后端功能，页面不展示这些未实现的入口。窄窗口保留导航文字和表格操作列，编辑弹窗内部滚动，底部操作保持可见。

登录页对 403、404、429、5xx、断网、超时和无效响应显示持续可见的故障卡片，支持重试或返回，保留账号与密码。账号密码错误留在表单中；已登录页面的会话过期仍回到登录入口。

## 图书问答边界

问答功能只处理本馆图书、作者、分类、借阅状态、推荐和馆藏位置相关问题。模型只负责理解查询意图，实际结果来自参数化数据库查询；没有查到的数据不会由模型补写。未配置 DeepSeek API 密钥时，系统使用本地安全解析处理能够确定的馆藏问题。

本人借阅、反馈和书评由登录身份限定；他人的借阅和反馈、用户列表只向管理员和超级管理员开放。每次请求重新核对数据库中的冻结状态和角色，旧 token 不保留冻结前或降级前的权限。

模型计划必须是单个 JSON 对象，只接受白名单字段和类型，不能更换已识别的查询类型或条件。外部模型完整响应限时 5 秒，同一账号最多一个模型请求，全局最多四个；超时、错误或繁忙时使用本地规则。当前以中文查询为主；多本书或多种记录需要拆开查询。每次最多返回 50 条，页面区分匹配总数与本次返回数，并提示截断。

### 回归测试与案例

在 `backend` 执行 `mvn test`，在 `frontend` 执行 `npm test`。后端的 `src/test/resources/assistant-cases.json` 保存原始项目案例，覆盖伪造权限、编码、Unicode、混合查询、非法模型 JSON、条件漂移、凭据索取和虚构馆藏；测试同时验证正常查书、本人记录和管理员查询。

攻击分类参考 [garak](https://github.com/NVIDIA/garak)、[PyRIT](https://github.com/microsoft/PyRIT) 和 [promptfoo](https://github.com/promptfoo/promptfoo)。案例根据本项目边界编写，没有运行或宣称覆盖这些工具的全部测试集。

前端修改后执行 `npm run build`，将 `frontend/dist` 内容同步到 `backend/src/main/resources/static`，然后重新编译后端，确保后端提供的页面与前端源码一致。

## 降级与权衡

DeepSeek 是可选的语义理解层，用于识别口语变形并提高查询召回率。未配置密钥或模型暂时不可用时，系统会退回本地规则；此时复杂表达可能漏检，但不会放宽本地范围过滤、意图白名单、参数化查询和数据库事实回答。

因此，降级影响的是自然语言理解能力与查全率，不影响 SQL 注入防护和“数据库是唯一事实来源”的边界。这是系统主动选择的可用性与智能程度权衡。

## 来源

本项目基于课程提供的教学脚手架完成。

原始教学项目：[B站 · 程序员辰星 · Spring Boot + Vue 图书管理系统](https://www.bilibili.com/video/BV16d4JenESJ/)

项目保留原有 `kmbeast` 包名，用于标识脚手架来源。
