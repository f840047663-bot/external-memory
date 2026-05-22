---
name: topic-monitor
description: 编排型技能 — 组合 cookie-extractor + waf-bypass + zhihu-reader 三个积木，从搜索→读帖→分析→长期跟踪，全流程自动化。不自己造轮子，只编排已有技能
---

# Topic Monitor

## 设计思想

**组合优于继承，编排优于硬编码。**

本技能不包含任何具体实现代码，它只描述如何编排以下独立技能：

```
┌─────────────────┐
│  topic-monitor  │  ← 编排器：告诉我怎么组合
│  (orchestrator) │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    │         │        │          │
    ▼         ▼        ▼          ▼
 cookie-   waf-     zhihu-   外部记忆L3 
 extractor bypass   reader    (归档)
    │         │        │          │
    └─────────┴────────┘          │
       通用积木，可替换          长期存档
```

**为什么这样设计？**
- cookie-extractor 换了 → 不影响其他层
- 知乎API改了 → 只修 zhihu-reader
- 想监控B站 → 新建 bili-reader，其他两层复用
- 任何一个层单独升级，不影响整个管道

---

## ⚡ 本机特殊说明（2026-05-19）

**Chrome 已升级到 v147+，CDP 是唯一能提取登录 cookie 的方案。**
- 不要先试 cookie-extractor (yt-dlp) — v11 加密不可破解
- 直接走 `local-chrome-cdp-bridge`：`python3 ~/.hermes/scripts/cdp-get-cookies.py --domain xxx --test`
- 桌面已有有效 cookie 文件：`~/桌面/zhihu_com_cookie_最新.txt`

## 工作流

### Phase 0: 加载积木

```python
# 先加载三个基础技能
# ⚠️ 本机 Chrome v147+ → CDP 是唯一方案，不要先试 yt-dlp
skill_view('cookie-extractor')    # 提cookie（仅 Chrome < v147 可用）
skill_view('local-chrome-cdp-bridge')  # ⭐ Chrome v147+ 唯一方案
skill_view('waf-bypass')          # 绕WAF（如果IP被封）
skill_view('zhihu-reader')        # 读知乎
```

### Phase 1: 搜索话题

用户给一个话题（如"算力/词元/本地部署"），先在知乎搜索相关讨论：

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone ...) Safari/604.1' \
  'https://www.zhihu.com/api/v4/search_v3?q={关键词}&limit=10'
```

筛选标准：
- 点赞数 > 5 或 回答数 > 3
- 时间近（1年内）
- 标题命中核心关键词

### Phase 2: 读帖

对每个筛选出的帖子，按 zhihu-reader 流程读取：
1. 用 cookie-extractor 确认 cookie 有效
2. 用 waf-bypass 的 iPhone UA 绕过封禁
3. 按 zhihu-reader 的方式 A（feeds API）或方式 B（单回答）读内容

### Phase 3: 分析

分析框架（三个维度）：

| 维度 | 问什么 |
|------|--------|
| **叙事一致性** | 回答之间观点是否打架？主流叙事是什么？ |
| **逻辑链检验** | 每个观点的论据硬不硬？（数据/案例/推理） |
| **反常检测** | 有没有跟主流叙事相反的异见？有没有新角度？ |

输出格式：
```
话题: XXX
主流观点: ...
异见观点: ...
跟咱们持仓的关系: ...
置信度评估: ...
后续关注点: ...
```

### Phase 4: 归档到L3

分析结果写入 `~/.hermes/external_memory/16-AI技能进化与话题监控体系.md` 的 `## 已有话题监控档案` 章节。

格式：
```
### 话题：{话题名}
- **分析日期：** YYYY-MM-DD
- **来源：** 知乎链接
- **回答数：** N
- **核心分歧：** ...
- **我的判断：** ...
- **后续关注：** ...
```

同时写入 L2 记忆（hindsight_retain）以备跨会话检索。

## 参考

- **实战案例：** `references/token-analysis-run-2026-05-18.md` — 首次完整跑通记录，包含每个阶段的输出
- **Cron提示词设计：** `references/cron-job-prompt-design.md` — cron job必须告诉AI它能用工具，而且必须加"不准编数据"的铁律
- **依赖技能：** `cookie-extractor` / `waf-bypass` / `zhihu-reader`（三个积木）
- **L3归档：** `~/.hermes/external_memory/16-AI技能进化与话题监控体系.md`（用户可编辑的持续跟踪文件）

