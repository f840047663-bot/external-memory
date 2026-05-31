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
| -799限流 | sleep(15s)重试1次→还限流→换平台→阶段二回头重试 |
| 连续-799 | **必须换平台！** 不能连续重试同一平台 |
| Cookie过期 | 返回❌，框架调[环境准备]刷新 |

**🚨 B站限流铁律：**
- 不同博主请求间必须sleep(5-8秒)
- 收到-799必须sleep(15秒)，不能只sleep(5秒)
