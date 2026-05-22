---
name: model-routing
title: 模型路由与API fallback设计
description: >-
  实际生产架构：主agent=DeepSeek V4 Flash（唯一支持Hermes tool calling的模型），
  阿里云Qwen Turbo不可作为主模型（已验证两次导致tool calling返回空）。
  闲聊路由走chat-relay.sh→硅基免费模型。
  本skill记录实际工作架构，非理想设计。
triggers:
  - 用户问模型切换/路由/省钱相关
  - 需要修改模型配置或API key
  - 免费API挂了需要排查
  - 用户抱怨API花费超标
  - 用户问为什么某条消息用了某个模型
  - 需要调整delegation配置
  - 考虑切主模型到阿里云Qwen Turbo（先读此skill的陷阱5！）
---

# 模型路由与API Fallback设计

## 🚨 行为铁律：用户说不要再讨论了，直接做

**用户原话（2026-05-17）：** "这个怎么省钱的事情，跟你说了吗100次。"

**这条命不是文档，是强制行为规则：**
1. 模型路由方案已定（见下文架构图），**不要再跟用户讨论/确认/提议换方案**
2. 闲聊时立刻用 chat-relay，**不需要问用户"要不要切"**
3. 用户问"免费额度没了怎么办" → 已配置自动 fallback 链，直接回答"自动切到付费，不中断"
4. 系统因为切模型崩了 → 小龙虾能修，**不要因为这个犹豫不切**
5. 用户对半吊子讨论比半吊子实现更厌烦。宁可执行有风险，也不要反复讨论不执行

**检查自己：** 如果我已经连续调了 3-5 个工具但没解决任何问题，应该停下来想想：这个方案行不行？不行就告诉用户，而不是继续试。

### 陷阱7: 系统卡死导致虚耗成本（易忽视）

**2026-05-19 实际案例：** hindsight 守护进程叠了7个副本（2.4GB内存），系统 IO wait 75%，每轮工具调用响应时间从正常秒级拖到几十秒。用户等不及就强制重启——重启后上下文丢失，之前的 token 全部白花。

**规则：**
1. 工具调用超时后 Hermes 可能自动重试 → 同样 prompt 再花一次钱
2. 系统响应慢 → 用户失去耐心强制重启 → 整个 session 的缓存和上下文清零
3. 省钱的第零步：确保系统稳定、工具调用能顺利返回。省 20 次因超时重试的调用比优化 KV 缓存命中率更实在
4. 遇到进程叠罗汉类故障时（见 skill:ubuntu-stability 故障模式三），优先恢复系统稳定再考虑模型省钱

**信号：** 如果连续出现 3+ 次工具调用超时或用户频繁强制重启，先排查系统内存/进程数，不要继续堆 token。

### 模型可用性测试结果（2026-05-22）

| 模型 | 可用？ | 说明 |
|------|:-----:|:-----|
| `deepseek-v4-flash` | ✅ | 当前主力，Hermes tool calling唯一兼容 |
| `deepseek-v4-pro` | ✅ | 可用但比Flash贵，仅审核/审计时临时切换 |
| `deepseek-v4` | ❌ | API拒绝——支持的模型名是`deepseek-v4-pro`或`deepseek-v4-flash` |
| Claude Sonnet 4 (OpenRouter) | ❌ | 区域限制："This model is not available in your region" |
| Claude 3.5 Sonnet (OpenRouter) | ❌ | "No endpoints found" |
| Claude 3 Opus (OpenRouter) | ❌ | "No endpoints found" |
| Claude 3 Haiku (OpenRouter) | ❌ | 区域限制同上 |

**结论：DeepSeek系是国内唯一可用的高端模型。Claude全线被区域封禁。**

---

## 省钱指南（不是改模型，是改行为）

**不要将主模型切到阿里云Qwen Turbo。已验证两次失败（2026-05-16, 2026-05-17）：**
- Hermes Agent 的 tool calling 需要模型返回结构化 tool use 调用
- Qwen Turbo 收到工具返回结果后输出空（日志: `⚠️ Model returned empty after tool calls`）
- 表现为：能收消息，能思考，但一调工具就死
- 阿里云 DashScope API 本身是通的（curl测试正常），但模型能力不够

**永远保持 `model.default = deepseek-v4-flash, provider = deepseek`。**

