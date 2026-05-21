# B站视频处理管线（解耦版）

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`bilibili-video-pipeline`

## 设计原则

独立模块组合：①拿cookie→②拉UP主视频列表→③取视频信息→④下载音频→⑤ASR转文字→⑥分析提炼。每步可独立调用、独立替换、独立调试。

```
┌────────────────────────────────────────────────┐
│            用户需求                             │
│  "付鹏最近有什么新视频"                          │
│         │                                      │
│         ▼                                      │
│  ┌─────────────┐    ┌──────────────────┐       │
│  │ 模块A: 拿cookie │──→│ 模块B: 拉UP主列表 │       │
│  │ (cdp-get-cookies)│   │ (space/arc/search)│      │
│  └─────────────┘    └────────┬─────────┘       │
│                              │ 选视频           │
│                              ▼                  │
│  ┌─────────────┐    ┌──────────────────┐       │
│  │ 模块C: 取字幕  │←──│ 模块D: 视频信息API  │       │
│  │ (API直取)    │   │ (/x/web-interface)│       │
│  └──────┬──────┘    └──────────────────┘       │
│         │无字幕                                 │
│         ▼                                       │
│  ┌─────────────┐    ┌──────────────────┐       │
│  │ 模块E: 下载音频│──→│ 模块F: ASR转文字   │       │
│  │ (yt-dlp)    │   │ (VideoCaptioner)  │       │
│  └─────────────┘    └────────┬─────────┘       │
│                              │                   │
│                              ▼                   │
│  ┌────────────────────────────────┐             │
│  │ 模块G: LLM分析→存events/       │             │
│  │        →有持仓相关→更新positions/│             │
│  └────────────────────────────────┘             │
└────────────────────────────────────────────────┘
```

- **每步独立：** 改API换header不管其他模块，换ASR引擎不管下载部分
- **可跳过：** 有字幕就直接从模块C拿文本，不走E/F
- **可复原：** 每步失败重试该步，不重跑前面

---

## 模块A：获取B站cookie

调用通用cookie模块（见 `skills/cdp-cookie-extractor.md`）：

```bash
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com --output /tmp/bili_cookies.txt
```

**输出：** `/tmp/bili_cookies.txt` + 桌面备份
**有效期：** 约7-30天，过期重跑

---

## 模块B：拉取UP主视频列表

```bash
# 参数: MID=UP主UID
MID=3546832705685582  # 财经大咖录
BILI_COOKIE=$(cat /tmp/bili_cookies.txt)

curl -s "https://api.bilibili.com/x/space/arc/search?mid=$MID&ps=30&pn=1&order=pubdate" \
  -H "User-Agent: Mozilla/5.0 Chrome/147" \
  -H "Referer: https://space.bilibili.com/$MID" \
  -H "Cookie: $BILI_COOKIE"
```

**输出：** 视频列表JSON（title/BV号/时长/播放量/发布时间）
**筛选：** 按关键词过滤标题（如"付鹏"、"沃什"）

### 已记录的UP主UID

| UP主 | UID | 备注 |
|------|-----|------|
| 财经大咖录 | 3546832705685582 | 付鹏/洪灝等大咖 |

### 搜索新UP主的UID

```bash
curl -s "https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword=UP主名" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Cookie: $BILI_COOKIE"
```

---

## 模块C：获取视频字幕（API直取，零token）

```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BVxxxxxx" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, json, urllib.request
d = json.load(sys.stdin)
sub = d.get('data',{}).get('subtitle',{}).get('list',[])
if sub and sub[0].get('subtitle_url'):
    url = 'https:' + sub[0]['subtitle_url']
    text = ''.join([b['content'] for b in json.loads(urllib.request.urlopen(url).read()).get('body',[])])
    print(text)
else:
    print('NO_SUBTITLE')
"
```

**输出：** 字幕文本（如有），或 "NO_SUBTITLE"
**决策：** 有字幕→直接取文本，走模块G分析。无字幕→走模块E/F

---

## 模块D：获取视频基本信息

```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BVxxxxxx" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, json
d = json.load(sys.stdin)
data = d.get('data',{})
print('标题:', data.get('title','?'))
print('描述:', data.get('desc','?')[:200])
print('时长:', data.get('duration','?'))
print('播放:', data.get('stat',{}).get('view',0))
"
```

---

## 模块E：下载B站音频

```bash
yt-dlp -f "ba" -o "/tmp/bili_video.%(ext)s" "https://www.bilibili.com/video/BVxxxxxx/"
```

