# B站抓取

> **输入：** mid, 断点BVID, 断点时间
> **输出：** 新视频列表 → 保存到~/.hermes/work/videos/ → 写/tmp/monitor_status.md一行

## API请求
```bash
COOKIE=$(cat ~/桌面/凭证/bilibili_com_cookie_最新.txt)
curl -s -b "$COOKIE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=30"
```
mid从`thinkers/INDEX.md`第四列读（格式`mid:数字`）。

## ID锚点比对
```
第一级：搜断点BVID在列表中 → 找到→看前面条目，BVID>断点且时间≥断点→算新
第二级：没找到→时间降级（created>断点时间→算新）
```

## 下载新视频
```bash
yt-dlp -f "ba" --cookies ~/.hermes/cookies/bilibili_netscape.txt \
  -o ~/.hermes/work/videos/{UP主}_{BVID}.mp4 "https://www.bilibili.com/video/{BVID}"
```

## 写状态清单
```
有新视频: "| B站 | {UP主} | 视频 | ✅ | {N} | videos/{UP主}_{BVID}.mp4 | 待转录 |"
0新:      "| B站 | {UP主} | 视频 | ✅ | 0 | - | 0新 |"
失败:     "| B站 | {UP主} | 视频 | ❌ | ? | - | 失败-待重试(-799) |"
```

## 失败处理
| 故障 | 解决 |
|:----|:-----|
| -799限流 | sleep(15s)重试1次→还限流→**跳过此平台，换下一个**→阶段二回头重试（冷却时间够了） |
| DNS解析失败 | `api.bilibili.com`临时解析不了→等30s重试1次→还失败→跳过此平台 |
| 连续-799 | **必须换平台！** 不能连续重试同一平台 |
| 阶段二还-799 | 标记"最终失败-待用户处理" |
| Cookie过期 | 返回❌，框架调[环境准备]刷新 |

**🚨 B站限流铁律：**
- 不同博主请求间必须sleep(5-8秒)
- 收到-799必须sleep(15秒)，不能只sleep(5秒)
- **三平台交替原则**：抖音A→B站A→知乎A→抖音B→B站B→知乎B（不准一口气跑完一个平台）

## 🚨 踩坑记录（2026-05-31）

### 坑1：浏览器兜底对B站SPA页面效果差
- **现象：** cdp-browser-reader.py打开`space.bilibili.com/{mid}/video`，返回的text只有"投稿视频-视频分享-哔哩哔哩视频"
- **原因：** B站space页面是SPA（单页应用），DOM内容靠JS动态渲染。cdp-browser-reader等`.card-wrap`选择器出现，但SPA的根容器加载后视频列表是通过异步API填充的，等不到
- **结论：** B站-799**不要走浏览器兜底**，优先用skip→retry策略（等冷却时间）
- **修复：** bilibili_monitor.py已去掉浏览器兜底逻辑，-799直接跳过

### 坑2：DNS解析失败
- **现象：** `api.bilibili.com`报`Temporary failure in name resolution`
- **原因：** 服务器DNS临时故障（非B站限流）
- **处理：** sleep(30s)重试1次，通常恢复。还失败→跳过此平台

### 坑3：browser_navigate CDP代理报404
- **现象：** Hermes的browser_navigate工具报`CDP WebSocket connect failed: HTTP error: 404 Not Found`
- **原因：** Hermes的CDP代理层有问题，但Chrome CDP端口9222本身是活的（`curl http://localhost:9222/json/version`正常）
- **处理：** 用`cdp-browser-reader.py`直连WebSocket绕过，不用browser_navigate

### 坑4：-799返回空不能标记"0新"
- **现象：** API返回-799，脚本输出"0个新"，但根本不知道有没有新视频
- **原因：** 没抓到数据就等同于没数据，是逻辑错误
- **铁律：** 每个博主必须返回最后一条视频的发布时间+标题，才能跟断点对比。抓不到=抓取失败，不是0新