## 🧩 三层积木架构

```
通用积木层（通用，不挑网站）
├── cookie-extractor      — 从Chrome偷cookie（Chrome < v147）
├── local-chrome-cdp-bridge — ⭐ CDP提取cookie（Chrome v147+，本机唯一方案）
├── waf-bypass            — 手机UA绕WAF

平台层（网站专用）
└── zhihu-reader          — 读知乎帖子/回答

编排层（本技能）
└── topic-monitor         — 组合上面做搜索+读帖+分析+归档
```

**铁律：** 编排器不包含任何平台的实现代码。它只负责按顺序调用下层技能。

**铁律：关键流程必须同时存储在技能 + 外部记忆两份。** 系统日切重置后，L1路牌指向外部记忆，外部记忆指向技能。只有技能文件可能丢失上下文（bloated/outdated），外部记忆的 00-总纲 是兜底。

## ⚠️ 陷阱

- ⚠️ **忘记已有技能 = #1 翻车原因。** 2026-05-18 验证：用户昨天建好的 topic-monitor/cookie-extractor/waf-bypass/zhihu-reader 四件套 + 桌面 zhihu_cookie.txt，今天全忘了，从零开始挖 Chrome v147 加密，耗费数十元 API 费用 + 一整天时间。**每次任务第1步必须是：读 00-技能目录.md → 读桌面文件列表 → 加载已有技能。**
- ⚠️ **AI在独立会话（cron/agent）中会编造数据！** 这些会话跟当前对话是不同实例，没有上下文。如果提示词说"用工具查数据"但没给具体命令，AI可能**忽略工具指令，直接用训练数据编造**。修复：提示词开头上大红字警告 + 给具体curl命令 + "宁缺毋滥"铁律。详见 `references/cron-job-prompt-design.md`。
- ⚠️ **监控覆盖 —— 三平台已全部自动化（2026-05-22：主数据源架构已切换）**
  - **★ 唯一数据源：** `thinkers/INDEX.md`（外部记忆）— 所有监控脚本从此文件读取博主列表，不再读独立txt文件。
  - **格式：** `| 博主 | 抖音sec_uid | B站mid | 知乎people | 权重 | 建档 | 互锁仓位 |`
    - 抖音：`MS4w...`（有反引号）  B站：`mid:数字`  知乎：`people/xxx`
  - **三脚本：**
    - **抖音：** `~/.hermes/scripts/douyin_monitor.py` — 每日13:00，优先读INDEX.md，fallback读 `~/桌面/抖音主页.txt`。
    - **B站：** `~/.hermes/scripts/bilibili_monitor.py` — 每日13:00，优先读INDEX.md（`mid:数字`），fallback读 `~/桌面/B站监控清单.txt`。
    - **知乎：** `~/.hermes/scripts/zhihu_monitor.py` — 每日13:10，优先读INDEX.md（`people/xxx`），fallback读 `~/桌面/知乎监控清单.txt`。
  - **辅助脚本：** 背离检查(bayesian_divergence_check.py)、信源可信度(source_credibility.py)、堆叠策略(check_stack_strategy.py)、全仓审计(audit_all_positions.py)、恢复指南(hermes_recovery_guide.py)。
  - **用户操作：** 加新监控源 → 改 `thinkers/INDEX.md` 一条记录。三旧txt文件已降级为fallback。
  - **YouTube/X：** 暂未覆盖。
- ⚠️ **B站内容获取方案（2026-05-21 已验证）：** 不依赖B站API，通过浏览器搜索找到视频URL → yt-dlp下载音频（免费格式无需登录）→ VideoCaptioner容器ASR转录→LLM分析。完整流程见 `videocaptioner-auto-transcribe` 技能的 `references/bilibili-video-extraction.md`。**不再需要用户手动分享链接。**
- ⚠️ **思想档案（Thinker Archive）是长期跟踪的输出格式** — 不是每篇文章都要单独存。topic-monitor的Phase 4归档应指向 external_memory/thinkers/{thinker-name}.md 文件，而不是每篇文章都建新文件。详见 investment-deep-dive 技能的「博主思想档案」章节。
