# B站抓取

## 输入
| 参数 | 类型 | 说明 |
|:----|:----|:----|
| mid | 数字 | UP主mid（从thinkers/INDEX.md第四列读） |
| 断点ID | 字符串 | 最后处理视频BVID |
| 断点时间 | 时间戳 | 最后处理视频时间 |

## 输出（返回值）
```
{
  "平台": "B站",
  "UP主": "xxx",
  "状态": "✅/❌",
  "新视频": ["BV号列表"],
  "失败原因": "xxx"
}
```

## 执行步骤

### Step 1：拉视频列表
```bash
COOKIE=$(cat /tmp/bilibili_cookies.txt)
curl -s -b "$COOKIE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=30"
```

### Step 2：ID锚点比对
```
第一级：搜断点BVID在列表中的位置
  ├─ 找到 → 看它前面的条目，BVID>断点 且 时间≥断点时间 → 算新
  └─ 没找到 → 第二级：时间降级（created > 断点时间 → 算新）
```

### Step 3：下载新视频
```bash
# 用yt-dlp下载（需要cookie）
yt-dlp -f "ba" --cookies ~/.hermes/cookies/bilibili_netscape.txt \
  -o ~/.hermes/work/videos/{UP主}_{BVID}.mp4 "https://www.bilibili.com/video/{BVID}"
```

### Step 4：写状态清单
```bash
echo "| B站 | {UP主} | 视频 | ✅/❌ | {N} | videos/{UP主}_{BVID}.mp4 | 待转录/失败-待重试 |" >> /tmp/monitor_status.md
```

## 失败处理
| 故障 | 解决 |
|:----|:-----|
| API返回-799 | sleep(15s)重试1次，还限流→换平台，阶段二回头重试 |
| 连续-799 | 标记"失败-待重试"，阶段二sleep(20s)再试 |
| Cookie过期 | 返回❌，框架调用[通用/环境准备]刷新 |

**🚨 B站限流铁律：**
- 不同博主请求之间必须sleep(5-8秒)
- 收到-799必须sleep(15秒)，不能只sleep(5秒)
- 连续重试同一平台→必须换平台
