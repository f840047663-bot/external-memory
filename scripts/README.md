# Hermes 脚本库

> `~/.hermes/scripts/` 下的自定义脚本说明。B盘如果需要相同功能，从这里拷。

---

## 🌐 网络与API

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `chat-relay.sh` | 模型路由转发（主力→硅基免费） | curl, API keys |
| `check_api_balance.sh` | 查各API余额 | curl |
| `daily-cost.sh` | 日消耗统计 | jq |

## 🍪 Cookie提取（Chrome v147+ CDP）

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `cdp-auto-cookies.sh` | 一键启动Chrome→拿cookie→关Chrome | CDP端口9222 |
| `cdp-get-cookies.py` | CDP提取指定域名cookie | websocket库 |
| `check-cookies.py` | cookie有效性验证 | curl |

## 🎥 抖音管线

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `douyin-monitor.py` | 抖音监控（主） | cookie, Chrome CDP |
| `douyin_monitor.py` | 抖音监控（旧版） | cookie |
| `douyin-extract-videos.sh` | 提取抖音视频列表 | curl |
| `douyin-full-extract.sh` | 完整抖音提取 | 多个工具 |
| `douyin-search-user.sh` | 搜索抖音用户 | cookie |
| `read_douyin_video.py` | CDP读抖音视频AI章节 | CDP |
| `fetch_douyin_videos.py` | 获取用户视频 | cookie |
| `search_douyin_user.py` | 搜索用户 | cookie |
| `capture-douyin-api.py` | 截取抖音API请求 | mitmproxy |

## 🏗️ 投资分析

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `consult_multi_model.py` | 多模型咨询 | DeepSeek/Qwen API |
| `consult_pro_for_report.py` | 专业报告咨询 | 同上 |
| `evening_digest.py` | 晚间摘要 | API |
| `daily_aggregator.py` | 日汇总 | API |
| `rss_aggregator.py` | RSS聚合 | requests, bs4 |
| `rss-bridge.py` | RSS Bridge | 同上 |
| `mini-rss.py` | 轻量RSS | requests |
| `search_mlcc.py` | 搜索MLCC信息 | curl |
| `search_bing_mlcc.py` | Bing搜索MLCC | curl |
| `fetch_mlcc_data.py` | 获取MLCC数据 | curl |
| `fetch_oil_data.sh` | 获取原油数据 | curl, jq |
| `sina-news.sh` | 新浪财经新闻 | curl |

## 📊 财联社

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `cls_push.py` | 财联社推送 | requests |
| `cls_web.py` | 财联社网页读取 | requests, bs4 |
| `cailianshe_scraper.py` | 财联社爬虫 | 同上 |
| `cailianshe_scraper.js` | 财联社JS版 | node |

## 📺 宋鸿兵/前途

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `song_hongbing_douyin.py` | 宋鸿兵抖音监控 | cookie |
| `find_qiantu_user.py` | 搜索前途用户 | cookie |
| `find_qiantu_videos.py` | 找前途视频 | cookie |
| `get_qiantu_userpage.py` | 拿用户主页 | cookie |
| `get_qiantu_video.py` | 拿视频信息 | cookie |
| `get_video_src.py` | 拿视频源 | cookie |
| `download_qiantu_video.py` | 下载前途视频 | cookie |
| `process_qiantu.py` | 处理前途内容 | cookie |
| `check_qiantu_page.py` | 检查页面 | cookie |
| `find_author_from_video.py` | 从视频找作者 | cookie |

## 🛠️ 系统工具

| 脚本 | 用途 | 依赖 |
|:----|:-----|:-----|
| `preflight-check.sh` | CDP前系统环境检查 | free, ps |
| `hindsight-watchdog.sh` | 向量库看门狗（内存超限杀进程） | 无 |
| `hindsight-start-and-query.sh` | 启动+查询Hindsight | hindsight |
| `start-hindsight.sh` | 启停Hindsight | hindsight |
| `start-hindsight-bg.sh` | 后台启hindsight | hindsight |
| `video_caption_auto.py` | 视频自动字幕 | VideoCaptioner |
| `video_topic_filter.py` | 视频话题筛选 | 无 |
| `auto_transcribe.py` | 自动转录 | Whisper |
| `qwen-ask.sh` | 问Qwen模型 | curl, API keys |

## 📦 需要Node.js的

| 脚本 | 用途 |
|:----|:-----|
| `cailianshe_scraper.js` | 财联社JS爬虫 |

---

## B盘移植建议

1. **核心必拷**：`cdp-get-cookies.py`, `cdp-auto-cookies.sh`, `chat-relay.sh`, `check_api_balance.sh`, `douyin-monitor.py`
2. **按需拷**：投资分析类脚本只在需要时拷
3. **不要拷**：`.bak` 备份文件、`node_modules/`、`__pycache__/`
4. **路径依赖**：大部分脚本硬编码了 `~/.hermes/`，B盘相同路径可直接用
