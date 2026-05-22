# Local Chrome CDP Bridge

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`local-chrome-cdp-bridge`（devops分类）

## 一句话

Chrome v147+ 唯一的cookie提取方案。CDP只做提取cookie→存文件→curl调API，浏览器不用于数据抓取。

## 前置条件

- Chrome已启动调试模式（端口9222）
- 启动脚本：`~/桌面/启动Chrome调试模式.sh`

```bash
# Wayland下正确启动方式（不设DISPLAY）
google-chrome --remote-debugging-port=9222 --no-first-run &
```

## 验证CDP连接

```bash
curl -s http://localhost:9222/json/version | python3 -m json.tool
# 如果返回 "Browser": "Chrome/..." 说明连接成功
```

## 核心操作

### 提取cookie

```bash
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --output ~/桌面/zhihu_com_cookie_最新.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com --output ~/桌面/bilibili_com_cookie_最新.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output ~/桌面/douyin_com_cookie_最新.txt
```

### 验证cookie

```bash
# 知乎
curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" "https://www.zhihu.com/api/v4/me"
# 应该返回你的用户信息，而不是登录页
```

### 通过CDP抓取页面内容（当API不够用时的兜底方案）

```bash
# 用Runtime.evaluate获取页面文本
python3 ~/.hermes/scripts/cdp-get-page-text.py --url "https://zhuanlan.zhihu.com/p/{article_id}" --output /tmp/page.txt
```

## Wayland兼容性

| 环境 | DISPLAY | 能否启动 |
|------|---------|---------|
| X11 | `:0` | 能 |
| Wayland | **不设**DISPLAY | 能 |
| Wayland | `:0` | **报错崩溃** |

**铁律：** Wayland下绝对不要设DISPLAY环境变量。

## 排障

| 症状 | 原因 | 解法 |
|------|------|------|
| curl 9222连接拒绝 | Chrome未启动/端口不对 | 确认Chrome正在运行 |
| 提取的cookie不全 | 目标tab未登录 | 先在Chrome登录对应网站 |
| 页面上无内容 | DOM未加载完 | 用Page.navigate + 等待后Runtime.evaluate |
| GPU/GL报错 | Wayland兼容性 | 加 `--disable-gpu` 启动 |
