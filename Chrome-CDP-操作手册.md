# Chrome CDP 操作手册

> **用途：** 所有需要浏览器登录态的操作（提取cookie、抓取网页内容、绕过API限制）都依赖Chrome CDP。
> **最后更新：** 2026-05-31

---

## 一、启动Chrome CDP

### 方式1：systemd用户服务（推荐，持久化）

```bash
# 启用并启动（开机自启）
systemctl --user enable --now chrome-cdp.service

# 查看状态
systemctl --user status chrome-cdp.service

# 重启
systemctl --user restart chrome-cdp.service
```

Service文件位置：`~/.config/systemd/user/chrome-cdp.service`

### 方式2：手动命令行启动

```bash
/opt/google/chrome/chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  --no-sandbox \
  --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" \
  --window-size=1280,720 \
  --noheadless
```

### 启动后验证

```bash
curl -s http://127.0.0.1:9222/json/version
# 应返回 Browser版本 + webSocketDebuggerUrl
```

---

## 二、关键配置

### Chrome参数说明

| 参数 | 作用 |
|:----|:-----|
| `--remote-debugging-port=9222` | CDP调试端口 |
| `--user-data-dir=/tmp/chrome-debug` | 独立配置目录（必须非默认路径） |
| `--no-sandbox` | Ubuntu容器/服务器必需 |
| `--noheadless` | **必须有可见窗口**，用户需要手动登录 |
| `--window-size=1280,720` | 窗口大小，模拟正常浏览器 |

### Hermes配置（关键！）

配置文件：`~/.hermes/config.yaml`

```yaml
browser:
  cdp_url: 'ws://127.0.0.1:9222/devtools/browser/{动态ID}'
```

**⚠️ 核心坑：Chrome每次重启，browser ID都会变！**

- 旧ID → Hermes browser工具报 `404 Not Found`
- **解决脚本：** `~/系统工具/更新Chrome-CDP-ID.sh`
- Chrome重启后必须运行一次：`bash ~/系统工具/更新Chrome-CDP-ID.sh`

---

## 三、调试CDP

### 3.1 检查Chrome是否在运行

```bash
# 方法1：HTTP API
curl -s http://127.0.0.1:9222/json/version

# 方法2：进程
ps aux | grep "chrome.*9222" | grep -v grep
```

### 3.2 查看当前标签页

```bash
curl -s http://127.0.0.1:9222/json | python3 -c "
import sys,json
tabs = json.load(sys.stdin)
for t in tabs:
    if t.get('type')=='page':
        print(f\"{t['id'][:20]}  {t.get('url','(loading)')[:70]}\")
"
```

### 3.3 创建新标签页（CDP工具）

用Hermes的 `browser_cdp` 工具：
```
method: Target.createTarget
params: {"url": "https://目标网站.com"}
```

### 3.4 提取cookie

**方法A：全局提取（推荐）**
```
browser_cdp:
  method: Network.getAllCookies
  params: {}
  target_id: {目标标签页ID}
```

**方法B：用脚本提取**
```bash
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com
# 输出到 ~/桌面/凭证/bilibili_com_cookie_最新.txt
```

### 3.5 Cookie保存位置

| 文件 | 用途 |
|:----|:-----|
| `~/.hermes/cookies/bilibili_netscape.txt` | B站Netscape格式（脚本用） |
| `~/.hermes/cookies/douyin_netscape.txt` | 抖音Netscape格式 |
| `~/.hermes/cookies/zhihu_netscape.txt` | 知乎Netscape格式 |
| `/tmp/bilibili_cookies.txt` | B站关键cookie（简洁版） |
| `/tmp/douyin_cookies.txt` | 抖音关键cookie |
| `/tmp/zhihu_cookies.txt` | 知乎关键cookie |
| `~/桌面/凭证/*_cookie_最新.txt` | 桌面凭证（脚本读取） |

**有效性判断：** Netscape文件 >1000字节 = 有效；<500字节 = 过期需刷新。

### 3.6 常见故障

| 症状 | 原因 | 解决 |
|:----|:-----|:-----|
| `curl 127.0.0.1:9222` 连不上 | Chrome没启动 | 启动Chrome CDP |
| browser工具报 `404 Not Found` | Browser ID变了 | `bash ~/系统工具/更新Chrome-CDP-ID.sh` |
| Chrome窗口不显示 | Wayland问题 | 检查DISPLAY/WAYLAND_DISPLAY环境变量 |
| Chrome被OOM杀了 | 内存不足 | 先`bash ~/桌面/脚本/内存急救.sh`再重启 |
| cookie提取为空 | 没登录 | 在Chrome窗口手动登录目标网站 |
| 标签页全是空白 | URL导航失败 | 用`Target.createTarget`创建新标签页 |

---

## 四、标准操作流程

### 监控前Cookie检查

```
1. 启动Chrome CDP（如果没运行）
2. 运行 bash ~/系统工具/更新Chrome-CDP-ID.sh
3. 检查cookie文件大小：
   ls -la ~/.hermes/cookies/*_netscape.txt
   - >1000字节 → ✅ 有效
   - <500字节 → ❌ 需要刷新
4. 需要刷新 → 用CDP打开目标网站 → 用户登录 → 提取cookie
5. 三个平台都OK → 开始跑监控
```

### 刷新cookie流程

```
1. browser_cdp(Target.createTarget, {"url": "https://www.bilibili.com"})
2. 等用户登录
3. browser_cdp(Network.getAllCookies, {}, target_id={新标签页ID})
4. 过滤目标域名的cookie → 保存Netscape格式到 ~/.hermes/cookies/
5. 同步到 ~/桌面/凭证/（脚本读取路径）
```

---

## 五、相关文件索引

| 文件 | 说明 |
|:----|:----|
| `~/系统工具/更新Chrome-CDP-ID.sh` | 自动更新CDP browser ID脚本 |
| `~/.config/systemd/user/chrome-cdp.service` | systemd服务文件 |
| `~/.hermes/config.yaml` | Hermes配置（cdp_url在此） |
| `00-网站内容抓取总纲.md` | 三平台抓取详细流程 |
| `INDEX.md` §1 | 三平台监控系统概览 |
