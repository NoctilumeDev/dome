# 高校学生宿舍管理系统

本项目于大二暑期独立完成。开发时曾将其视为未来本科毕业设计的一个可能方向，但不代表最终毕业设计选题。

课程与开发过程未要求或讲授 Git，因此项目完成阶段没有 Git 提交历史；本仓库从归档版本开始记录，不补造历史提交。

系统围绕宿舍与床位、入住退宿、报修、账单、公告和数据看板形成完整业务闭环。

## 技术栈

- Spring Boot 2.7、Spring Data JPA、MySQL 8
- 原生 HTML、CSS、JavaScript
- Session 登录与 BCrypt 密码摘要

前端静态页面与后端位于同一个 Maven 项目中，启动一个服务即可。

## 运行

1. 使用 `sql/dormitory_management.sql` 初始化数据库。
2. 设置本机数据库账号和密码。
3. 在项目根目录执行 `mvn spring-boot:run`。
4. 打开 `http://localhost:8660/login.html`。

PowerShell 示例：

```powershell
$env:DB_USERNAME = "root"
$env:DB_PASSWORD = "你的数据库密码"
mvn spring-boot:run
```

默认演示账号：

- `admin / 123456`：管理员
- `manager / 123456`：宿舍管理员
- `student / 123456`：学生

## 主要功能

- 楼栋、楼层、宿舍、床位和用户管理
- 学生注册、登录和角色权限控制
- 宿舍偏好评分与空床推荐
- 入住、退宿、报修和账单流程
- 公告与数据看板

相关计划、模块图、学习指南和开发记录位于 `docs`。