**输出：** `/tmp/bili_video.m4a`（约10MB/10分钟音频）

---

## 模块F：VideoCaptioner ASR转文字

### 前置条件
- VideoCaptioner Docker容器在运行
- 命令前加 `sg docker -c "..."`

### 步骤

```bash
# ① 复制音频进容器
sg docker -c "docker cp /tmp/bili_video.m4a videocaptioner:/app/temp/video.m4a"

# ② 容器内转mp3
sg docker -c "docker exec videocaptioner ffmpeg -i /app/temp/video.m4a -vn -acodec libmp3lame -q:a 2 /app/temp/video.mp3 -y"

# ③ 写入转录脚本（容器重启/清理后需要重新写入）
sg docker -c "docker cp /tmp/transcribe.py videocaptioner:/app/temp/transcribe.py"

# ④ 执行转录
sg docker -c "docker exec videocaptioner python3 /app/temp/transcribe.py /app/temp/video.mp3 /app/temp/video"

# ⑤ 取回结果
sg docker -c "docker cp videocaptioner:/app/temp/video_全文.txt /tmp/bili_transcript.txt"

# ⑥ 清理
sg docker -c "docker exec videocaptioner rm -f /app/temp/video.* /app/temp/transcribe.py"
```

### transcribe.py 内容（存于 /tmp/transcribe.py）

```python
import sys
sys.path.insert(0, '/app')
from app.core.bk_asr.transcribe import transcribe
from app.core.entities import TranscribeConfig, TranscribeModelEnum
video = sys.argv[1]; output_base = sys.argv[2]
config = TranscribeConfig(transcribe_model=TranscribeModelEnum.BIJIAN, transcribe_language='zh', use_asr_cache=True)
result = transcribe(video, config)
with open(output_base + '.srt', 'w', encoding='utf-8') as f: f.write(result.to_srt())
segments = result.split_to_word_segments()
full_text = ''.join([s.transcript.strip() for s in segments if s.transcript.strip()])
with open(output_base + '_全文.txt', 'w', encoding='utf-8') as f: f.write(full_text)
```

---

## 模块G：分析提炼→喂入 thinker-info-to-belief 流程

### 输出路径（与抖音信息一致）

```
① events/{日期}-B站-{视频简名}.md    ← 完整分析报告
② thinkers/{UP主}.md                  ← 追加最新观点+信念影响
③ positions/{资产}.md                 ← 如有持仓影响→贝叶斯更新
④ 23-贝叶斯更新日志.md                ← 如有P值变化→追加一行
```

### 分析步骤

1. 读转录文本 → 提炼3-5条核心观点 + 关键数据 + 金句
2. 识别观点属于哪个 **thinker档案**（付鹏→thinker-fupeng.md）
3. 识别观点影响哪些 **持仓**（按资产逐个分析：🟢利好/🟡中性/🔴利空）
4. 如需贝叶斯更新 → 走 thinker-info-to-belief 流程
5. 保存到 events/{日期}-B站-{视频简名}.md

### 与抖音信息流的合并

- **同一UP主**（如付鹏）的B站视频和抖音视频 → 合并进同一个 thinker-fupeng.md
- **同一观点**重复出现 → 取最清晰的一次记录，不重复写
- **新观点** → 追加到最新观点区，更新对持仓的影响表
- B站来源在日期后标注 `（B站·渠道名）` 以区分

### 互锁检查

处理完B站视频后必须检查：
- [ ] events/ 写了吗？
- [ ] thinkers/ 追加了吗？
- [ ] positions/ 有更新贝叶斯吗？
- [ ] 23-贝叶斯更新日志.md 更新了吗？

---

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| API返回空/限流 | 未带cookie | 跑模块A拿cookie |
| cookie过期 | 7-30天后失效 | 重跑模块A |
| yt-dlp下载失败（格式不可用） | 需登录 | 加 `--cookies /tmp/bili_cookies.txt` |
| ASR失败（DNS错误） | 必剪API偶发 | 重试1-2次 |
| 容器不存在 | 没启动VideoCaptioner | 启动容器 |

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `/tmp/transcribe.py` | ASR转录脚本（需复制进容器） |
| `/tmp/bili_cookies.txt` | B站cookie（模块A产出） |
| `events/{日期}-B站-{视频名}.md` | 分析结果存储 |
| `positions/{资产}.md` | 持仓更新（若观点影响P值） |
