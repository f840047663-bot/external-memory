---
name: daily-cron-exec
title: 每日cron执行 — 视频监控→转录→分析→推小龙虾（精简版）
description: 13:00 cron专用，不加载完整daily-briefing skill。只包含执行步骤和关键铁律，不包含全部文档和参考。
triggers:
  - 用户问"今天有什么新视频"或"监控有没有跑"
  - 收到抖音/B站/知乎监控报告后需要分析转录
---

# 每日cron执行 — 精简版（监控直跑+AI分析分离架构）

## 🔴 架构原则：监控（机械）≠ 分析（脑力），必须分离

**2026-05-22 架构升级：** 原来cron让AI包揽全流程（监控→转录→分析→推送），AI在cron环境频繁跳步骤。
**现在改为两层分离：**

| 层 | 谁做 | 是否走AI | 方式 |
|---|------|---------|------|
| **监控巡逻**（每天检查谁发了新内容） | 脚本直跑 | ❌ 零token | no_agent=true cron |
| **分析转录**（下载→ASR→写events→更新贝叶斯→推小龙虾） | 我（Hermes） | ✅ | 收到监控报告后手动/对话中做 |

**好处：** 监控永远不跳步骤、零token成本；脑力活由AI负责，不浪费上下文。

## 🔴 克隆体环境警告

**本机是原始系统的克隆体。** 以下事项不能假设与原始系统一致：
- Chrome CDP端口（9222）可能未启动 → cookie三路保底必须走桌面文件优先
- Docker容器可能来自克隆（名称/端口可能变化）→ 每次先 `docker ps` 确认videocaptioner容器在跑
- cron状态是从原盘克隆过来的 → 首次运行先检查脚本输出是否异常

## 步骤（AI层 — 收到监控报告后执行）

### Step 0: 读监控报告（三个平台）
先读今日的监控报告，了解谁发了什么新视频：
- `~/桌面/每日视频总结/{今日日期}_监控报告.md`（抖音）
- `~/桌面/每日视频总结/{今日日期}_B站报告.md`（B站）
- `~/桌面/每日视频总结/{今日日期}_知乎报告.md`（知乎）

如果最新报告 < 今天 → 先手动跑脚本排查管道。

### Step 2: 筛选（只处理跟持仓相关的重要视频）

**✅ 必须处理的（高优先级）：**
- 芯片/半导体/AI/算力（芯片ETF 020628、海外科技007476相关）
- 黄金/避险（黄金持仓相关）
- 养殖/猪周期（养殖ETF相关）
- 银行/宏观/经济数据（银行001595相关）
- 恒生科技/中概
- 有色金属/能源/原油（HALO框架）

**⏭️ 跳过：**
- 文化/社会杂谈/鸡汤/成功学/军事/日常生活

**最大处理量：** 每个博主最多处理2条最新视频，总数不超过5条。

### Step 3: 下载+转录

用docker VideoCaptioner转录：
```bash
# 1. 从监控报告取aweme_id，拼接视频URL
#    URL格式：https://www.douyin.com/video/{aweme_id}

# 2. 获取play_addr（需cookie）
COOKIE=$(cat ~/桌面/douyin_com_cookie_最新.txt | tr -d '\n')
SEC_UID=$(从监控报告获取博主sec_uid)
API="https://www.douyin.com/aweme/v1/web/aweme/post/?sec_user_id=${SEC_UID}&count=30&aid=1128"
RESP=$(curl -s "$API" -H "User-Agent: Mozilla/5.0" -H "Cookie: $COOKIE" -H "Referer: https://www.douyin.com/" --max-time 15)
PLAY_URL=$(echo "$RESP" | python3 -c "import sys,json,re; d=json.loads(re.sub(r'[\x00-\x1f\x7f]','',sys.stdin.read())); [print(v['video']['play_addr']['url_list'][0]) for v in d['aweme_list'] if v['aweme_id']=='TARGET_ID']" 2>/dev/null | head -1)

# 3. 下载（不传cookie！只传Referer）
curl -L -o /tmp/video.mp4 -H "Referer: https://www.douyin.com/" -H "User-Agent: Mozilla/5.0" "$PLAY_URL" --max-time 120

# 4. 复制到容器 → ffmpeg提音频 → 转录 → 取回
sg docker -c "docker cp /tmp/video.mp4 videocaptioner:/app/work-dir/video.mp4"
sg docker -c "docker exec videocaptioner ffmpeg -y -i /app/work-dir/video.mp4 -vn -ar 16000 -ac 1 -f mp3 /app/work-dir/video.mp3"
sg docker -c "docker exec videocaptioner python3 /app/temp/transcribe_new.py /app/work-dir/video.mp3 /app/work-dir/video"
sg docker -c "docker cp videocaptioner:/app/work-dir/video_全文.txt /tmp/video_全文.txt"

# 5. 清理容器
sg docker -c "docker exec videocaptioner rm -f /app/work-dir/video.mp4 /app/work-dir/video.mp3 /app/work-dir/video_全文.txt /app/work-dir/video.srt"
```

