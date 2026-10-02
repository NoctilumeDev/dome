# 浏览器交互演示

三个项目使用独立的虚构样例数据，写入当前浏览器的 localStorage，可切换身份、体验常用操作并单独重置。这里不运行后端或安全验证，不连接数据库、微信登录或真实模型。宿舍与图书馆复用原有前端；青野的 WXML、WXSS 与页面逻辑在构建时适配为浏览器视图。

入口还包含小游戏 [点睛](../independent-projects/dianjing/)，使用同一份静态游戏代码。在线地址：[项目体验](https://noctilumedev.github.io/dome/)。

图书馆前端安装依赖后，在仓库根目录执行：

```sh
npm ci --prefix coursework/library-management-system/frontend
node --test demo/tests/*.test.mjs
python -m unittest discover -s demo/tests
node demo/build.mjs
python -m http.server 6950 --bind 127.0.0.1 --directory demo/_site
```

打开 `http://127.0.0.1:6950`。GitHub Actions 构建相同的静态文件并发布到 GitHub Pages；构建目录不提交。

修改原项目页面后重新构建即可同步；演示样例与适配代码位于本目录。文件上传和注册使用预置身份替代，问答只做简单样例匹配，不代表完整项目的语言理解能力或权限边界。演示数据可以从控制台修改，不能用于保存真实资料。

三个原项目的登录页包含故障卡片与恢复入口。`tests/login-failures.test.mjs` 直接加载原登录逻辑及请求处理，验证 HTTP 状态、断网、超时、异常响应、输入保留、重试和会话过期；线上静态演示不提供故障注入控件，也不连接真实登录服务。

青野样式转换只替换原生标签，保留 `.page` 等类名及页面内边距；对应回归位于 `tests/test_qingye_converter.py`。
