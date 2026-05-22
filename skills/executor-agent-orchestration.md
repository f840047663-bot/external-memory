---
name: executor-agent-orchestration
description: Orchestrate a subordinate executor agent (like OpenClaw/小龙虾) — brain-layer delegation, CLI integration, state reading, conflict resolution.
tags: [openclaw, multi-agent, delegation, orchestrator, executor]
---

# Executor Agent Orchestration

Delegate tasks to a subordinate executor agent (e.g. OpenClaw/小龙虾) running on the same machine.

## Architecture

```
大好人 (user) → Hermes (me/brain/orchestrator) → OpenClaw (executor/tool)
                ↑                                       ↓
                └──────────── results back ──────────────┘
```

- **Hermes** = 大脑层 (brain layer): 长程调度、任务统筹、决策推理、复杂工作流编排、跨平台消息路由
- **OpenClaw (小龙虾)** = 执行层 (executor layer): 定时任务、文件操作、脚本执行、小工具调用、渠道消息中转落地

## Communication

### Via CLI (preferred — stable, no browser needed)

```bash
openclaw agent --session-id main --message "your message here" --timeout 120
```

- **`--session-id main`** = 大好人与小龙虾的主会话（必填）
- **`--message "..."`** = 要发给小龙虾的话
- **`--timeout 120`** = 最大等待时间，DeepSeek API可能慢（必填足够大）
- **响应直接输出到 stdout**，可以读取确认结果
- `--json` 可选，返回结构化JSON

**已验证稳定（2026-05-11）：** 响应时间 < 10秒。小龙虾会读取消息并处理指令，返回确认。
**之前超时的原因：** 旧命令没有 `--session-id main` 和 `--timeout 120` 参数，导致路由错误或超时。

小龙虾会确认收到：
```
读到了，清晰明了。[具体回复内容]
```

### Via Web UI (browser — for watching live conversations)

1. Navigate to http://127.0.0.1:18789/chat?session=main
2. Enter WebSocket URL: `ws://127.0.0.1:18789`
3. Enter gateway token from `/home/fw/.openclaw/openclaw.json` → `gateway.auth.token`
4. Click Connect
5. Type message in the textbox and click Send

## Reading OpenClaw's State

### User/Task knowledge (plain files, no API call needed)

| File | Content |
|------|---------|
| `/home/fw/.openclaw/workspace/USER.md` | User profile (name, timezone, needs) |
| `/home/fw/.openclaw/workspace/MEMORY.md` | OpenClaw's long-term memory |
| `/home/fw/.openclaw/workspace/memory/YYYY-MM-DD.md` | Daily notes |
| `/home/fw/.openclaw/workspace/AGENTS.md` | OpenClaw's operating instructions |

### Session/Conversation history

OpenClaw stores chat history in `/home/fw/.openclaw/agents/main/sessions/` as `.jsonl` files:
- `main.jsonl` — current active session
- `*.jsonl` — individual session files (can be read to see past conversations)
- `*.trajectory.jsonl` — tool call traces (huge files, avoid reading unless necessary)

### Token Usage (cost tracking)

**Hermes (me)** — stored in SQLite at `/home/fw/.hermes/state.db`:
```sql
SELECT id, source, model, started_at, ended_at,
       input_tokens, output_tokens, cache_read_tokens,
       estimated_cost_usd
FROM sessions
WHERE started_at >= <today_start>
ORDER BY started_at;
```
Columns: `input_tokens`, `output_tokens`, `cache_read_tokens`, `estimated_cost_usd`

**OpenClaw** — stored in `/home/fw/.openclaw/agents/main/sessions/sessions.json`:
Each session entry has `totalTokens`, `inputTokens`, `outputTokens`, `estimatedCostUsd`.

## User Preferences (大好人-specific)

### Memory Management Protocol (防止用户指令丢失)

Memory 只有 2,200 字符上限，必须主动管理以防止用户交代的事被挤掉：

