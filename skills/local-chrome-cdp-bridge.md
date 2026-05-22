---
name: local-chrome-cdp-bridge
description: 【核心技能】Chrome v147+ 唯一能提取登录cookie的方案。CDP 只做cookie提取→存文件→curl调API，浏览器不用于数据抓取（token太贵）。
---

# Local Chrome CDP Bridge

## 一句话定位

Chrome v147+（本机）的**唯一** cookie提取方案。yt-dlp已废（v11加密不可破解），不走CDP就没cookie。

**判断逻辑：**
```bash
# 先查版本
google-chrome --version
# ≥147 → 本技能  |  <147 → cookie-extractor (yt-dlp)
```

## ⭐ 解耦模式：CDP只拿cookie → 存文件 → curl调API（核心原则）

**这是最核心的模式，比下面所有内容都重要。**

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Chrome    │────→│ cookie   │────→│ curl 调  │
│ CDP       │     │ 存桌面   │     │ 网站API  │
│ (仅拿     │     │ .txt     │     │ (搜索/读 │
│  cookie)  │     │          │     │ 文章等)  │
└──────────┘     └──────────┘     └──────────┘
 只做这一步       再也不碰CDP      主力工作模式
```

**铁律：** CDP启动的浏览器不用于任何数据抓取。它只是cookie提取器。拿完cookie就关。

### 本机快速启动（Wayland / Ubuntu 22.04）

```bash
# ✅ 正确方式（一次性）
rm -rf /tmp/chrome-debug
mkdir -p /tmp/chrome-debug
ln -sf ~/.config/google-chrome/Default /tmp/chrome-debug/Default 2>/dev/null
WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  --ozone-platform=wayland \
  --window-size=1,1

# 或者用现成脚本
~/.hermes/scripts/cdp-auto-cookies.sh <域名>
```

### ⚠️ 典型操作用例：知乎搜索用户

```bash
COOKIE=$(cat ~/桌面/zhihu_com_cookie_最新.txt)

# 搜用户
curl -s "https://www.zhihu.com/api/v4/search_v3?q=名字&t=people&limit=5" \
  -H "Cookie: $COOKIE" -H "User-Agent: Mozilla/5.0 ..."

# 读文章列表
curl -s "https://www.zhihu.com/api/v4/members/{user_id}/articles?limit=20" \
  -H "Cookie: $COOKIE"
```

**不踩的坑：** 
- ❌ 不要用CDP浏览器去知乎搜索 → 没登录态返回空
- ❌ 不要自己开headless → 没cookie
- ✅ 用桌面已有cookie文件直接调API

### 本机已有cookie文件一览

| 域名 | 文件路径 |
|:----|:---------|
| 知乎 | `~/桌面/zhihu_com_cookie_最新.txt` |
| 抖音 | `~/桌面/douyin_com_cookie_最新.txt` |
| B站 | `~/桌面/bilibili_com_cookie_最新.txt` |
| GitHub | `~/桌面/github_com_cookie_最新.txt` |

这些cookie有效期约7-30天，过期再跑CDP重新提取。

---

## ⚠️ 内容获取三层优先级（2026-05-21 用户确立铁律）

用户明确要求获取网络内容时按此顺序，不得跳级：

| 优先级 | 方式 | token消耗 | 何时用 |
|:------|:-----|:---------|:-------|
| 🥇 **API + cookie** | curl调网站API | 零token | 主力，平时都用这个 |
| 🥈 **CDP提取cookie → API** | 连用户Chrome拿cookie → 存文件 → 继续调API | 偶尔一次拿cookie | API不通时（cookie过期/未登录） |
| 🥉 **浏览器直接操作** | browser_navigate/click/snapshot 读内容 | 高（页面渲染+操作） | API和cookie都搞不定时，最后手段 |

**用户原话：** *"能调API的就调API，不能调API的手段，你获取到cookie之后再来调API，实在没办法的时候，你再用浏览器来整。用浏览器来整token消耗非常高。"*

### 核心原则

1. **API是默认模式** — 所有网站内容获取优先走curl+存好的cookie
2. **CDP只用来拿cookie，不是替代API** — 连用户Chrome、拿cookie、断连、存文件，然后继续走API
3. **浏览器工具是最后手段** — token高、可能被反爬、慢，只有API彻底搞不定才用
4. **连用户的Chrome，不是自己开headless** — 用户反复强调不要自己开一个没登录态的Chrome

### 检查当前CDP配置

```bash
grep cdp_url ~/.hermes/config.yaml
# 空字符串 → 没连用户Chrome，自己开headless（用户不接受的错误状态）
# ws://127.0.0.1:9222 → 正常
```

## CDP提取cookie全流程（当API不通时）

**场景：** cookie过期了 / 要读新网站。**全程AI执行，用户不用管。**

### Step 0: 先试现有cookie

```bash
curl -s --connect-timeout 5 -H "Cookie: $(cat ~/桌面/zhihu_com_cookie_最新.txt 2>/dev/null)" \
  "https://www.zhihu.com/api/v4/me" | grep -c '"name"'