**转录文本清理（必剪ASR字间有空格）：**
```python
import re
with open('/tmp/video_全文.txt') as f: t = f.read()
t = re.sub(r' (?=[\u4e00-\u9fff\u0041-\u005a\u0061-\u007a0-9])', '', t)
t = re.sub(r'(?<=[\u4e00-\u9fff]) ', '', t)
```

### Step 4: LLM分析

对每个转录完的视频，提炼：
- **核心观点**（1-2句）
- **关键数据/数字**
- **影响持仓**（利好/利空哪个持仓）
- **时间节点/预判**（如有）

### Step 5: 写events/和thinkers/

**写 events/{今日日期}.md：**
格式：
```
### {博主}：{视频标题}

**来源:** 链接
**核心观点:** 1-2句

**影响:**
| 持仓 | 方向 | 逻辑 |
|:----|:----:|:-----|

**对应thinker:** thinkers/{博主}.md
```

**更新对应 thinkers/{博主}.md** 的最新观点栏。

### Step 6: 推成品给小龙虾（非半成品）

⚠️ **铁律：必须全部加工完再推，不准推半成品。** 小龙虾不具备事件链概念，推半成品他得重新处理一遍=浪费token。

**推之前必须确认已完成：**
- ✅ 所有视频已转录并分析
- ✅ events/已更新
- ✅ thinkers/已更新  
- ✅ 宏观/中观/微观对应的文件已更新
- ✅ P值已更新（贝叶斯）
- ✅ 事件链已补全

确认全部做完后，再推：
```bash
openclaw agent --session-id main --message "今日已完成数据（成品）：\n- 转录X个视频：...\n- 更新P值：...\n- 事件链：...\n路径：events/..." --timeout 120
```

推的内容包含：
- 已更新的P值（带最终数字，不用验证）
- 事件链摘要（宏观→中观→微观已串好）
- 新增的事件文件路径

### Step 7: 清理
```bash
rm -f /tmp/video.mp4 /tmp/video_全文.txt /tmp/video.srt
```

## 🔥 完整信息处理工作流（必读）

**每个转录完的视频必须按三层流程归档，不能跳过任一层：**

```
转录完成
  ↓
[第1步] 判断信息属于哪层？
  ├─ 🟤 宏观层（利率/地缘/经济数据）→ 更新00-宏观传导框架.md
  ├─ 🟠 中观层（行业/产业链/板块） → 更新对应板块分析
  └─ 🟢 微观层（具体持仓）→ 更新positions/{资产}.md
  ↓
[第2步] 跨层传导（不准只写一层）
  宏观更新后 → 查对应哪些中观板块受影响 → 再查微观(具体持仓)
  中观更新后 → 再查微观(具体持仓)
  ↓
[第3步] 归档+推送
  ├─ 更新对应thinkers/{博主}.md 的最新观点栏
  ├─ 更新23-贝叶斯更新日志.md
  ├─ 更新00-宏观传导框架.md（如果宏观层有变）
  └─ 全部完成后→推成品给小龙虾（不准推半成品）
```

**完整三步骤流程见：** external_memory/workflow-info-processing.md

## 每日报告后工作简报（用户强要求 2026-05-22）

每天出完日报(约14:00-15:30)后，立即向用户推送一条工作简报：

**格式：**
```
今日工作简报
━━━━━━━━━━━━
转录了X个视频 / 收集了Y条信息

抖音：X个视频（宋鸿兵、伊娃...）
B站：X个视频（xxx）
知乎：X篇文章（xxx）

事件链大更新：有/无
（有的话简述）
```

**规则：**
- 不是问用户"要看吗"，是直接推
- 事件链有重大更新时详细说明，没更新时一句话带过
- 这是正式任务，不是想起来才做

**本机是整盘克隆盘B**，不是原始系统。这意味着：
- 原始系统能跑通的管道，克隆体可能因为环境差异（Chrome登录态、docker状态、cookie时效）而跑不通
- **cookie/Chrome/docker切换后行为不同**是管道断裂的根因，不是脚本本身有bug
- 切换克隆后必须验证：①cookie是否有效 ②docker容器是否正常 ③cron任务是否重新注册

