---
name: videocaptioner-auto-transcribe
title: VideoCaptioner 自动转文字
description: >-
  通过 Docker 直接调用 VideoCaptioner (卡卡字幕助手) 容器的必剪 ASR 引擎，
  完成视频→音频→转录→取回文字的全自动流程。不启动浏览器，不依赖 Playwright/Streamlit UI。
triggers:
  - 用户要求将视频转文字/提取字幕
  - 需要批量处理抖音、B站等平台的视频
  - 用户要求提炼B站视频的核心观点
  - 需要自动从视频生成文字分析报告（不只是原文）
  - 任何需要调用视频转录的场景（不管视频来源）
---

# VideoCaptioner 自动转文字（Docker ASR 方案）

## 🚨 重要：Docker ASR 是唯一推荐方案

> **Playwright/Streamlit UI 浏览器自动化方案已弃用。** 该方案（2026-05-10版本）需要启动 Chrome 图形界面、操作复杂、Streamlit 元素选择器不稳定、`set_input_files` 容易超时。已被 Docker 直接调用 ASR 替代。

**当前已验证通过的方案**：将视频复制进容器 → ffmpeg 提取音频 → 调用容器内 Python 脚本（必剪引擎）→ 取回转录结果。全程无需浏览器，稳定可靠，已验证 5 次（最长 11,369 字）。

## 前置条件

- VideoCaptioner Docker 容器运行中（`ghcr.io/weifeng2333/videocaptioner:latest`，端口 8501）
- 视频文件已下载到本地（如 `/tmp/video.mp4`）
- 容器内有 `transcribe.py` 脚本（见下方「写入转录脚本」）
- 用户属于 docker 组 → 命令前加 `sg docker -c "..."`

## Docker 权限

用户属于 docker 组，但直接 `docker` 有权限问题。**必须用 `sg docker -c` 包装：**

```bash
# ✅ 正确
sg docker -c "docker exec videocaptioner ls /app/"
sg docker -c "docker cp /tmp/video.mp4 videocaptioner:/app/temp/"

# ❌ 错误
docker exec videocaptioner ls /app/       # permission denied
```

## ⚠️ 铁律：输出必须是分析报告，不是原文

用户明确要求：**不要只丢原始字幕或全文**。必须提炼：核心观点、值得注意的点、金句、跨源对比。原始SRT字幕作为附件备查即可。

## 完整流程（5步）

### 第1步：复制视频进容器

```bash
sg docker -c "docker cp /tmp/video.mp4 videocaptioner:/app/temp/video.mp4"
```

### 第2步：用 ffmpeg 提取音频

VideoCaptioner 只支持音频格式，所以先提音频：

```bash
sg docker -c "docker exec videocaptioner ffmpeg -i /app/temp/video.mp4 -vn -acodec libmp3lame -q:a 2 /app/temp/video.mp3 -y"
```

### 第3步：写入 / 确认转录脚本

先在 /tmp 准备 transcribe.py：

```python
import sys
sys.path.insert(0, '/app')
from app.core.bk_asr.transcribe import transcribe
from app.core.entities import TranscribeConfig, TranscribeModelEnum

video = sys.argv[1]          # 音频文件路径（如 /app/temp/video.mp3）
output_base = sys.argv[2]    # 输出前缀（如 /app/temp/video）

config = TranscribeConfig(
    transcribe_model=TranscribeModelEnum.BIJIAN,  # 必剪，免费
    transcribe_language='zh',
    use_asr_cache=True,
)
result = transcribe(video, config)

# 输出 SRT
with open(output_base + '.srt', 'w', encoding='utf-8') as f:
    f.write(result.to_srt())

# 输出纯文本（去掉空格，合并成连续文字）
segments = result.split_to_word_segments()
text_parts = [seg.transcript.strip() for seg in segments if seg.transcript.strip()]
full_text = ''.join(text_parts)  # 用 '' 不是 ' '，ASR带空格分开每个字
with open(output_base + '_全文.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)
```

写入容器（只需做一次，之后可复用）：

```bash
sg docker -c "docker cp /tmp/transcribe.py videocaptioner:/app/temp/transcribe.py"
```

### 第4步：执行转录

```bash
sg docker -c "docker exec videocaptioner python3 /app/temp/transcribe.py /app/temp/video.mp3 /app/temp/video"
```

成功输出示例：
```
申请上传成功, 总计大小...
上传...提交成功...转换成功
OK: XXXX字
```

注意：如果出现 DNS 临时故障（`NameResolutionError: Failed to resolve 'member.bilibili.com'`），等几分钟重试即可。**特征：** Python socket 模块能在容器内正常解析，但 requests/urllib3 连接池报DNS失败。这是 B站API 侧偶发问题，重试1-2次即可恢复。

### 第5步：取回结果并清理

```bash
# 取回全文和SRT
sg docker -c "docker cp videocaptioner:/app/temp/video_全文.txt /tmp/"
sg docker -c "docker cp videocaptioner:/app/temp/video.srt /tmp/"

# 删除容器内临时文件
sg docker -c "docker exec videocaptioner rm /app/temp/video.mp4 /app/temp/video.mp3 /app/temp/video.srt /app/temp/video_全文.txt"
```

### 第6步：生成分析报告

用 LLM 分析全文内容，输出结构化的分析报告（核心观点、关键数据、持仓影响判断）。

## 完整示例脚本（一键执行）

`~/.hermes/skills/research/social-media-monitor/scripts/docker-transcribe.py` 已包含以上全部步骤。

## B站视频提取

B站视频的内容提取：搜索→下载音频→VideoCaptioner转录用 `references/bilibili-video-extraction.md`。

详见参考文件。

## ASR 引擎说明

当前使用 **必剪（BIJIAN）免费引擎**，中文识别效果好。VideoCaptioner 还支持：
- ✅ 必剪语音识别 — 免费、中文好、轻量（默认，已验证）
- ✅ 剪映语音识别 — 免费、中文好（未验证）

修改 `TranscribeModelEnum` 即可切换。

## 清理铁律

**处理完成后必须删除容器内的视频文件**（mp4 + mp3 + srt + 全文txt），否则长期累积会吃光硬盘空间。容器 1核/1G 限制，资源有限。

## Pitfalls

- ❌ **不要用 Playwright/Streamlit UI** — 已弃用，不稳定
- ❌ 不要把原始字幕/全文当输出——用户要的是分析提炼
- ❌ ASR 输出每个字带空格（"美 国 人"） — 取回后要 `.replace(' ', '')` 去掉
- ❌ `sg docker -c` 有时会超时（terminal 工具超时报 BLOCKED） — 改用 Python subprocess 调用，或重试
- ⏱ 转录时间：10分钟音频约需 5-15 分钟（受容器性能限制）
- 📡 DNS 临时故障会打断转录 — **典型表现：** Python `socket.getaddrinfo()` 可正常解析，但 `requests/urllib3` 报 `NameResolutionError: Failed to resolve 'member.bilibili.com'`。这是因为必剪ASR会上传音频到 B站Bcut API。**重试1-2次即可恢复，不要换引擎。**