# 返回1 → cookie有效，直接用
# 返回0 → 执行下面
```

### Step 1: 启动Chrome调试模式

**⚠️ 铁律：Wayland环境下必须设对环境变量，不要设DISPLAY=:0**

```bash
# ✅ 正确（Wayland）
WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  --ozone-platform=wayland \
  --window-size=1,1 &
```

```bash
# ❌ 错误（Wayland下会报Missing X server）
DISPLAY=:0 google-chrome --remote-debugging-port=9222 ...
```

用自动化脚本 `~/.hermes/scripts/cdp-auto-cookies.sh`（2026-05-21新增，2026-05-22补入技能）：

```bash
# 快速拿指定域名的cookie
~/.hermes/scripts/cdp-auto-cookies.sh zhihu.com
# 脚本会自动：起Chrome → 等端口 → 拿cookie → 关Chrome → 存到桌面
```

或者手动分步操作：

```bash
# ① 清理旧profile + 杀旧调试Chrome
rm -rf /tmp/chrome-debug
mkdir -p /tmp/chrome-debug
# ⚠️ 下面的symlink复制用户登录态，但Chrome运行中时锁文件会导致失败。
# 更可靠的做法：直接启动独立实例（无登录态，只拿cookie，后面用cookie调API即可）
# 或者：先杀用户Chrome（必须问用户）后重启带CDP
kill $(ps aux | grep 'chrome.*remote-debugging-port=9222' | grep -v grep | awk '{print $2}') 2>/dev/null

# ② 用crontab启动（Wayland下唯一可靠方式）
# ✅ 这个方法的好处：即使用户的Chrome正在运行，也能启动独立CDP实例
# （因为用了 /tmp/chrome-debug 作为独立数据目录）
crontab -l | grep -v "remote-debugging\\|chrome-debug\\|One-shot" > /tmp/cron_new
echo "# Chrome CDP" >> /tmp/cron_new
echo "$(date -d '+1 minute' '+%M %H %d %m *') WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus google-chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=/tmp/chrome-debug --no-first-run --ozone-platform=wayland > /tmp/chrome_cdp.log 2>&1" >> /tmp/cron_new
crontab /tmp/cron_new
rm /tmp/cron_new
```

### Step 2: 等9222端口就绪

```bash
for i in $(seq 1 30); do
  curl -s --connect-timeout 2 http://127.0.0.1:9222/json/version && echo "OK" && break
  sleep 4
done
```

### Step 3: 提取cookie

```bash
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --test --output ~/桌面/
```

### Step 4: 用cookie干活

```bash
# Header格式（最常用）
curl -H "Cookie: $(cat ~/桌面/zhihu_com_cookie_最新.txt)" \
  "https://www.zhihu.com/api/v4/me"
```

### Step 5: 关掉临时Chrome

```bash
kill $(ps aux | grep 'chrome.*remote-debugging-port=9222' | grep -v grep | awk '{print $2}') 2>/dev/null
```

## 场景二：读取网页/视频内容（CDP Page Reader）

**使用场景：** 需要读取已登录页面内容（抖音视频章节摘要、知乎隐藏内容、登录后才能看到的文章）。

### 原理

CDP 可以在浏览器中打开目标 URL，等页面加载后提取 AI 生成的章节摘要/纯文本内容。**不需要下载视频，不需要转录**。对抖音视频尤其有效——抖音的 AI 自动生成章节摘要功能可以在 CDP 读取到。

### 脚本

`~/.hermes/scripts/read_douyin_video.py`

**用法：**
```bash
python3 ~/.hermes/scripts/read_douyin_video.py "https://www.douyin.com/video/{aweme_id}"
```

**返回内容（已验证 2026-05-19）：**
- TITLE: 页面标题（可能为空）
- HTML_LEN: 页面 HTML 长度（约 1MB → 页面已完整加载）
- CONTENT: 页面纯文本，包含 AI 生成的章节要点

**抖音 AI 章节摘要示例输出：**
```
章节要点：共4个
流动性与产业链的关系
  流动性与产业链是两个维度，流动性收紧会对市场造成影响