**自查命令：**
```bash
# cookie
cat ~/桌面/douyin_com_cookie_最新.txt | grep -o 'sessionid=[^;]*'
# docker
docker ps | grep videocaptioner
# 最近转录
ls -lt ~/桌面/每日视频总结/ | head -5
```

## ⚠️ Pitfalls & 铁律

### 🚨 转录完成后必须当天推给小龙虾（2026-05-22 用户纠正）
用户铁律：分析结果必须在**当天15:30日报前**推给小龙虾，不能等到明天。
用户原话：\"这不是今天当天看当天的报告，怎么成明天的\"。
**做法：** Step 6（推小龙虾）必须在Step 4/5完成后立即执行，不等用户确认。

### 🚨 BIJIAN ASR间歇性DNS故障（2026-05-22 实证）
此机器有间歇性DNS解析失败（`Failed to resolve 'member.bilibili.com'`）。
**解决：** 转录失败时重试一次。两次都失败则标记为\"转录失败\"，输出错误原因。
不要反复硬试超过2次（浪费40s+）。

### 🚨 save_state可知假阳性（2026-05-22 修复）
douyin_monitor.py的save_state上限（100→200条已修复）。但重启后state重置，旧视频会被重新标记为\"新\"。
**处理：** 运行监控脚本后先看create_time时间戳，只处理当天（今天00:00后）的视频。
旧视频（超过3天前）的play_addr基本已过期，下载会返回400，不用试。

### 🚨 推给小龙虾时不要只给结论不给事由（2026-05-22）
每条事件必须写明：①来源（哪个博主的哪个视频）②关键数据和原文 ③影响持仓和方向。
只给P值不给事由 = 用户看不懂。

### 🚨 cron中AI不会自动执行脚本（2026-05-22 发现）
AI经常**跳过**"运行脚本"指令，改读缓存/digest文件来代替。
**必须**用 terminal 工具先执行脚本，把其真实输出作为后续步骤的输入。不要假设AI会主动跑。

### 🚨 Cron持续Error的硬修复：no_agent隔离（2026-05-22 已实施）
此问题已修复，方案：**监控脚本全部改为no_agent=true，AI不从cron中跑。**

当前cron配置：
- 抖音监控-每日13:00 → `python3 ~/.hermes/scripts/douyin_monitor.py`（no_agent=true）
- B站监控-每日13:00 → `python3 ~/.hermes/scripts/bilibili_monitor.py`（no_agent=true）
- 知乎监控-每日13:10 → `python3 ~/.hermes/scripts/zhihu_monitor.py`（no_agent=true）

如果再次故障，检查cron健康：
```bash
# 最新监控报告日期
ls -lt ~/桌面/每日视频总结/*_报告* | head -3
# cron任务状态
hermes cron list | grep -E "抖音|B站|知乎"
# 修改后验证
hermes cron update --job-id <ID> --enabled true  # 重置失败状态
```

**不要恢复旧模式：** 绝不要在cron里挂AI skill做监控。

### 🚨 SKILL.md文件大小破坏cron（2026-05-22 实证）
本skill约15KB（daily-briefing是77KB）。**绝对不要在cron的skills列表里加载daily-briefing**（会超时报RuntimeError: Connection error，一行实际的代码都跑不了）。
本skill就是为此设计的精简替代品。

### 🚨 cookie三路保底（2026-05-22）
1️⃣ 桌面cookie文件(`~/桌面/douyin_com_cookie_最新.txt`) — 主路径，raw header格式
2️⃣ yt-dlp — 备用，Chrome v147+可能失败
3️⃣ CDP浏览器直读(`cdp-get-cookies.py`) — 最后手段
douyin_monitor.py已有完整的三路保底实现，无需手动干预。

### 🚨 转录管道存活检查
日报前必须验证：
```bash
ls -lt ~/桌面/每日视频总结/ | head -5
```
最新文件 > 3天前 → 管道断了，先修管道再出日报。

### 🚨 旧视频play_addr已过期
几天前的视频play_addr返回400（正常现象）。每天13:00跑当天新视频即可。

### 🚨 管道健康检查（2026-05-22 新增）
每天13:30自动跑 `pipeline_health_check.py`：
- 检查三个平台cookie是否有效（有无sessionid/b_nut/z_c0字段）
- 检查今日监控报告是否生成
- 检查最新events文件是否在3天内
- 检查监控报告和events的时间差（有报告没处理？）
- **有问题才输出告警，没问题静默**（零token浪费）