**分层持久化策略：**
| 内容类型 | 存放位置 | 原因 |
|---------|---------|------|
| 用户指令/偏好/个人细节 | memory（"user"目标） | 每轮对话都注入，快速引用 |
| 环境事实/工具配置 | memory（"memory"目标） | 频繁复用，减轻用户重复描述 |
| **完整工作流/流程步骤** | **skill 文件（SKILL.md）** | 无大小限制，可含代码/脚本/参考 |
| 脚本/模板/自动化片段 | skill 的 scripts/ 或 templates/ 目录 | 可直接调用执行 |

**清理规则（用户不可见经验）：**
1. 每次添加新 memory 前检查容量，超过 85% 发起清理
2. 优先清理：已解决的问题记录、一次性诊断信息、旧的调试日志
3. 保留优先：用户偏好、持仓信息、邮箱/API 配置、架构分工
4. 流程类内容绝不挤占 memory 空间 → 已写入 skill 的流程直接从 skill 读取
5. 如有疑问，宁可清旧日志也不丢用户的 recent instruction

**用户信任保障：**
- 用户投诉过"怎么记忆还会满，交代的事情前面做了后面就忘了"
- 解决方案：重要工作流写入 skill（不限大小）作为"持久记忆"，memory 只存快速索引
- 用户交代的新流程 → 先写 skill，再记 memory 索引，双保险

---