市场传导的时间
  市场传导时间有滞后，投资者需正确预估
风险低估的后果
  低估风险可能导致连锁反应
市场现状分析
  市场过于关注AI产业链，忽略能源、地缘政治等因素，风险偏好已达极值
内容由AI生成
```

### 工作流

```
需要读取抖音视频内容
  → 确认 Chrome CDP 端口 9222 已就绪
  → python3 read_douyin_video.py <URL>
  → 等待 10-15 秒（页面加载+AI章节生成）
  → 提取 CONTENT 中的章节要点
  → 更新分析结果到 events/ 和 positions/
```

### ⚠️ 要点

1. **需要 Chrome CDP 端口已就绪** — 如果端口未就绪，先按「CDP提取cookie全流程」的 Step 1-2 启动
2. **等待时间要够** — 抖音页面加载需要 8-10 秒，AI 章节摘要需要页面渲染完成后才能提取
3. **抖音可能弹验证码** — 如果返回 `验证码中间页`，说明需要重新登录（约7-30天一次）
4. **关闭打开的页面** — 脚本自动关闭新标签页，不需要手动清理
5. **CDP 端口不能同时跑多个** — 多个并发的 CDP 请求可能导致冲突
6. **环境就绪检查** — 执行 CDP 操作前先跑 preflight-check.sh 确保系统资源充足

### ⚡ 铁律：遇到CDP问题 → 先加载本技能，不要闷头试（2026-05-22 用户纠正）

当需要启动Chrome/CDP时，**必须先加载本技能（skill_view）**，里面已有：
- 完整的Wayland环境变量（`WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/run/user/1000`）
- **不能设DISPLAY=:0**（Wayland下会Missing X server）
- 现成的启动脚本 `cdp-auto-cookies.sh`
- crontab启动方案（见 `references/chrome-restart-crontab.md`）

**禁止的行为：**
- ❌ 不加载技能就自己试启动参数（试一个错一个，浪费多步）
- ❌ 设 `DISPLAY=:0`（Wayland X11变量无效）
- ❌ 不加 `--ozone-platform=wayland`
- ❌ 闷头试多个方案不出声（用户原话：*"怎么时好时坏的cdb搜不能搜吗"* → 先汇报状态再行动）

**正确的流程：**
```
用户说"搜一下XX" / "CDP搜啊"
  → ① skill_view('local-chrome-cdp-bridge') 加载本技能
  → ② 诊断CDP状态并立即汇报（一句话说清楚：通了/没通）
  → ③ 按技能步骤操作
  → ④ 每5-10分钟汇报进度，不要闷头干
```

### 本技能的核心脚本

`~/.hermes/scripts/cdp-get-cookies.py` — 通用，`--domain` 支持任何网站，`--test` 自动验证
`~/.hermes/scripts/cdp-read-page.py` — 通用页面读取（初版，可读任何 URL）
`~/.hermes/scripts/read_douyin_video.py` — 抖音视频内容专用（等待时间长+异常处理更完善）
`~/.hermes/scripts/cdp-auto-cookies.sh` — 一键自动化：起Chrome→拿cookie→关Chrome（2026-05-22 补入技能档案，注意Wayland环境变量的正确设置）

## 场景三：连接Hermes内置浏览器工具到用户Chrome（2026-05-21 新增）

**核心问题：** Hermes Agent 的内置浏览器工具（browser_navigate、browser_click、browser_type等）默认自己启动一个headless Chrome。用户反复强调：**不要自己开headless，要连他的Chrome**。连他的Chrome才能用他的登录态（书签、cookies、反爬豁免）。

### 配置方法

在 `~/.hermes/config.yaml` 中设置cdp_url指向用户Chrome：

```yaml
browser:
  cdp_url: 'ws://127.0.0.1:9222'
  inactivity_timeout: 120
  command_timeout: 30
  engine: auto