对应的cron：`管道健康检查-每日13:30`（no_agent=true）

### 🚨 新信源管理：必须问用户"要不要加监控"（2026-05-22 用户严正纠正）
**这是本skill最核心的行为规则之一。** 用户多次因我处理完内容但不保存信源而愤怒。

**铁律：** 每次转录/分析完一个**新出现的UP主或知乎用户**后，在推给用户内容时**必须**附带一句：
> 「这个人/账号要不要加到监控清单里？以后有新内容自动抓。」

**错误模式（被用户严厉批评）：**
- ❌ 转录了付鹏B站视频 → 写了events → **没把链接存到B站监控清单.txt** → 下次他发新视频没人抓
- ❌ 转录了无知半人抖音视频 → 写了events → **没问要不要加监控**
- ❌ 用户给了链接 → 我看了/分析了 → 链接丢了 → 用户原话：\"你读完了，你把他视频转录了，你好像就没有把它链接保存下来\"

**正确做法：**
1. 转录分析完新UP主/用户后
2. 在推给用户的总结末尾**主动问**：「这个要加进监控清单吗？」
3. 用户说「加」→ 立即写到对应平台的清单文件
4. 用户说「不加」→ 不做记录
5. 永远不默认添加

### 🚨 执行铁律：不准说"做完了"实际没做（2026-05-22 用户严厉纠正）
这是本skill最高优先级铁律。用户因我多次"说审完了实际没审"而极度不满。
- 执行的每个步骤必须**真实跑通**才算完成。用更强模型必须通过API直调验证
- 如果某步失败了，老实说"失败了+原因+下一步"，不要假装都做完了
- 用户原话："你不能骗我，你不能就是说没整好，你跟我说整好了"

### 🚨 任务理解：审工作流不是审结果（2026-05-22 用户纠正）
用户要求审核时，必须先确认**审什么**：
- 审**工作流架构稳定性**（管道断没断、有没有自我检查、单点故障在哪）？
- 还是审**投资结果/持仓P值/事件链**？
- 问清楚再动手，不默认理解。用户原话："我一直说叫你审核工作流，不是审核这个结果"

### 铁律（精简版）
1. **没转录的视频不准概括内容。** 宁可说"没看过"也不能编。
2. **净值是果不是因。** 不用净值反推概率。
3. **浓缩原则：** 核心事实保留，背景铺垫砍，修辞填充砍，重复强调砍。
4. **全中文。** 所有文件和分析用中文写。
5. **删除视频源文件。** 转录完成后立即删。
6. **不用 `--deliver` 参数推小龙虾。** 只用 `--session-id main --message "..." --timeout 120`。
7. **如果完全没有新视频 → 输出 [SILENT] 并结束。**

## 关联脚本一览

| 脚本 | 功能 | 调用方式 |
|------|------|---------|
| `~/.hermes/scripts/douyin_monitor.py` | 抖音10个博主视频监控 | no_agent cron 每天13:00 |
| `~/.hermes/scripts/bilibili_monitor.py` | B站UP主视频监控 | no_agent cron 每天13:00 |
| `~/.hermes/scripts/zhihu_monitor.py` | 知乎用户文章监控 | no_agent cron 每天13:10 |
| `~/.hermes/scripts/audit_all_positions.py` | 全仓审计快照（P值+更新时间） | 手动或每14天cron |
| `~/.hermes/scripts/hermes_recovery_guide.py` | Hermes恢复指南（给小龙虾用，5步流程） | 手动运行 |
| `~/.hermes/scripts/cron_health_check.sh` | 每6小时cron健康告警 | no_agent cron 每6h |
| `~/.hermes/scripts/pipeline_health_check.py` | 每日管道健康检查（cookie时效+报告新鲜度+事件时间差） | no_agent cron 每天13:30 |
| `~/.hermes/scripts/hermes_recovery_guide.py` | Hermes恢复指南（给小龙虾用，5步恢复流程） | 手动运行 |

**监控清单文件（用户可自行添加链接）：**
- `~/桌面/每日视频总结/抖音主页.txt` — 抖音博主（URL【名称】格式）
- `~/桌面/B站监控清单.txt` — B站UP主（名称|mid或链接）
- `~/桌面/知乎监控清单.txt` — 知乎用户（名称|people/链接）

详情见 `references/scripts-overview.md`
