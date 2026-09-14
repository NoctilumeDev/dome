# 图书借阅管理系统

本科短学期课程作业。系统包含读者查书、借书、还书与个人记录，以及管理员对图书、分类、书架和用户的管理功能。在课程脚手架基础上补充了权限、库存一致性、书架关联和数据库约束下的图书问答。

## 技术栈

- 后端：Spring Boot 2.7、JDK 17、MyBatis、MySQL 8
- 前端：Vue 2、Element UI
- 登录：JWT、BCrypt
- 图书问答：本地范围判断、DeepSeek 语义解析、参数化 SQL、数据库事实回答

## 运行

1. 使用 `sql/init.sql` 初始化 `library_management` 数据库。
2. 设置数据库密码、JWT 密钥和 DeepSeek API 密钥。
3. 在 `backend` 中执行 `mvn spring-boot:run`。
4. 打开 `http://localhost:22090`。

PowerShell 示例：

```powershell
$env:DB_USERNAME = "root"
$env:DB_PASSWORD = "你的数据库密码"
$env:JWT_SECRET = "本地随机密钥"
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API 密钥"
cd backend
mvn spring-boot:run
```

如需前端开发模式，在 `frontend` 中执行 `npm install` 和 `npm run serve`，访问 `http://localhost:22091`。

默认演示账号为 `admin`、`zhangsan`、`lisi`，密码均为 `123456`。

## 图书问答边界

问答功能只处理本馆图书、作者、分类、借阅状态、推荐和馆藏位置相关问题。模型只负责理解查询意图，实际结果来自参数化数据库查询；没有查到的数据不会由模型补写。

## 来源

本项目基于课程提供的教学脚手架完成。

原始教学项目：[B站 · 程序员辰星 · Spring Boot + Vue 图书管理系统](https://www.bilibili.com/video/BV16d4JenESJ/)

仓库保留原有 `kmbeast` 包名，用于标识脚手架来源。