```

改完需要重启Hermes agent。

### 前提条件

用户Chrome必须已启动并监听9222端口：

```bash
curl -s --connect-timeout 3 http://127.0.0.1:9222/json/version
# 返回JSON → 可连  |  超时/拒绝 → 用户Chrome没开调试端口
```

### 启动用户Chrome调试端口

桌面已放置脚本 `~/桌面/启动Chrome调试模式.sh`，用户双击即可启动带调试端口的Chrome（用他的正常配置、书签、登录态全在）。

### ⚠️ 铁律：CDP不通时先诊断+汇报，不闷头试其他方案（2026-05-22 用户纠正信号）

**场景：** user说"搜一下XX" 或 "CDP搜啊" — 需要浏览器访问内容。

**正确流程：**
```
① 先查Chrome进程 + CDP端口
   pgrep -af chrome  → 看Chrome有没有运行
   ss -tlnp | grep 9222  → 看CDP端口是否监听
   
② 结果直接汇报给用户，一句话说清楚：
   ✅ Chrome运行中 + 9222就绪 → 直接开搜
   ❌ Chrome未运行/9222不通 → "Chrome没开CDP，你那边开一下？"
   ❌ Chrome运行中但9222不通 → "Chrome在跑但没开调试端口，需要重启带CDP"

③ 不要做：
   ❌ 用户说要搜 → 闷头用curl/Bing/其他方法试半天 → 用户问"怎么没反应"
   ❌ 先试API/WAF-bypass/RSSHub一圈 → 最后才说CDP不通
   ❌ 用户问"CDP搜吗" → 答"CDP不通"但没有主动提供解决办法
```

**核心原则：** 用户问某个渠道能不能用→诊断后直接给出**结论+下一步**，不要默默换渠道。

## 坑（必读）

1. **不要自己开headless Chrome** — 用户原话：*"意思就是说你用的cdp是操作你自己的浏览器，不是操作我的是吧？"* 自己开一个没有登录态的Chrome等于白干，用户不接受。
2. **9222连不上时 = 用户Chrome没开** — 正常情况。此时浏览器工具不可用，退回到「🥇 API + 存好的cookie」。**但要先汇报给用户，不闷头干。**
3. **不要杀用户正在用的Chrome** — 用户在浏览时杀Chrome会让他丢失工作。如需重启必须问用户。
4. **用户不开Chrome也可以工作** — 用存的cookie文件调API即可，大部分场景不需要浏览器。
5. **⚠️ CDP启动的独立Chrome实例没有用户登录态** — 即使`ln -sf`了Default配置目录，Chrome v147+将cookie存在OS keyring而非SQLite文件。所以：
   - 用`cdp-auto-cookies.sh`启动的Chrome → 知乎搜人返回空
   - **正确做法：直接用桌面已有的cookie文件调API**（见上方「解耦模式」章节）
   - CDP只用来提取新cookie（当旧的过期时），不用于任何内容读取
6. **⚠️ Wayland下必须``不要设DISPLAY=:0``** — 设了X11变量会导致"Missing X server"崩溃。只设`WAYLAND_DISPLAY=wayland-0`和`XDG_RUNTIME_DIR=/run/user/1000`。

### 工作流决策树

```
需要获取网页/视频内容
  → 有API吗？
    → 有 → curl + cookie文件 → 完成 ✅（零token）
    → 没有 → 
      → cookie文件过期了吗？
        → 过期 → 启动CDP临时Chrome → 拿cookie → 关Chrome → curl + 新cookie → 完成 ✅
        → 没过期 → 直接curl → 完成 ✅
      → 还是没有API？
        → 用户Chrome 9222开了吗？
          → 开 → browser_navigate 读页面 → 完成 ⚠️（高token）
          → 没开 → 告诉用户：需要开Chrome调试模式才能读这个
