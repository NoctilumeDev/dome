# 图书借阅管理系统

本科短学期课程作业。系统包含读者查书、借书、还书与个人记录，以及管理员对图书、分类、书架和用户的管理功能。在课程脚手架基础上补充了权限、库存一致性、书架关联和数据库约束下的图书问答。

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
mysql -u root -p < sql/library_management.sql
```

也可以在 MySQL 客户端或 Navicat 中打开该文件并完整执行。重复导入会重建本项目的数据表，请先确认其中没有需要保留的数据。

### 启动后端

根据本机环境设置数据库连接信息。需要使用 DeepSeek 进行语义解析时，再设置对应的 API 密钥。

```powershell
$env:DB_USERNAME = "root"
$env:DB_PASSWORD = "你的数据库密码"
$env:JWT_SECRET = "本地随机密钥"
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API 密钥"
cd backend
mvn spring-boot:run
```

启动后打开 `http://localhost:22090`。默认演示账号为 `admin`、`zhangsan`、`lisi`，密码均为 `123456`。

### 前端开发模式

如需单独调试前端，在 `frontend` 中执行：

```bash
npm install
npm run serve
```

开发服务器地址为 `http://localhost:22091`。

## 图书问答边界

问答功能只处理本馆图书、作者、分类、借阅状态、推荐和馆藏位置相关问题。模型只负责理解查询意图，实际结果来自参数化数据库查询；没有查到的数据不会由模型补写。未配置 DeepSeek API 密钥时，系统使用本地安全解析处理能够确定的馆藏问题。

## 来源

本项目基于课程提供的教学脚手架完成。

原始教学项目：[B站 · 程序员辰星 · Spring Boot + Vue 图书管理系统](https://www.bilibili.com/video/BV16d4JenESJ/)

仓库保留原有 `kmbeast` 包名，用于标识脚手架来源。