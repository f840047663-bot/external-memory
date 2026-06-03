# B站抓取

> **输入：** mid（从 `thinkers/INDEX.md` 第3列读，格式 `mid:数字`）
> **输出：** 新视频→保存到 `~/.hermes/work/videos/` → 写 `/tmp/monitor_status.md` 一行

## API请求（副路：curl）
```bash
COOKIE=$(cat ~/桌面/凭证/bilibili_com_cookie_最新.txt)
curl -s -b "$COOKIE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=30"
```

## 主路：Evil0ctal
```python
import asyncio
from douyin_tiktok_scraper.scraper import Scraper

async def fetch():
    s = Scraper()
    result = await s.get_bilibili_video_data('https://www.bilibili.com/video/{BVID}')
    return result

asyncio.run(fetch())
```
**切换逻辑：** 主路超时(>10s)→切副路(curl)。

## 下载新视频
```bash
yt-dlp -f "ba" --cookies ~/.hermes/cookies/bilibili_netscape.txt \
  -o ~/.hermes/work/videos/{UP主}_{BVID}.mp4 "https://www.bilibili.com/video/{BVID}"
```

## ID锚点比对
```
第一级：搜断点BVID在列表中 → 找到→看前面条目，BVID>断点且时间≥断点→算新
第二级：没找到→时间降级（created>断点时间→算新）
```

## 🚨 B站踩坑记录

### 坑1：浏览器兜底对B站SPA页面效果差
B站space页面是SPA，DOM内容靠JS动态渲染。cdp-browser-reader等选择器出现但视频列表是异步API填充的。**B站-799不要走浏览器兜底，优先用skip→retry策略。**

### 坑2：DNS解析失败
`api.bilibili.com`报`Temporary failure in name resolution`→sleep(30s)重试1次，通常恢复。

### 坑3：browser_navigate CDP代理报404
Hermes的CDP代理层有问题，但Chrome CDP端口9222本身是活的。用`cdp-browser-reader.py`直连WebSocket绕过。

### 坑4：-799返回空不能标记"0新"
每个博主必须返回最后一条视频的发布时间+标题，才能跟断点对比。抓不到=抓取失败，不是0新。

## 🚨 B站限流铁律
- 不同博主请求间必须sleep(5-8秒)
- 收到-799必须sleep(15秒)
- **三平台交替**：不准一口气跑完一个平台

## 🚨 步骤末尾：写L1.5（不写=模块没跑完）
```python
ts = datetime.datetime.now().strftime("%H:%M")
line = f"- {ts} [B站抓取 {N}人✅ 新{M}条]\n"
open("/home/fw/.hermes/external_memory/L1.5_工作记忆.md", "a").write(line)
```