## 实际生产架构（2026-05-17 已验证可行）

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户消息                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐ ┌──────────────────────────────────────┐
│ 层1: 主agent — DeepSeek │ │ 闲聊路由: chat-relay.sh              │
│     V4 Flash            │ │  → 硅基流动 Qwen2.5-7B (免费)        │
│ ─────────────────────── │ │ ─────────────────────────────────── │
│ · 唯一支持Hermes tool   │ │ · 纯文本闲聊/简单问答                │
│   calling 的模型        │ │ · 用 curl 直调 API，不经过 Hermes   │
│ · 系统必须运行在此模型  │ │    Agent 的 tool calling 引擎        │
│ · 备份配置可以改其他，  │ │ · 如果超时→不降级，直接               │
│   但生产环境不要动      │ │   告诉用户 API 暂时不通               │
│ · 默认模型参数：        │ │                                       │
│   deepseek-v4-flash     │ │                                       │
│   base_url: api.deepseek│ │                                       │
└─────────────────────────┘ └──────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 层2 (fallback): dashscope (阿里云, 紧急兜底) → siliconflow (免费, 最弱)│
│ · fallback_providers 已配置：dashscope → siliconflow                   │
│ · 阿里云在 DeepSeek 挂了时提供付费兜底（Qwen Turbo 但无 tool calling）  │
│ · siliconflow 作为最后防线（Qwen2.5-7B，免费，能力极弱）                │
└───────────────────────────────────────────────────────────────────────┘
```

### 关键决策逻辑

**我（agent）在主模型 DeepSeek V4 Flash 上运行，按以下规则处理：**

1. **简单消息**（问候/确认/简短回复）→ 直接回复，**减少工具调用**，控制输出量
   - 不用每次查 Hindsight/记忆
   - 输出控制在 100-200 tokens
   - 输出 ¥2/百万 tokens 是最贵的部分
2. **中等消息**（查询数据/读文件/简单分析）→ 调1-2个工具，快速完成
3. **复杂任务**（投资分析/代码/调试/多步骤）→ 用 `delegate_task()` 起子agent
4. **尽力压缩上下文** → 系统prompt（含 MEMORY.md）频繁变化会破坏 DeepSeek 服务端 KV 缓存

### 当前配置快照（2026-05-17 生效 — 注意：下面config是旧版本，实际已改为dashscope→siliconflow）

> ⚠️ 下面的 YAML 代码块是原始记录的旧配置（deepseek→siliconflow），实际 config.yaml 中 fallback_providers 已修正为 `dashscope → siliconflow`。保留此段仅作历史对比。**实际以/root/home/.hermes/config.yaml为准。**

```yaml
model:
  default: deepseek-v4-flash          # 主模型 = DeepSeek V4 Flash（不要改！）
  provider: deepseek
  base_url: https://api.deepseek.com/v1
providers:
  dashscope:
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: ${DASHSCOPE_API_KEY}
  deepseek:
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
  siliconflow:
    base_url: https://api.siliconflow.cn/v1
    api_key: ${HINDSIGHT_LLM_API_KEY}
fallback_providers:
  - deepseek                             # DeepSeek挂了→DeepSeek重试（其实没用）
  - siliconflow                          # 最后防线，免费模型
prompt_caching:
  cache_ttl: 1h                          # 2026-05-17 从 5m 改为 1h，边际收益
compression:                              # 2026-05-17 以下三项同步调整
  enabled: true
  threshold: 0.6                          # 0.5→0.6，少压缩防复读
  target_ratio: 0.2
  protect_last_n: 30                      # 12→30，保护更多上下文
agent:
  tool_use_enforcement: true              # auto→true，强制调工具
  reasoning_effort: medium                # ''→medium，默认省token
delegation:
  model: ''                              # 空=继承主模型=deepseek-v4-flash
  provider: ''                           # 继承主模型=deepseek
