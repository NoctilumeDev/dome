# 点睛

一个轻松的「你画我猜」小游戏：AI 创作的内置 SVG 图画逐笔出现，你用中文或英文猜答案。

[开始玩](https://noctilumedev.github.io/dome/dianjing/)

第一版有 20 幅图画，每局随机 5 题，每题 60 秒。支持两次提示、跳过、得分结算和浏览器最高分。切到后台暂停计时；开启减少动态效果时直接显示图画。

使用 Python 标准库和原生 HTML / CSS / JavaScript，不需要安装依赖、配置 API Key 或数据库。题目来自内置题库，答案按预设中文、英文别名匹配，当前没有实时大模型识图、在线生图或多人房间。最高分仅保存在当前浏览器，这是休闲小游戏，不做防作弊排行榜。

## 本地运行

需要 Python 3.10 或更高版本，在本目录运行：

```sh
python server.py
```

打开 `http://127.0.0.1:6951`，按 Ctrl+C 停止。端口可用 `python server.py --port 6952` 调整。`static/` 也可以放到任意静态服务器，GitHub Pages 使用同一份代码。

## 文件与验证

- `static/puzzles.mjs`：图画、答案别名和提示，可直接加题。
- `static/game.mjs`：抽题、猜测、计分与轮次规则。
- `static/app.mjs`：逐笔动画、页面交互和计时。
- `server.py`：仅提供静态页面，不接收玩家输入。

```sh
node --test tests/game.test.mjs
python -m unittest discover -s tests
```