```

## 铁律（必读）

1. `--remote-allow-origins=*` **必须加**，否则Python WebSocket连不上
2. `--user-data-dir` 必须用非默认目录（用`/tmp/chrome-debug`），否则Chrome拒绝开调试端口
3. **不要杀用户正在用的Chrome** — 用户可能在浏览。先报备，用户允许了再重启
4. **Chrome重启会闪一下** — 正常，标签页自动恢复
5. **cookie约7-30天过期** — 过期重跑即可，用户登录态保持就不用再手动登录
6. **"昨天能用今天不行"** → 先查Chrome版本，大概率自动升级了
7. **不要在v11解密上浪费工具调用** — 超过3次就切CDP。v11是Chromium内部加密，外部无解
8. **CDP操作前先跑 preflight-check.sh** — 系统资源不足时CDP会超时或让系统更卡
9. **⚠️ "正在现有的浏览器会话中打开" 陷阱** — 这是最常见也最隐蔽的失败模式。当用户的Chrome**已经在运行**时（几乎永远如此），执行 `google-chrome --remote-debugging-port=9222` **不会**启动新的调试实例，而是静默地在已有Chrome中打开一个新标签页。`--remote-debugging-port` 参数被完全忽略，9222端口不会被监听。表现：
   - `ss -tlnp | grep 9222` 返回空
   - 系统日志显示 "Opening in existing browser session"（中文/英文）
   - CDP WebSocket连接报 `Connection refused`
   **修复方法：** 要么先杀已有Chrome（必须问用户！），要么用独立 `--user-data-dir=/tmp/chrome-debug` 方案。不要连续重试——每次调用只是开新标签页，越开越多。`cdp-auto-cookies.sh`用 `/tmp/chrome-debug` 独立目录可以在一定程度上避免此问题。

10. **⚠️ Wayland环境坑（2026-05-22 本人在此摔过7步）** 
    - ❌ **不要设 `DISPLAY=:0`** → 会报 `Missing X server or $DISPLAY` + `Authorization required, but no authorization protocol specified`
    - ❌ **不要只加 `--ozone-platform=wayland` 但不设环境变量** → Chrome静默启动但端口不通（进程跑着但不监听9222，因为没连上Wayland显示服务器）
    - ✅ **必须同时设：** `WAYLAND_DISPLAY=wayland-0` + `XDG_RUNTIME_DIR=/run/user/1000` + `--ozone-platform=wayland`
    - ✅ **直接运行 `cdp-auto-cookies.sh`** 或参考 `references/chrome-restart-crontab.md`

## 关联技能

| 技能 | 用途 |
|------|------|
| `bilibili-video-pipeline` | B站视频处理（API取列表→下载→ASR转文字→分析） |

B站的API需要cookie才能获取UP主视频列表（防rate limit）。流程：
CDP拿cookie → 存/tmp/bili_cookies.txt → 调space/arc/search API → 下载+ASR

## 完整流程索引

```
遇到需要获取内容（不限于登录态）
  → 先走🥇API+cookie → 不行走🥈CDP拿cookie → 最后🥉浏览器
  → 查00-网站内容抓取总纲.md
  → 本技能：Chrome v147+ CDP全自动提取
  → cookie存到 ~/桌面/{domain}_cookie_最新.txt
  → 调目标网站API
```

## 兜底方案：CDP不可用时的cookie文件直读

**场景：** Chrome 9222端口未监听，现有桌面cookie文件存在。

```bash
# Step 1: 直接试桌面cookie文件
ls ~/桌面/*cookie*_最新.txt 2>/dev/null
# 预期: douyin_com_cookie_最新.txt, zhihu_com_cookie_最新.txt

# Step 2: 用cookie调API验证
curl -s --connect-timeout 5 -H "Cookie: $(cat ~/桌面/douyin_com_cookie_最新.txt 2>/dev/null)" \
  "https://www.douyin.com/aweme/v1/web/aweme/post/?sec_user_id=TEST&count=1&aid=1128" | grep -c '"status_code":0'
# 返回1 → cookie有效

# Step 3: 复制到/tmp供脚本读取
cp ~/桌面/douyin_com_cookie_最新.txt /tmp/douyin_cookies.txt
```

### ⚠️ 格式陷阱：桌面cookie是Header格式，不是Netscape格式

桌面cookie文件格式为 `key=value; key=value; ...`（HTTP Header格式）。
**不是** `MozillaCookieJar` 兼容的Netscape格式。

当脚本使用 `MozillaCookieJar.load()` 读取时，会报错：
```
LoadError: '/tmp/douyin_cookies.txt' does not look like a Netscape format cookies file
```

**修复（2026-05-20 douyin-monitor.py）：** `get_cookie_str()` 改为双格式兼容，先试Netscape，失败则读raw header。

---

- `00-网站内容抓取总纲.md` — 完整执行链 + 三件套积木选择逻辑
- `cookie-extractor` — Chrome < v147 的轻量方案
- `waf-bypass` — 被WAF拦截时用手机UA绕过
- `references/douyin-video-chapters.md` — 用CDP读抖音视频AI章节摘要（替代下载转录）
- `references/cookie-encryption.md` — Chrome v11 cookie加密机制解密记录