```

**注意：** `fallback_providers` 中有 deepseek 是冗余的（主模型本身就是 deepseek），但无害。设计上 dashscope 应在 deepseek 之前做 fallback。

## 关键陷阱（不遵守会出问题）

### 陷阱1: 🚫 阿里云 Qwen Turbo 不能做主模型 ⭐⭐⭐

**最高优先级陷阱。** 此前skill.md写的架构（主agent=Qwen Turbo）是错误的理想设计。实际已验证两次（2026-05-16, 2026-05-17）：
- Qwen Turbo 收到 tool calling 的返回结果后输出空
- 日志表现为：`⚠️ Model returned empty after tool calls`
- 用户遭受服务中断，小龙虾被叫来救火

**结论：永远不要设置 `model.default = qwen-turbo` 或 `model.provider = dashscope`。**

### 陷阱2: 模型切换后Hindsight可能不工作

Hindsight的LLM key（用于记忆提取/反射）独立于主模型配置。如果切换了主provider，Hindsight的base_url可能指向错误的地址。

**当前 Hindsight 配置（2026-05-17 已修正）：**

硅基流动 API key 已过期，Hindsight 改用 DeepSeek 作为 LLM 后端：
```bash
# 在 .env 中（当前生效值）
HINDSIGHT_API_DATABASE_URL=pg0                 # 覆盖 compat.py 的 SQLite 默认值
HINDSIGHT_API_LLM_PROVIDER=openai              # 必须设置！缺失会导致 daemon startup 失败
HINDSIGHT_API_LLM_BASE_URL=https://api.deepseek.com/v1  # 原为 siliconflow.cn
HINDSIGHT_API_LLM_MODEL=deepseek-v4-flash
HINDSIGHT_LLM_API_KEY=<同DEEPSEEK_API_KEY>     # 跟主模型同一个 Key
```

**重要：** `HINDSIGHT_API_LLM_PROVIDER` 在 `.env` 中初始为空，必须手动设为 `openai`。
缺少此变量时 daemon 启动时报 `ValueError: Invalid LLM provider` 并退出。

**如果 DeepSeek 挂了，可以把 Hindsight 切到阿里云：**
```bash
# 改 .env 中：
HINDSIGHT_API_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
HINDSIGHT_LLM_API_KEY=<DASHSCOPE_API_KEY的值>
# 保持 HINDSIGHT_API_LLM_PROVIDER=openai 不变（阿里云也兼容 OpenAI 格式）
```

### 陷阱3: 硅基流动key被截断

硅基流动的API key在config.yaml中是**硬编码且被截断的**（`sk-rsb...nijd`）。必须用env变量 `${HINDSIGHT_LLM_API_KEY}`。

检查方法：
```bash
grep "api_key:" ~/.hermes/config.yaml | grep siliconflow
# 应输出包含 ${HINDSIGHT_LLM_API_KEY}
```

### 陷阱4: delegation继承主模型

`delegation` 配置为 `model: '' provider: ''` 时，子agent会使用主模型的配置（DeepSeek V4 Flash）。这目前是OK的——主模型本身够强，子agent直接用同一个模型也够用。

但如果将来真的成功切换了主模型，记得也改 delegation 配置指向 DeepSeek。

### 陷阱6: 💸 工具调用死循环 = 烧钱最快方式 ⭐⭐⭐

**实际案例（2026-05-18）：** 为解密一个 Chrome v147 cookie 反复尝试 yt-dlp → Python 解密 → GNOME Keyring → 6种密钥派生 → ... 用了约 **15次工具调用**（≈¥0.3-0.5，¥8+对余额¥3.86来说很要命）。

**规则：**
1. 遇到"已知无解"的技术问题（如 Chrome v147 cookie 加密），**最多试3次工具调用就立即投降**
2. 试了不行就告诉用户"这个技术问题今天解不了"，切到手动方案（F12复制、用户重启Chrome等）
3. 不要在同一个死胡同里绕：3次失败 = 换方案 or 告诉用户
4. **每轮工具调用 ≈ ¥0.01-0.03**，这是真金白银从余额里扣的
5. 知道答案就执行（用户原话），不知道答案先承认不行（用户也接受），**最不能做的是瞎试半吊子方案拖长对话**

**检查自己：** 如果我已经连续调了 3-5 个工具但没解决任何问题，应该停下来想想："这个方案行不行？不行就告诉用户，而不是继续试。"


DeepSeek 服务端 KV 缓存命中率 **94.81%**（2026-05-14~16 实测数据）。边际提升空间极小：

- `prompt_caching.cache_ttl: 5m` → 1h 更改已做（2026-05-17），预期提升 <1%
- 跨会话缓存清零——每次新会话从头开始
- 影响命中率的最大因素：**系统 prompt 稳定性**。MEMORY.md 频繁变化 = 每次都有新前缀 = 缓存不命中
- 输出 token **不参与缓存**（永远全价 ¥2/M）

## 省钱指南（不是改模型，是改行为）

94.81% 缓存命中率下，改模型路由和省配置的杠杆很有限。**真正的省钱杠杆在行为层面：**

| 方法 | 预估节省 | 风险 | 说明 |
|:----|:--------|:----|:-----|
| **控制输出长度** | 中-高 | 低 | 输出 ¥2/M tokens 是最贵部分。非分析场景输出 ≤200 tokens |
| **减少不必要的工具调用** | 中 | 低 | 每调一次工具=新的一轮上下文回传+新输出。简单确认不查记忆 |
| **稳定 system prompt** | 边际 | 低 | MEMORY.md 频繁变→缓存命中率降。改完等几轮缓存重建 |
| **cache_ttl 5m→1h** | 低(<1%) | 极低 | 2026-05-17 已改 |
| **聊天路由到硅基免费** | 中-高 | 低 | 见下方「闲聊路由实操」 |
| **压缩策略调更激进** | ❌ 反向 | 中 | 更积极压缩=更多重新生成=token 消耗增加，反而更贵 |

**结论：最省钱的改动不在 config.yaml 里，在我的行为习惯里。**

> 完整 KV 缓存机制分析见 `references/deepseek-kv-cache-mechanism.md`（2026-05-18 基于官方文档整理）。

## 闲聊路由实操（代理端使用指南）

chat-relay.sh 是**独立工具调用**，不是 Hermes 模型路由。能否节省费用取决于**我是否在聊天时主动使用它**。

### 检测：当前是"闲聊"还是"正事"？

| 场景 | 类别 | 应该 |
|:----|:----|:-----|
| 问候/表情/日常聊天/简单确认 | 闲聊 ⚡ | 走 chat-relay |
| 用户问是否该做某事（安装/配置/操作） | 行动型 | **先直接做再分析**。用户厌恨半吊子分析，知道答案就执行 |
| 查询数据/分析投资/调试代码 | 正事 🛠 | 走 DeepSeek V4 Flash |
| 用户说"想一下有什么没搞的事" | 盘存型 | 走 DeepSeek（需工具调用查系统） |

### 行动型消息的规则（新版 2026-05-17）

用户问"XXX是否更合适/要不要装"这类问题时：
1. **知道答案 → 直接做，不用分析**
2. 用户原话模式："装上装上" — 反映出用户对啰嗦分析不耐烦
3. 只有用户明确要求分析时才给出详细分析

### 聊天中切换 chat-relay 的方法

```bash
# 在 casual 对话中，直接调脚本获取回复，不走 Hermes tool calling
terminal("bash ~/.hermes/scripts/chat-relay.sh \"用户的问题\"", timeout=15)