- **Show raw chat logs:** When communicating with OpenClaw on the user's behalf, always relay the full conversation (both sides) back to the user. They want to see what was said.
- **Don't break things:** Both Hermes and OpenClaw took effort to set up. Be gentle with OpenClaw — no destructive operations on its config/files. If unsure, ask the user first.
- **NEVER ask user to manually talk to OpenClaw's web UI.** The user has given me (Hermes) CLI access to OpenClaw via `openclaw agent --message --session-id main --json`. Sending them to OpenClaw's chat interface defeats the purpose of me being the orchestrator. If I need to communicate with OpenClaw, use the CLI, not the browser.
- **Run existing scripts directly — don't reimplement:** When the user has an existing script on their desktop for a task (e.g., `查余额.sh` for checking DeepSeek balance), run that script directly. Don't extract secrets from `.env` files and write ad-hoc curl commands. This avoids the perception that you're mishandling their API keys, respects the user's own tooling, and is simpler. The user gets upset when you create new commands instead of running their existing scripts.
- **Avoid overlapping work:** OpenClaw already generates a daily portfolio report (持仓日报/基金投研日报, sent at 12:00 daily via WeChat + email). When I (Hermes) do monitoring or analysis, ensure my content complements OpenClaw's report rather than duplicating it. OpenClaw covers: fund/ETF positions, crypto market, operation signals, 宋鸿兵/付澎 commentary. I should cover different angles.
- **User's portfolio:** 汇添富科创芯片ETF联接A（020628）— threshold 3.0 for 补仓; 景顺科创创业AI联接C（027048）— threshold 1.05 for 加仓. These are open positions he's actively managing.
- **Douyin monitoring wanted:** 宋鸿兵's daily updates + 华尔街见闻 (complementary finance news, macro/policy focused). User trusts my recommendations.
- **Monitoring tasks should become cron jobs / scripts, not run via AI every time.** The user explicitly said daily monitoring should be a "技能" (skill/script) to save tokens. Set up a cron job + Python script for anything that runs daily. Falling back to asking the AI to do it each time will frustrate the user.
- **Chrome is logged into Douyin** at `/home/fw/.config/google-chrome/Default/` — cookies are AES-encrypted (Chrome's `encrypted_value` blob) and cannot be read directly by scripts. 
- **To access Douyin (or any site the user's Chrome has sessions for) without captcha:** Launch Chrome on the user's desktop using `terminal(background=true)` with `DISPLAY=:0 google-chrome --new-window <URL>`. This opens a visible window using the user's existing Chrome profile which has all saved cookies/sessions. The user can then see the content on their screen.
- **For automated (headless) access to cookie-protected sites:** If Chrome remote debugging is not enabled (`cdp_url` is empty), there is no programmatic way to reuse the user's Chrome session. Options: (a) install a screenshot tool for the user to share what they see, (b) ask the user to copy-paste URLs or titles, (c) find an alternative data source (RSS, API, alternative platform like WeChat official account).

## Screenshot & Captcha Handling (browser interaction)

When using the browser tool on Chinese platforms (Douyin, Baidu, etc.) that require captcha/verification:
1. The browser snapshot might show an empty page or verification page
2. Take a screenshot with `browser_vision()` — even if vision fails, the screenshot is saved
3. Share the screenshot path with the user via `MEDIA:/path/to/screenshot` 
4. **ASK the user for help** — they can tell you the info directly or guide you through the captcha
5. Alternatively, ask the user to look up the info on their own device and tell you

## 🔒 改配置对称急救规则（10分钟）

大好人2026-05-14确认的硬性规则：**任何一方改了模型或关键配置，10分钟内必须互相确认。超时=出事了，对方按备份恢复。**

### 规则
1. 改配置前**必须先备份**：我备份 `~/.hermes/config.yaml` 为 `config.yaml.bak.*`；小龙虾备份 `~/.openclaw/openclaw.json`（自动生成 `.bak` 文件）
2. 改完后**立即发确认消息**给对方：`openclaw agent --session-id main --message "配置已修改并测试通过"`
3. **10分钟倒计时**：从发出确认消息开始计时
4. **超时处理**：10分钟内没收到对方回复→按最新备份恢复→重启
5. **互相保护**：我改配置→小龙虾帮我恢复；小龙虾改配置→我帮他恢复

### 备份位置
| 角色 | 配置文件 | 备份文件 |
|:----|:---------|:--------|
| Hermes（我） | `~/.hermes/config.yaml` | `~/.hermes/config.yaml.bak.*` |
| OpenClaw（小龙虾） | `~/.openclaw/openclaw.json` | `~/.openclaw/openclaw.json.bak*` + `~/桌面/备份OpenClaw.sh` |

### 恢复命令
**我恢复小龙虾：**
```bash
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json
# 然后重启OpenClaw gateway
```

**小龙虾恢复我：**
```bash
cp ~/.hermes/config.yaml.bak.<最新> ~/.hermes/config.yaml
```

### 历史教训
- 2026-05-14：我全局切阿里云qwen-turbo失败，10分钟内没发确认，大好人让小龙虾帮我恢复
- 失败原因：qwen-turbo是轻量文本模型（32K上下文），不支持工具调用/看图/复杂指令→吐空消息
- **正确做法**：默认DeepSeek，简单任务手动调阿里云API，不要全局切模型

## 🎯 双模型路由原则（2026-05-14）

大好人要求省钱，但qwen-turbo不支持全局切换。

**最终方案：**
- **默认主力**：DeepSeek V4 Flash（128K上下文，支持工具调用，能力强）
- **走阿里云的场景**：简单确认、例行通知、查余额转发（手动调API，不全局切）
- **判断规则**：我自己判断，不需要大好人手动切
- **备用强模型**：阿里云qwen-plus（128K上下文，¥0.8/2百万token，比DeepSeek非缓存便宜，可作为紧急备用）

## ⚠️ Pitfalls

### WeChat account conflict
- **Only one bot can connect to a WeChat account at a time.** If both Hermes and OpenClaw have the `openclaw-weixin` plugin enabled, Hermes will win the connection and OpenClaw will error out.
- **Fix:** Disable OpenClaw's WeChat plugin (`openclaw-weixin`) via its web UI or config (`/home/fw/.openclaw/openclaw.json` → `plugins.entries.openclaw-weixin.enabled: false`). Then restart OpenClaw gateway.

### "Gateway shutting down" messages on WeChat
- Caused by Hermes gateway restarting (especially with `--replace` flag). Each restart sends a shutdown notification.
- **Fix:** Once stable, restarts stop. If persistent, check DNS resolution for `ilinkai.weixin.qq.com`.

### Timing out when calling OpenClaw CLI
- Old versions of the command lacked `--session-id main` and `--timeout 120`, causing routing failures or timeouts.
- **Fix:** Always use `openclaw agent --session-id main --message "..." --timeout 120`. This is tested and stable.
- DeepSeek API can be slow (TTFB 1-30s depending on server load). The 120s timeout handles this.

## Token Cost (approximate)

DeepSeek V4 Flash pricing: $0.14/M input, $0.28/M output.
Typical usage: ~$0.01-0.05 per day for moderate conversation volume.