# 然后把输出贴在回复里
```

### 什么时候用

- **✅ 应该用：** 用户友好问候、闲聊、简短问答、非技术性对话
- **❌ 不应该用：** 任何需要工具调用（读文件/查数据/调API）、投资分析、配置修改、调试

### 限制

- chat-relay 拿不到对话上下文 — 每次是独立调用
- 如果硅基免费模型挂了，chat-relay 自动降级到付费
- 输出限制在 200 tokens（脚本硬编码 `max_tokens: 200`）
- **用户回复消息时不要用** — 所有用户消息必须经过 Hermes Agent 完整处理

## DeepSeek V4 Flash 定价

| 项目 | 价格 |
|:----|:----|
| 输入 — 缓存命中 | ¥0.1 / 百万 tokens（实际账单价） |
| 输入 — 缓存未命中 | ¥1 / 百万 tokens |
| 输出 | ¥2 / 百万 tokens |
| 上下文长度 | 1M tokens |
| 最大输出 | 384K tokens |

定价详情见 `references/deepseek-pricing.md`。
进阶优化参考见 skill:hermes-10-config-optimizations（视频总结，含当前系统实施状态）。

## API Key 位置

| 提供商 | Key位置 | 余额/付费方式 | 用途 |
|:------|:--------|:-------------|:-----|
| DeepSeek | `.env: DEEPSEEK_API_KEY` | ~¥8.73 余额（2026-05-17） | **主模型（不可替代）** — 可用模型: `deepseek-v4-flash`(日常), `deepseek-v4-pro`(审计) |
| 阿里云百炼 | `.env: DASHSCOPE_API_KEY` | 后付 ~¥5/月 | fallback 兜底（无tool calling） + Hindsight备选 |
| 硅基流动 | `.env` 中已废弃 | ~~免费额度已过期~~ | 原 Hindsight LLM + chat-relay 后端，2026-05-17 弃用 |
| OpenRouter | `.env: OPENROUTER_API_KEY` | $0余额, 50次/天 | 备用 |

> ⚠️ 2026-05-22 更新：ChatGPT/Claude系列在OpenRouter上被中国区域封锁。`anthropic/claude-sonnet-4`、`anthropic/claude-3-haiku` 均返回 `not available in your region`。如需使用只能走VPN。DeepSeek V4 Pro（model名 `deepseek-v4-pro`）在本区域可用且无需VPN。`deepseek-v4` 不是有效模型名，只能用 `deepseek-v4-pro` 或 `deepseek-v4-flash`。Hindsight 的 LLM 现在走 DeepSeek API。chat-relay 脚本如果使用硅基也需要切换（当前仍在走硅基，如果硅基不通会自动 fallback 到 DeepSeek）。

## 故障恢复

### DeepSeek 挂了
→ fallback_providers 自动切 → dashscope → siliconflow
→ 注意：切到 dashscope 后 tool calling 不可用，只能处理简单消息

### DeepSeek + 阿里云都挂了
→ fallback到硅基流动Qwen2.5-7B（免费，能力弱，无tool calling）
→ 紧急恢复：读外部记忆 `API密钥与提供商信息.md`

### 对称急救协议（改配置时遵守）

1. 备份: `cp config.yaml config.yaml.bak.$(date +%s)`
2. 测试: 改前先curl测通新配置
3. 改后10分钟内互相确认（通知小龙虾）
4. 超时 → 对方用备份恢复
