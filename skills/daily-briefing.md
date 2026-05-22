---
name: daily-briefing
title: 每日信息简报 — 多源监控→转文字→分析→邮件
description: 全自动每日信息简报流程。监控多个博主/信息源（抖音等）→ 检测新视频 → 下载 → 转文字 → 提炼核心观点 → 多源对比 → 添加AI分析 → 邮件发送。最终产出是一份每天早上送达的「世界正在发生什么」简报。
triggers:
  - 用户要求每日定时推送信息摘要
  - 需要监控多个社交账号的更新
  - 需要跨源对比不同博主的观点
  - 用户说"要让我实时知道世界正在发生什么"
  - 需要将多个信息源整合成统一报告
---

# 每日信息简报 (Daily Briefing)

## ⚠️ 重要：模块化设计（2026-05-22 重构）

**本skill文件很大(77KB)，不可直接用于cron任务。** cron中加载本skill会导致AI读指令超时(RuntimeError: Connection error)，一条实际代码都跑不了。

**cron执行请使用精简版 `skill:daily-cron-exec`**（~15KB 含步骤→转录→分析→推小龙虾的完整流程）。

本skill保留作为完整参考手册，包含全部铁律、参考文件、脚本说明和pitfalls。日常查阅时使用本skill，cron执行时用daily-cron-exec。

**健康告警：** `/home/fw/.hermes/scripts/cron_health_check.sh` 每6小时检查cron失败，失败时通知用户。cron的skills列表不要加载本skill。

# 每日信息简报 (Daily Briefing)

## ⚠️ 重要：模块化设计（2026-05-22 重构 — 8天管道崩溃教训）

**本skill文件很大(77KB)，不可直接用于cron任务。** cron中加载本skill会导致AI读指令超时报 `RuntimeError: Connection error`，一条实际代码都跑不了。2026-05-14~05-22实证：每日13:00全量博主cron连续8天超时，0条视频被下载转录。

**cron执行请使用精简版 `skill:daily-cron-exec`**（~15KB）。本skill保留作为完整参考手册。

**管道健康告警：** `/home/fw/.hermes/scripts/cron_health_check.sh` 每6小时检查cron失败状态，有异常主动通知用户。

**日报前存活检查：** 每天日报前检查最新转录文件时间戳，>3天前说明管道断了，先修再出日报。

## 铁律

### 🔥 净值是果不是因（2026-05-18 大好人纠正 — 最高优先级铁律）

**净值/价格不参与贝叶斯推理。** 净值是事实层面的结果（果），新信息（新闻/政策/博主观点）才是原因（因）。

```
正确因果链：
因（客观事实）→ 被报道 → 信息层（带置信度的证据）→ 贝叶斯推理 → 后验概率
                                                                          ↓
净值/价格（唯一的果）→ 只在月校准核验时使用，不参与推理
```

**净值在系统中的正确用途：**
1. 月校准：对比月初P(上行)预测 vs 月末净值方向 → 更新验证标记
2. 触发检查：银行001595净值是否跌破1.60
3. 仓位计算：当前盈利/亏损
4. 异常报警：单日>±4% → 触发归因

**禁止行为：** 用净值反推概率（如"净值跌了→P下行增加"）。净值不是信息源。

---

### 🔥 不瞎编概率铁律（2026-05-18 大好人纠正）

**每条概率更新必须注明数据来源。来源不明的概率=瞎编，比不编更坏。** 虚假概率带来的副作用大于不设概率。

正确做法：
- 有数据/有来源 → 设先验，注明来源（如"大好人判断+天天基金API净值0.6348"）
- 没数据/没来源 → 写"信息不足"，不编数字
- 净值数据 → 只能用于月校准，不能用于初始化概率

**概率总览表必须包含「数据来源」列。**

---

### 🔥 日报格式铁律（2026-05-18 用户纠正 — 自上而下+事件链+贝叶斯透明）

**日报本质不是「给你数据」，而是「让你跟上世界的变化」。** 三个价值维度：
1. **事件串联** — 今天发生了什么 → 跟之前什么关系 → 接下来要注意
2. **逻辑透明** — 我的推理暴露出来，你才能纠正我
3. **可回溯** — 每项资产有完整事件链+贝叶斯概率变化

**日报结构（2026-05-18定版）：**

```
━━━ 5月X日 ━━━ 今天世界在发生什么 ━━━

🌍 宏观传导（自上往下）
[宏观事件1：摘要]
  → 影响：[解释传导路径]
  → 影响资产：[受影响的具体资产]

[宏观事件2：...]

━━━ 仓位分析（逐项）━━━

📦 [资产名]
│ 事件链：[历史链] ... → [今日新信息]
│ 📖 我的思考：
│   [推理过程：我认为这个信息说明了什么/为什么]
│   [暴露判断逻辑：用户可以纠正我]
│ ├─ 上行空间：约X%（理由）
│ ├─ 下行空间：约X%（理由）
│ └─ 贝叶斯：P(上行) X%→Y% | 仓位建议 | ⏳验证

📦 [资产2]...

━━━ 无更新 M项 ━━━
[今日无新信息的资产列表]

━━━ 值得盯的 ━━━
🔴 [最高优先级]
🟡 [关注]
🟢 [观察]
```

**输出原则：**
1. 宏观→中观→微观，自上而下推，不自下而上凑
2. 每项资产必须包含事件链（之前→现在），让人看懂变化过程
3. 「我的思考」段必须暴露推理逻辑，不能只说结论
4. 一天内无明显变化 → 「无更新」区块一句话带过，不浪费行数
5. 输出长度：正常日2-3分钟扫完，事件密集日5分钟
6. 用户要看的是「外部敏感度」——知道窗口何时打开、叙事何时转向

### 🔥 全中文铁律（2026-05-18 用户纠正 — 最高优先级）

**所有外部记忆文件、技能文档、分析报告、聊天回复、事件记录、持仓文件，必须全部用中文书写。**
- 禁止任何英文段落、英文标题、英文标签
- 必要的技术术语（CDP、API、URL等缩写）可保留，但旁边要写中文解释
- 文件路径/脚本名称/命令代码块保持原样（这些不是给人读的，是给机器跑的）
- 违反后果：用户看不懂，会生气（"我跟你说100次了"）

### 🔥 日报格式铁律补充：全中文标签（2026-05-20 用户纠正）

**概率总览表中禁止使用符号缩写，必须用完整中文标签：**

✅ 正确格式（日报/聊天中使用）：
```
芯片ETF 020628 → 上行空间50分/下行风险25分 → 上涨概率61%/下跌概率39% → 盈亏比2.78 → 卖出阈值:概率低于20%就卖
```

❌ 错误格式（用户看不懂，会生气）：
```
芯片ETF | ⬆50分/⬇25分 | 61%/39% | 盈亏比2.78 | P≤20%卖
```

**规则：** 文件内部表格可以用缩写节省空间，但凡是发给用户看的报告/聊天回复/邮件，必须用全中文标签格式，每个数字前面带文字说明。

**P值必须带中文标签（2026-05-21 用户纠正）：**
- ✅ `P上涨61%/下跌39%` — 正确
- ❌ `P61%/39%` — 错误（用户看不懂）
- ❌ `P 61%` — 错误（缺少下跌概率）
- 用户原话：\"给我写中文好吗？P括号加个上行\"
### 🔥 传给小龙虾的数据必须同样严格（2026-05-21 新增 — 包括重发规则）

翻车教训（2026-05-21）：第一次发给小龙虾的数据没有指定完整版式要求，他输出的文本摘要信息量大但格式不对。
第二次指定了完整版式要求，他输出了正确格式但信息量缩水了。

**解决方法：**
1. 传给小龙虾的数据必须**写明完整版式的各项要求**（阈值监控/贝叶斯概率更新/今日事件融合/机会成本排序/叙事检验/操作建议）
2. 每项资产下面的**详细新闻事件也必须写明**（如三星罢工的细节、黄金暴跌的具体数字），不能只写结论不写事由
3. 如果反馈回来的报告格式不对 → **追加重发指令**，不将就。但重发时必须注意：**保留第一版的所有细节，不能因为换了格式就丢信息。** 用户要的是格式正确+信息完整的版本，不是二选一。
4. 已清仓的标的必须在数据中**明确标注「已清仓，移除」**，小龙虾不会自动知道哪些卖掉了

### 已清仓持仓的日报展示规则（2026-05-21 确立）
- 不再出现在每日Step 0的新闻搜索中
- 不再出现在每日日报的持仓表中
- 改为每两周决策回看时顺带检查
- 用户原话：\"我卖了之后，你就每隔十几天监测一次，而不是每天都监测\"
- position文件头部标注 ❌已清仓 + 后续监控频率

### 🔥 「待跟进」不允许留在报告里（2026-05-20 用户纠正）

**禁止在报告/日报中使用「待跟进」「待关注」「待查询」等占位词。** 用户原话：\"你写个待跟进是啥意思？那你就跟进呀\"

当需要为一个新资产/新事项建立初始信息时：
1. 当场搜索查询，不能写\"待跟进\"等着下次
2. 给出查到的事实+初始先验概率
3. 如果确实查不到数据（如该基金最新持仓未公布），写\"信息不足\"并注明缺什么，而不是写\"待跟进\"

### 其他铁律

- **核心目的：让用户准确全面地获取「外界正在发生什么（事实）」，不是观点灌输。** 博主预测只是辅助工具——记录他们的逻辑+时间节点，定期与实际走势对比验证。不是为了转发他们的观点，而是为了判断「现实走到哪一步了」。
- **不要丢原始文本** — 用户要的是简洁陈列，不是原文大段粘贴
- **全自动化** — 不要请求用户手动操作
- **多个信息源要交叉对比** — 同一话题的不同观点要放在一起说
- **加入自己的判断** — 不只是转述，要有 Hermes 的综合分析
- **🔥 报告只使用博主监控内容做依据（2026-05-15 用户铁律）** — 不要用通用网络搜索找新闻。所有事件归因和叙事串联，只从已转录的博主视频中提炼。宁可说"博主没说这个"也不要拿过时新闻凑。
- **和 OpenClaw 分工（2026-05-15 用户确立: Hermes主刀, 小龙虾打下手）** — 小龙虾只做短任务（验证数据点、推送渠道），因为P&L计算+事件归因+串联叙事的完整任务链太长他做不了。Hermes用天天基金API直接拉净值算P&L，对照daily-briefing博主语料做事件归因，周日串成周报。整个"拉数据→算钱→归因→串联→出报告"链条由Hermes完成。详见 skill:weekly-holdings-track 的「分工铁律」章节。
- **模型路由原则（2026-05-14 确认）** — 默认DeepSeek V4 Flash主力，**不要全局切换阿里云模型**（qwen-turbo/qwen-plus不支持Hermes工具调用和vision）。简单任务（确认/转发/例行通知）我在代码里手动调阿里云API实现省钱，不切默认模型。**⚠️ 对称急救规则：改配置/模型后10分钟内向对方发确认，超时对方按备份回滚。Hermes备份 config.yaml.bak.***，OpenClaw备份 openclaw.json.bak。**
- **🔥 视频转完文字后立即删除源文件** — 不占硬盘空间
- **🔥 没下载转文字的视频，不准概括内容** — 用户极度厌恨。没实际读过转录文本就不准说"这个视频讲了什么"。宁可说"没看过/没转录"也不能编。这是铁律，不是建议。
- **🔥 用户极度厌恨我问他能自己查的数据。** API/搜索/爬虫能解决的绝不问他。基金代码/净值/市场数据→用天天基金API自动查。不要让他打字告诉我这些。详见 skill:weekly-holdings-track 的 references/fund-code-lookup.md。 — 分析结果中涉及用户持仓（科创芯片/AI/半导体等）的，通过 `openclaw agent --message --session-id main --json` 推给小龙虾整合到每日持仓日报
- **🧹 主动管理记忆空间** — 记忆只有 2200 字符，定期清理过时条目，重要流程写入 skill（不限大小），确保用户交代的事不掉
- **🔍 下载前必须做内容筛选** — 不是所有新视频都值得下载。先看标题+描述判断相关性，只处理跟用户持仓/理财/国际形势有关的视频，跳过扯淡内容（详见「视频内容筛选」章节）

### 🪟 关窗铁律（必读）

**所有浏览器窗口用完后必须立即关闭。** 不得留任何 Chrome 进程存活。

每条规约：
1. 每完成一个浏览器操作单元（如：打开视频页→提取链接→**立即关**）
2. 全部任务完成后，最后一步 **必须杀干净所有残留的 Chrome 进程**
3. 任何时候一个 Chrome 实例用完了，不要留着它"备用"
4. 违反后果：用户机器 i5-3340M 只有 7.1G 内存，几个 Chrome 窗口就能吃光 → 卡死

**⚠️ 定时任务中，最后一步必须包含 `pkill -f "google-chrome" 2>/dev/null || true`**

## 🔍 视频内容筛选铁律（必读）

> **用户2026-05-12原话提炼：** 第3部（下载前筛选）只看 ✅ 跟科创芯片/持仓/AI/养殖/理财/财经/国际形势/宏观有关的，❌ 中国文化/社会杂谈/性别/鸡汤/成功学等扯淡内容一律跳过。

**所有新视频在下载前必须做相关性判断。** 用户明确要求：只处理有价值的视频，跳过扯淡内容。

### ✅ 允许下载（满足任一项即可）

视频标题/描述包含以下关键词或同类语义：

| 类别 | 关键词示例 |
|------|-----------|
| **科创芯片 / 半导体** | 芯片、半导体、光刻、科创芯片、晶圆、封装、EDA、光通信、EML、激光 |
| **持仓相关（AI）** | AI、人工智能、算力、大模型、AGI、GPU、英伟达、NVIDIA、Anthropic、OpenAI、ChatGPT |
| **持仓相关（养殖）** | 猪价、生猪、养殖、猪周期、猪肉、饲料 |
| **持仓相关（其他）** | 黄金、白银、纳指、恒生科技、有色金属、电池、机器人、碳中和、原油、医药 |
| **理财 / 财经** | 理财、股市、A股、基金、ETF、财报、央行、美联储、利率、通胀、加息、降息 |
| **国际形势 / 地缘** | 关税、贸易战、制裁、中美、俄乌、伊朗、中东、欧盟、北约、美国大选、地缘 |
| **宏观 / 经济** | GDP、就业、失业、经济衰退、通缩、通膨、供应链、全球市场 |

### ❌ 跳过下载（满足任一项则跳过）

| 类别 | 关键词示例 |
|------|-----------|
| **文化杂谈** | 中国文化、传统文化、国学、历史故事（非经济史）、书法、茶道 |
| **社会杂谈** | 性别议题、男人怀孕、LGBT、女权、男权、家庭伦理、情感 |
| **扯淡内容** | 成功学、鸡汤、人生哲理、星座、算命、娱乐八卦、明星 |
| **明显不相关的个人生活** | 个人日记、日常、做饭、旅游 |

### ⚠️ 不确定时的处理规则

1. **标题拿不准的** → 用标题关键词搜一下同类内容，确认后再决定
2. **跨类别的**（如"国际形势" + "中国文化"）→ 只要有 1 个匹配 ✅ 类别就下
3. **博主本身有垂直标签的可以直接信任**（如猪猪女王=养殖不筛选，长坡厚雪=理财不筛选，拿幸·AI启示录=AI不筛选）
4. **闭眼看世界**（国际时评类）→ **只看国际形势/地缘/宏观经济标签的视频**，跳过社会杂谈/文化类
5. **当判断一个视频属于 ❌ 类别时，不要下载、不要转文字、不要分析，直接跳过**
6. **用户偏好：分析结果直接在聊天框回复**，而不是另存到文件。除非特别要求保存才写文件。以前存MD的方式已废弃，现在优先即时聊天回复。

## 可扩展性：任意数量博主

本流程支持 **任意数量** 的博主/信息源，不设上限。只需要用户提供每个博主的抖音主页链接（SEC_UID URL）或抖音 ID。

**每个博主独立维护：**
- 独立的状态文件（`~/.hermes/douyin_state_{username}.json`）记录最新已处理视频
- 每天只检查新视频，已处理过的自动跳过
- 同一流水线跑 N 个博主 = 只是循环遍历，不额外增加复杂度

**如果用户说「我会给你很多人的 ID 或主页链接，你用同一套技能跑」→ 这就是本 skill 的用例。**

### 已知博主清单

| 博主名称 | 真实抖音号 | 过滤策略 | 来源 |
|----------|-----------|----------|------|
| 拿幸·AI启示录 | sec_uid: `MS4wLjABAAAAYiyWLrWJmy2JDr3EaQYGNOD9z2ZTCYIOgIXnckGDZYZmyAIMpnZtU99Wr6WpXdbN` | ✅ 信任（AI垂直） | 脚本硬编码 |
| 生猪贸易~芳姐(山东) | sec_uid: `MS4wLjABAAAA84Px8FIb4E4UdQowhWdw_ZhHjXLQA_TeUJv7TygncxMxO-NGSfd5G--s0L66E36w` | ✅ 信任（养殖垂直） | 脚本硬编码 |
| 飞阅硬核财经 | sec_uid: `MS4wLjABAAAAGhkQZE8oAPGw2HoVyyCAAEK3niXCe_2GhrwmL_qePZTTuVdiMgNh21kNEXHcpTp_` | ✅ 信任（财经垂直） | 脚本硬编码 |
| 长坡厚雪 | sec_uid: `MS4wLjABAAAAHxYcDidnyJe_0c8b8fwU0725ODtyWYoiOsg8Q0TKUg0` | ✅ 信任（理财垂直） | 脚本硬编码 |
| 猪猪女王 | sec_uid: `MS4wLjABAAAA9akoFc9rg5UbgoNGRED9mf4NI1X0doHdmglkhrN-SWo` | ✅ 信任（养殖垂直） | 脚本硬编码 |
| 闭眼看世界 | sec_uid: `MS4wLjABAAAAr_z1wGRb1oFflUusY0OYxeoJEs6msQoD16kBaSil9Ghl1ptC5mnKQ0PbPISvYdTR` | ⚠️ 过滤（只看国际形势） | 脚本硬编码 |
| 岩松笔记 | sec_uid: `MS4wLjABAAAAKmBn1W1OtE3A2O79hh_R-HIAMHBX8iuTyoQhGMVVqg3nZMcZiJSfJp8qPCUuOnXc` | ✅ 信任（投资方法论） | 脚本硬编码 |
| 伊娃新营销 | sec_uid: `MS4wLjABAAAA6iF4GTOZwszOizo6WSZxfBUE_sR88Az5DkBVcDR4RJE` | ✅ 信任（养殖/猪周期垂直） | 脚本硬编码 |
| 但宾（但斌·东方港湾） | MS4wLjABAAAA4b19SkuGGVJCNpzGEiPdmvtIuI86lMLV415tjfA2KTw | ✅ 信任（财经/投资） | 脚本硬编码 |
| **宋鸿兵** | **sec_uid: `MS4wLjABAAAAzaye_V0qtP4d7m77UywUBRq7xB9CRiLaeGPfg79hLtQ`** | ✅ 信任（财经/历史） | 脚本硬编码 |
| **付鹏的财经世界** | **sec_uid: `MS4wLjABAAAAy5ym9wTQRRPyS8wY1UA4SXkgUkw7gZyg1Pkws_ppDtO2z0uOpWjbUWassaacpe8C`** | ✅ 信任（宏观/资产配置/149万粉） | 脚本硬编码 |
| 差评君 | **sec_uid: `MS4wLjABAAAAoioyA1wed-aUyuGnSSbUEcjLerCyVtbSCvAxym9ZOWUTEPEdaPbHUlNI4dHOhdMU`** | ✅ 信任（科技科普/478万粉） | 脚本硬编码 |
| **小Lin说** | **sec_uid: `MS4wLjABAAAAunpkE2IXyHAxm4A24G5d1Cf5141pnZy8HwNR5f2-6pI_GYBVR-Pv23uFyfMPB_9I`** | ✅ 信任（财经国际/1170万粉） | 脚本硬编码 |
| **蒋宇飞商业** | **sec_uid: `MS4wLjABAAAACny9yd6GiSgFyyTvE6jt44j0VxBKVVhe69GdklIZIL4`** | ✅ 信任（科技/半导体/产业投资/2026-05-20新增，已建thinker档案） | 用户分享链接 |
| **未知AI博主01** | **sec_uid: `MS4wLjABAAAALpAaN8biUOl9Z3VYzcKltEFdgvK5I2AeVD5bO8NC8IlysGEvUNZnw6A20jjuEpLd`** | ✅ 信任（AI垂直/2026-05-16新增） | 用户分享链接 |
| **大牛洲** | **sec_uid: `MS4wLjABAAAAUg7vX8TvzbeKIsXOeca3DgxNOTpZKDP4eR40AlHkJAwfrYwNI0UP-xPiFsDfBb3K`** | ✅ 信任（AI/腾讯/科技垂直，偏互联网AI生态分析/2026-05-18新增） | 用户分享链接 |

> 博主筛选标准（2026-05-14确认）：粉丝量>=20万 + 内容与持仓方向（芯片/AI/猪周期/宏观/价值投资/金银/科技）相关 + 存在时间>1年 + **不意识形态化**（只需客观事实，不要带着意识形态讲地缘/社会）。未通过：老石谈芯（20万但偏技术不涉投资）、半导体小罗罗（7899粉太小）、老石（85万但记录农村生活）、温铁军（意识形态过重）。**差评君（478万粉科技科普）的优先级低于投资分析类博主，但内容质量高可以加。**

> ⚠️ 宋鸿兵SEC_UID和但宾不同！`抖音主页.txt` 中曾误写成但宾的ID，已修正。**脚本里的才是最新的正确值。**

> 🔍 **监控覆盖缺口分析** → `references/monitoring-coverage-gaps.md`（按持仓金额排的优先级+知乎候选作者列表）
> 
> ⚠️ **宋鸿兵发布平台不仅是抖音（2026-05-19 发现）** — 宋鸿兵的长视频（如"利率风暴席卷全球"）多发在B站和YouTube，抖音只覆盖他的短视频。B站监控在此机器上不可行（IP被B站限流 -799 + 浏览器超时），YouTube被墙。**目前监控盲区：宋鸿兵B站/YouTube长视频内容不会被daily-briefing捕获。** 需要用户手动提供B站视频链接后才能转录分析。

## 💰 Token 成本估算

因为视频下载和转文字全部走本地免费工具，**唯一花钱的是 DeepSeek API 的分析环节**。用 `deepseek-v4-flash` 模型：

| 项目 | 单价 |
|------|:----:|
| 输入（缓存命中） | ¥0.02 / 百万 tokens |
| 输入（未命中） | ¥1 / 百万 tokens |
| 输出 | ¥2 / 百万 tokens |

**单个视频分析约 2000 tokens**（800 字幕 + 200 提示 + 500 输出），**1000 个视频/月 ≈ ¥5~8**。

详见 `references/daily-briefing-cost-estimation.md`。

## 📝 内容浓缩原则（2026-05-15 用户确立）

**用户明确偏好：所有外部信息必须先浓缩再呈现，砍掉废话只留干货。**

用户原话：\"我觉得他废话太多了，你把它浓缩一下\"

### 浓缩标准

| 级别 | 规则 | 示例 |
|:----|:-----|:-----|
| 🥇 **核心事实** | 必须保留 | 数据、政策变化、关键结论、时间节点 |
| 🥈 **逻辑推理** | 只保留因果链 | 不要保留\"接下来我想到了...\"之类的过渡废话 |
| 🥉 **背景铺垫** | **砍** | 用户不需要知道原文是怎么引出的，直接给结果 |
| ❌ **重复强调** | **砍** | \"这很重要\"、\"我们要记住\"、\"总而言之\" 等废话 |
| ❌ **修辞填充** | **砍** | 感叹、情绪表达、不必要的类比比喻 |

### 浓缩后的格式

```
标题（一句话概括核心）
- 关键数据/政策变化
- 要做什么
- 对持仓的影响（如有）
```

做到：原文200字→浓缩后30-50字，不丢核心信息。

## 输出格式

**⚠️ 2026-05-18 报告格式已升级为 v2。详见 `references/daily-report-format-v2.md`。

### 2026-05-19 更新：事件链枢纽 events/ 集成

日报生成前先读 `events/{日期}.md`。新事件只写在 events/ 一次，所有受影响持仓在同一个事件条目里列全。持仓文件引用事件时只写一句话+链接。详见 `00-记忆体系与工作流程说明书.md`。** 以下格式为旧版本，仅做参考。

用户现在偏好**即时聊天回复**，而不是存文件。回复结构：

```
━━ 博主名 ━━━
📅 最新视频：《标题》
📌 核心观点：2-3句话概括
🔥 值得注意的点：炸裂的、反常识的、数据突出的
💡 对持仓的参考价值（如果有）

━━ 博主名 ━━━
...
```

## 💰 余额监控（API成本管理）

**2026-05-14 确认：每天跑日报时顺便查两边API余额。**

脚本：`~/.hermes/scripts/check_api_balance.sh`

### 输出格式
```
--- DEEPSEEK ---
余额: 46.01 CNY (充值 46.01 | 赠送 0.00)

--- 阿里云百炼 ---
✅ API可用（额度未用完）
```

### 注意事项
- **DeepSeek** 有正式余额API（`/user/balance`），可直接查余额
- **阿里云百炼** 是后付费模式，无余额概念。脚本通过调一次 `qwen-turbo`（max_tokens=1）验证API是否可用
- 阿里云查不到具体消费金额，需去控制台看月度账单
- 当DeepSeek余额<10元时，在日报中提醒大好人充值
- 阿里云如果返回400/429，说明可能需要充值或key有问题

### 非预充值的API（无余额接口）
阿里云百炼、通义千问、智谱、百度文心、讯飞星火 — 都是后付费，查不到"余额"。只能用ping测试。

详见 `references/api-balance-monitor.md`。

## 📺 博主观点长期追踪（2026-05-14 新增 — 带预判的逻辑型观点持久化）

> **核心原则：** 不是所有视频内容都要追，只追**带预判、带时间节点、带逻辑推理链**的观点。

## 🧠 思想家档案集成（2026-05-19 新增）

> 每位博主的核心世界观浓缩为 thinkers/{博主}.md，与持仓文件双向互锁。
> 详见：`thinkers/INDEX.md` 和 `00-记忆体系与工作流程说明书.md`

### 日常维护规则

**每天监控+日报时，自动做三件事：**

1. **观点入库** — 转录分析中发现"值得追踪的观点"（带预判+带逻辑链）→ 写入对应 thinker 档案的「最新观点」栏
2. **L2 召回存入** — 关键互锁关系写入 Hindsight，命名规则：`thinker:{博主}:{主题}`
3. **日报引用** — 报告生成前读 thinkers/ 看谁有最新观点影响持仓

### 什么观点值得入库

| 条件 | 说明 |
|:----|:-----|
| ✅ 带时间预判 | 说了大概什么时候会发生 |
| ✅ 带价格/数据目标 | 说了具体数字 |
| ✅ 带因果关系 | 解释了为什么这样判断 |
| ✅ 与持仓相关 | 直接或间接影响持仓 |
| ❌ 纯预测无逻辑 | 只说"会涨"不说为什么 |
| ❌ 纯情绪/喊口号 | 跳过 |
| ❌ 重复已有观点 | 只更新验证状态，不重复录入 |

### 录入格式

```
### 2026-05-19 标题
- **来源：** 抖音/知乎/B站 链接
- **核心观点：** 1-2句话
- **关键数据：** 如果有
- **影响持仓：** [资产名] → [利好/利空]
- **状态：** ⏳待验证
```

### 互锁关系（读 reporter 时自动加载）

```
日报生成流程：
1. 读 positions/{资产}.md → 当前贝叶斯链+互锁↔thinkers
2. 读 thinkers/{博主}.md → 最新观点+互锁↔positions
3. 读 00-宏观传导框架.md → 自上而下传导路径
4. 输出：宏观→仓位→贝叶斯更新→思想家观点引用
```

### 什么算"值得追踪的观点"

| 条件 | 说明 | 例子 |
|:----|:-----|:-----|
| ✅ 带时间预判 | 说了大概什么时候会怎样 | "反转可能要2026底-2027" |
| ✅ 带价格目标 | 说了涨到哪/跌到哪 | "白银可能跌到$40" |
| ✅ 带因果关系 | 解释了为什么这样判断 | "规模化率>70%→底部拉长" |
| ❌ 纯预测无逻辑 | 只说"会涨"不说为什么 | 跳过 |
| ❌ 纯情绪/喊口号 | 没有推理链 | 跳过 |

### 每日日报中的追踪格式

每天出日报时，从当天视频digest中筛选出带预判的逻辑以后，写入**外部记忆05-投资观点与持仓讨论.md**的「博主观点追踪日历」表格。格式：

```markdown
#### 🐷 伊娃新营销 — 猪周期
- **核心观点：** 猪价4元时代，行业60%亏损，底部拉长。**反转可能要到2026年底甚至2027年。**
- **关键数据：** 规模化率超70%→底部拉长；饲料豆粕月涨20%雪上加霜
- **历史参照：** 2006年见底→2007大牛市；2018触底→2019最大风口
- **验证状态：** ⏳ 待验证（目标2026H2-2027）
```

同时更新追踪日历表：

```
| 博主 | 预测标的 | 预测内容 | 预测时间 | 验证截止 | 状态 |
|:----|:--------|:---------|:--------|:---------|:----|
| 伊娃 | 猪周期 | 反转要到2026底-2027 | 2026-04 | 2027-06 | ⏳ |
```

### 验证状态更新

每天日报时检查这些观点的进展：
- ⏳ **待验证** — 还没到时间
- ✅ **已验证正确** — 节点到了，预测对
- ❌ **已证伪** — 节点到了，预测错
- 🔄 **需修正** — 方向对但幅度/时间有偏差
- ❓ **无法验证** — 条件不具备/博主反悔了

### 长期价值

- **筛选博主质量** — 谁的预判准就是优质信源，谁的总是错就降权
- **提供决策锚点** — 伊娃说猪价2026底才反转，那现在建仓就太早了
- **减少重复处理** — 一个观点只入表一次，后续只更新状态不重写

详见 `references/blogger-prediction-tracker.md`。

## 🔥 报告与P&L整合铁律（2026-05-15 更新 — Hermes主刀，小龙虾打下手）

> ⚠️ **2026-05-15 用户明确纠正：小龙虾不适合长链任务。完整报告链条由Hermes完成。**
> 以下规则更新自用户与大好人的多轮讨论（经 DeepSeek V4 Pro + 阿里云 Qwen-max 双模型验证）。

### 🏗️ 三层分析框架（2026-05-16 新增）

所有日报/周报运行在宏观→中观→微观三层框架之下。详见 `~/.hermes/external_memory/05-投资观点与持仓讨论.md` 的宏观层和分析框架。

**从宏观往下推，不从中观/微观往上凑。**

### 📰 新闻链跟踪（2026-05-16 新增）

每项关键资产的每日表现必须记录为 日期|净值变化|触发事件|叙事链 格式，周报时直接引用。新闻链表在 `~/.hermes/external_memory/05-投资观点与持仓讨论.md` 末尾。

> ⚠️ **2026-05-15 用户明确纠正：小龙虾不适合长链任务。完整报告链条由Hermes完成。**
> 以下规则更新自用户与大好人的多轮讨论（经 DeepSeek V4 Pro + 阿里云 Qwen-max 双模型验证）。

**大好人核心原则：所有持仓项按机会成本排序决定资金分配优先级，不是三选一。所有项都买，只是比例跟着置信度走。**

**排序四维度（每日必须带）：**
1. ⬆️ **上行空间** — 涨到哪（合理目标/趋势目标，%）
2. ⬇️ **下行空间** — 跌到哪有支撑/安全边际（%）
3. 🎯 **置信度** — 这个判断多大信（低/中/高/极高）
4. 📊 **盈亏比** — 上行÷下行，划算不划算（倍数）

**规则：** 上行大+下行小+置信度高=配最多仓位，反之配最少。

**报告三要素（用户明确要求）：**
1. 💰 **P&L数字** — 亏了多少/赚了多少，精确到元
2. 🔍 **事件归因** — 哪个事件导致哪个持仓涨跌
3. 📖 **叙事串联** — 周日把整个串起来

**日报格式（2026-05-18 定版 — 见「🔥 日报格式铁律」章节的完整格式定义）：**
```bash
# 天天基金实时净值API（已验证可用）
curl -s 'https://fundgz.1234567.com.cn/js/{基金代码}.js'
```

**详细日报/周报框架见：** `~/.hermes/external_memory/11-日报周报事件跟踪框架.md`

## ⚠️ CRON任务请勿加载本技能

**本技能文件约77KB，在cron任务中加载会导致AI读指令超时（RuntimeError: Connection error），永远不会执行实际的监控/转录/分析步骤。**

cron任务（全量博主视频总结+推小龙虾）必须使用 `daily-cron-exec` 技能（精简版，约15KB），不要加载本技能。

详见：`/home/fw/.hermes/skills/media/daily-cron-exec/SKILL.md`

## 完整流程

### ⚠️ 必须执行 Step 0：新浪财经新闻抓取（2026-05-21 新增 — 自动化输入）

**每天13:00的全量博主监控前，先拉新浪财经的最新新闻作为输入。** 没有新输入，贝叶斯就是空转。

**URL模板：** `https://search.sina.com.cn/search?q={代码}+{名称}&tp=news&range=all&time=day`

**各持仓搜索词：**
| ETF/资产 | 代码 | 新浪搜索词 |
|:---------|:----|:----------|
| 电池ETF | 018926/159147 | 018926 电池 |
| 芯片ETF | 020628/159995 | 020628 芯片 |
| 养殖ETF | 512450 | 512450 畜牧养殖 |
| 海外科技 | 007476 | 海外科技QDII |
| 恒生科技 | 513180 | 恒生科技ETF |
| 有色金属 | 008826 | 有色金属ETF |
| 纳指QDII | 513300 | 纳指ETF |
| 银行 | 001595/512820 | 银行ETF |
| 黄金 | — | 黄金ETF |

**如何执行：** browser_navigate 到搜索URL，从snapshot提取今日新闻链接，点击阅读关键文章。提取事实和数据。不读全文的手机快讯则跳过。

**输出：** 将今日相关新闻摘要写入 events/当天日期.md，作为当日贝叶斯更新的输入素材。
### ⚠️ 抖音监控 — 只调API，CDP只用来拿cookie

> **2026-05-20 澄清：CDP只用于cookie提取这一步（打开about:blank页调Network.getCookies），不访问抖音页面，不走浏览器渲染。** 这不是"走浏览器路线"。

**当前已验证的稳定路线：**
1. **Cookie来源（三路保底）：** CDP提取（Chrome 9222端口在监听时）→ 桌面cookie文件（~/桌面/douyin_com_cookie_最新.txt）→ /tmp/douyin_cookies.txt
2. **调API拿视频列表：** `/aweme/v1/web/aweme/post/?sec_user_id={ID}&count=30` — curl + cookie
3. **调API拿play_addr：** 同上API返回的数据中提取
4. **下载：** curl + 仅Referer头（不传cookie → CDN会400）
5. **转录：** VideoCaptioner Docker → ffmpeg提音频 → transcribe_new.py (BIJIAN ASR)
6. **取回+清理**

**Cookie获取（通用，不挑平台）：**
```bash
# 唯一方案（Chrome v147+）
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --test
# 桌面已有cookie文件：~/桌面/douyin_com_cookie_最新.txt（raw header格式）
```
- **不要用 yt-dlp** — Chrome v147+ 的v11加密不可破解，yt-dlp报 `cannot decrypt v11 cookies`，直接废
- **桌面cookie文件是raw header格式（key=value; key=value），不是Netscape格式**
- `douyin-monitor.py` 的 `get_cookie_str()` 已兼容两种格式（2026-05-20修正）

### 已废弃路线（不要再用）

| 已废弃方法 | 失败原因 | 替代 |
|:-----------|:---------|:-----|
| CDP打开抖音页面搜视频 | 抖音弹验证码/headless检测 | API直调 `/aweme/v1/web/aweme/post/` |
| 复制用户Chrome配置来解密cookie | Chrome147 cookie加密(portal/libsecret)不可解 | CDP Network.getCookies 提取 |
| Playwright + 系统Chrome（非headless） | 依赖用户桌面会话 | API直调 |
| yt-dlp 下载抖音视频 | 频繁报Failed to parse JSON | API直链 + curl |
| 浏览器访问用户主页URL | CAPTCHA拦截 | API `/aweme/v1/web/aweme/post/` |
| **yt-dlp --cookies-from-browser chrome** | **v11加密不可解，只提取44/229非登录cookie** | **cdp-get-cookies.py（CDP通用）** |
**输出：** 新视频列表（标题+描述+ID）+ `~/.hermes/output/video_digest.json`（全量）+ `~/.hermes/output/filtered_digest.json`（仅持仓相关）

### Step 1.5: 🔍 内容筛选（关键步骤）

**在下载之前，必须用视频标题和描述做相关性判断。** 这是节省时间/硬盘/Token的核心环节。

判断方式：
1. 读取每个新视频的 `desc`（描述文字），提取标题关键词
2. 对照「视频内容筛选铁律」的 ✅ 和 ❌ 列表做匹配
3. ✅ 命中任一个 → 标记为「待下载」
4. ❌ 命中任一个 或 都不命中 → **跳过，不做任何处理**
5. 博主本身是垂直领域的（猪猪女王→养殖、飞阅硬核财经→财经等）→ **直接信任，无需逐条筛选**（但闭眼看世界除外，详见筛选表）
6. 2026-05-18 补充：筛选后生成 filtered_digest.json（仅持仓相关），推给小龙虾时只推这个精简版，**不要一股脑把108条全丢给他**
7. **2026-05-19 补充（永久假阳性对策）：** 由于 `save_state` 只存 top 20 导致的假阳性问题，monitor 报告的大量"新视频"中大部分是旧视频。处理时必须**先检查 create_time 时间戳，只处理今天（当天）的视频**。较旧的视频 play_addr 已过期，下载会返回 400。从 state JSON 中提取 create_time（Unix 时间戳）对比当天 00:00 即可。

**实现方式：** `video_topic_filter.py` 脚本（`~/.hermes/scripts/`）提供 `should_download()` 和 `filter_video_list()` 接口，已在 `douyin_monitor.py` 中集成。

### Step 1.5: 写事件链（events/ 枢纽）

**核心变更（2026-05-19 用户确立）：** 一个事件影响多个持仓。如果只写在单个持仓文件里，其他持仓会漏。

**正确做法：**
1. 转录分析结果中，筛选出与持仓相关的观点
2. 判断该观点影响哪几个持仓（可能多个）
3. 写入 `events/{日期}.md`（事件只写一次，列全所有受影响持仓 + 贝叶斯建议幅度）
4. 同时更新对应 `thinkers/{博主}.md` 的「最新观点」
5. 关键互锁写入 L2

**事件条目格式：**
```
### {来源}：{事件标题}

**来源:** 链接
**日期:** YYYY-MM-DD
**摘要:** 1-2句核心事实

**影响:**
| 持仓 | 方向 | 逻辑 |
|:----|:----:|:-----|
| 代码 | 🟢🟡🔴 | 为什么影响 |

**🎲 贝叶斯建议:**
| 持仓 | 当前P(上行) | 调整 | 新P(上行) | 理由 |
|:----|:----------:|:----:|:---------:|:-----|

**对应thinker:** thinkers/博主名.md
**🔗 互锁→** positions/持仓1.md | positions/持仓2.md
```

### Step 1.6: 推筛选后digest给小龙虾

```bash
# 筛选持仓相关的推给小龙虾（用keywords匹配标题）
# 2026-05-18 铁律：不要全量推！只推跟持仓/AI/芯片/猪周期/黄金/原油/国际形势相关的
openclaw agent --session-id main --message "抖音监控完成。发现XX条，筛选后YY条与持仓相关。关键内容：..." --timeout 200
```

### Step 2: 获取视频内容 — 下载+转录

**2026-05-20 已验证的完整管道：API直链 + curl下载 + VideoCaptioner Docker转录**

```bash
# 1. 从API获取play_addr（需cookie，参数count=30）
SEC_UID="博主sec_uid"
COOKIE=$(cat ~/桌面/douyin_com_cookie_最新.txt | tr -d '\n')
curl -s "https://www.douyin.com/aweme/v1/web/aweme/post/?sec_user_id=${SEC_UID}&count=30&aid=1128" \
  -H "User-Agent: Mozilla/5.0 ..." \
  -H "Cookie: ${COOKIE}" \
  -H "Referer: https://www.douyin.com/user/${SEC_UID}" \
  --max-time 15

# 2. 从JSON中提取play_url（video.play_addr.url_list[0]）
#    注意JSON含控制字符，需先 re.sub(r'[\x00-\x1f\x7f]', '', raw)
#    时长字段是毫秒：duration=341543 → 约5.7分钟

# 3. curl下载（不传cookie！只传Referer）
curl -L -o /tmp/video.mp4 \
  -H "Referer: https://www.douyin.com/" \
  -H "User-Agent: Mozilla/5.0 ..." \
  "https://...play_url..." --max-time 120

# 4. 复制到VideoCaptioner容器
sg docker -c "docker cp /tmp/video.mp4 videocaptioner:/app/work-dir/video.mp4"

# 5. ffmpeg提音频
sg docker -c "docker exec videocaptioner ffmpeg -y -i /app/work-dir/video.mp4 -vn -ar 16000 -ac 1 -f mp3 /app/work-dir/video.mp3"

# 6. 转录（BIJIAN ASR）
sg docker -c "docker exec videocaptioner python3 /app/temp/transcribe_new.py /app/work-dir/video.mp3 /app/work-dir/video"

# 7. 取回结果
sg docker -c "docker cp videocaptioner:/app/work-dir/video_全文.txt /tmp/video_全文.txt"
sg docker -c "docker cp videocaptioner:/app/work-dir/video.srt /tmp/video.srt"

# 8. 清理容器
sg docker -c "docker exec videocaptioner rm -f /app/work-dir/video.mp4 /app/work-dir/video.mp3 /app/work-dir/video_全文.txt /app/work-dir/video.srt"

# 9. 清理本地
rm -f /tmp/video.mp4
```

**实测性能（2026-05-20）：** 5.7分钟/38MB视频 → 下载24秒 + 提音频5秒 + 转录60秒 ≈ 2分钟

**已知风险：**
- BIJIAN ASR依赖 `member.bilibili.com` DNS解析，间歇性失败 → 重试一次
- play_addr几分钟后失效 → 拿到URL立刻下载
- 不要传Cookie到CDN → 400 Bad Request

### Step 2.5: 下载视频（次选，仅当 CDP 摘要不够用时）

**⚠️ 不要用 yt-dlp 下载抖音视频！** yt-dlp 经常报 `Failed to parse JSON` 或 `Fresh cookies are needed`，已验证不可靠。

**正确做法：API直链 + curl 下载（2026-05-13 已验证）**

```python
import json, urllib.request, http.cookiejar, subprocess

# 1. 加载cookie
cj = http.cookiejar.MozillaCookieJar()
cj.load('/tmp/douyin_cookies.txt')
cookies = {c.name: c.value for c in cj}
cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])

# 2. 调API拿视频列表+play_addr
# 注意：必须用 sec_uid 调 /aweme/v1/web/aweme/post/，不能用 /aweme/detail/
sec_uid = '博主的SEC_UID'
api = f'https://www.douyin.com/aweme/v1/web/aweme/post/?sec_user_id={sec_uid}&count=30&aid=1128'
req = urllib.request.Request(api)
req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
req.add_header('Cookie', cookie_str)
req.add_header('Referer', f'https://www.douyin.com/user/{sec_uid}')
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode())

for video in data.get('aweme_list', []):
    vid = video['aweme_id']
    play_url = video['video']['play_addr']['url_list'][0]  # CDN直链
    
    # 3. ⚠️ curl下载，不要传Cookie！(否则400)
    subprocess.run([
        'curl', '-L', '-o', f'/tmp/{vid}.mp4',
        '-H', 'Referer: https://www.douyin.com/',
        '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        play_url
    ], timeout=120)
```

**关键坑：**
- ❌ 下载时传Cookie → CDN返回 `400 Bad Request (Request Header Or Cookie Too Large)`，因为cookie字符串有100+个
- ✅ 下载时只传Referer，不传Cookie
- ❌ 用urllib/requests下载 → 也会遇到同样问题，用curl最干净
- ⚠️ play_addr URL有时效性，拿到后必须立刻下载
- 旧视频（几天前的）play_addr已过期，会返回400。每天13:00跑当天新视频即可
- ❌ **detail API (`/aweme/v1/web/aweme/detail/`) 返回空响应** — 不要用它获取 play_addr。必须用 `post` API（`/aweme/v1/web/aweme/post/?sec_user_id=...`），它返回包含 `play_addr` 的完整 `aweme_list`。用 `count=30` 可获取全部视频数据。
- ⚠️ **抖音API返回的JSON包含控制字符** — 用标准 `json.loads` 会报 `Invalid control character` 错误（在 JSON 较长时出现）。处理前必须用 `re.sub(r'[\x00-\x1f\x7f]', '', raw)` 清除控制字符后再解析。示例：
  ```python
  import re, json
  raw = resp.read().decode()
  clean = re.sub(r'[\x00-\x1f\x7f]', '', raw)
  data = json.loads(clean)
  ```
- ⚠️ **对已知 aweme_id 获取 play_url 的快捷方法** — 如果已经知道博主的 sec_uid 和目标 aweme_id，不需要重新扫描全量：
  1. 从 Netscape cookie 文件构建完整 cookie_str（使用 `http.cookiejar.MozillaCookieJar`）
  2. 调 `post` API 获取该博主最新 N 条视频数据（内含 play_addr）
  3. 在返回的 `aweme_list` 中按 aweme_id 匹配目标视频
  4. 立即用 curl（不传cookie）下载 play_addr URL
  Cookie构建示例：
  ```python
  import http.cookiejar
  cj = http.cookiejar.MozillaCookieJar()
  cj.load('/tmp/douyin_cookies.txt')
  cookie_str = '; '.join([f'{c.name}={c.value}' for c in cj])
  # 通过 -H "Cookie: $cookie_str" 传给 curl
  ```

### Step 3: 转文字 — 直接调用 VideoCaptioner Docker 容器内部转录脚本（推荐）

**⚠️ 2026-05-18 发现并采用：Playwright/CDP 路线不再推荐。** 用 `docker exec` 直接调用 VideoCaptioner 容器内的 `transcribe_new.py` 脚本，使用必剪(BIJIAN) ASR引擎。无需打开浏览器、无需显示、无需 CDP。

#### 完整管道（已验证 ✅ 2026-05-18 — 所有 docker 命令需用 sg docker -c 包装）

```bash
#!/bin/bash
# 参数
VIDEO_LABEL="$1"       # e.g. "naxing-OpenAI"
VIDEO_AWEME_ID="$2"    # e.g. "7641066969520721187"

# 注意：本机的 docker 需要 sg 组权限，所有 docker 命令必须通过 sg docker -c 包装

# 1. 下载视频到 /tmp（使用 API 直链 + curl）
# （详见 Step 2 的下载脚本）

# 2. 复制到容器
sg docker -c "docker cp /tmp/${VIDEO_LABEL}.mp4 videocaptioner:/app/work-dir/${VIDEO_LABEL}.mp4"

# 3. 容器内提取音频（ffmpeg已装）
sg docker -c "docker exec videocaptioner ffmpeg -y -i /app/work-dir/${VIDEO_LABEL}.mp4 \
  -vn -ar 16000 -ac 1 -f mp3 /app/work-dir/${VIDEO_LABEL}.mp3"

# 4. 转录（BIJIAN ASR，需联网上传到Bilibili服务端）
sg docker -c "docker exec videocaptioner python3 /app/temp/transcribe_new.py \
  /app/work-dir/${VIDEO_LABEL}.mp3 /app/work-dir/${VIDEO_LABEL}"

# 5. 取回结果
sg docker -c "docker cp videocaptioner:/app/work-dir/${VIDEO_LABEL}.srt /tmp/${VIDEO_LABEL}.srt"
sg docker -c "docker cp videocaptioner:/app/work-dir/${VIDEO_LABEL}_全文.txt /tmp/${VIDEO_LABEL}_全文.txt"

# 6. 🔥 清理容器内临时文件
sg docker -c "docker exec videocaptioner rm -f \
  /app/work-dir/${VIDEO_LABEL}.mp4 \
  /app/work-dir/${VIDEO_LABEL}.mp3 \
  /app/work-dir/${VIDEO_LABEL}.srt \
  /app/work-dir/${VIDEO_LABEL}_全文.txt"
```

#### 转录结果处理

`_全文.txt` 文件中每个字符之间有空格（BIJIAN ASR的字级时间戳输出），分析前需清理：

```python
import re
with open(f'/tmp/{label}_全文.txt') as f:
    text = f.read()
clean = re.sub(r' (?=[\u4e00-\u9fff\u0041-\u005a\u0061-\u007a0-9])', '', text)
clean = re.sub(r'(?<=[\u4e00-\u9fff\u0041-\u005a\u0061-\u007a0-9\.\%]) ', '', clean)
```

#### 耗时参考

| 视频时长 | 下载 | 音频提取 | 转录(BIJIAN) | 总计 |
|:--------|:----:|:--------:|:------------:|:----:|
| ~14分钟(81MB) | ~30s | ~5s | ~60s | ~2min |
| ~3分钟(51MB) | ~15s | ~3s | ~30s | ~1min |

#### 三种转录方式对比

| 方式 | 可靠性 | 速度 | 依赖 | 推荐度 |
|:----|:------|:----|:-----|:------:|
| **Docker exec + transcribe_new.py（必剪ASR）** | ⭐⭐⭐⭐ 需联网DNS解析 | ⭐⭐⭐⭐ 30-60s/视频 | Docker运行中 | ⭐⭐⭐⭐⭐ **首选** |
| Playwright + Streamlit UI | ⭐⭐ 需显示+浏览器 | ⭐⭐ 5-10分钟/视频 | Chrome + 显示 | ⭐⭐ 备用 |
| CDP WebSocket | ⭐⭐ 需Chrome远程调试 | ⭐⭐ | Chrome + CDP | ⭐ 不推荐 |

#### 已知问题

- **🚨 BIJIAN ASR 可能因 DNS 解析失败而崩溃**（`Failed to resolve 'member.bilibili.com'`）。这是此机器的间歇性网络问题。重试一次通常可解决。
- **FASTER_WHISPER / WHISPER_CPP** 在容器内可用但不一定能直接运行 — `FasterWhisperASR` 需要 `faster-whisper-xxl` 二进制文件，`WhisperCppASR` 需要 `whisper-cpp` 二进制和 `ggml` 模型文件。这些文件在本环境中未预装。如需离线转录，需先下载模型。

### Step 4: 分析→入库→贝叶斯更新（八步互锁闭环）

**转录完成后，必须按严格顺序执行以下步骤，不能跳步、不能漏。**

```
  ↓ Step 1
提炼核心观点：逻辑链、时间节点、数据、预判方向
  ↓ Step 2
判断影响哪些持仓和框架（可能多个）
  ↓ Step 3 [events/]
写 events/{当天日期}.md
→ 一个事件一个条目，列全所有受影响持仓
→ 更新 events/INDEX.md
  ↓ Step 4 [thinkers/]
更新对应 thinkers/{博主}.md 的「最新观点」栏
→ 更新 thinkers/INDEX.md（新博主首次建档）
  ↓ Step 5 [宏观框架]
如涉及宏观层 → 更新 00-宏观传导框架.md
  ↓ Step 6 [positions/]
更新 positions/{资产}.md 的贝叶斯概率
→ P(上行)调整=f(证据等级)：多源共识+2~5pp | 单博主坚实+1~2pp | 纯观点±0
→ 写思考过程 + 更新文件头部P值
  ↓ Step 7 [23-贝叶斯日志]
写一行摘要到 23-贝叶斯更新日志.md
  ↓ Step 8 [互锁收尾清单]
□ INDEX.md（如果涉及L3框架原则，也要更新00-宏观传导框架.md）？
□ KEYWORD_INDEX.md？
□ events/INDEX.md？
□ thinkers/INDEX.md？
□ 99-灾难恢复？
□ Hermes急救手册？
□ L1记忆（memory tool）？
□ L2 hindsight_retain？
□ daily-briefing skill/douyin-monitor.py 博主列表？
```

**⚠️ 贝叶斯链先验传播检查（2026-05-20 新加 — 芯片ETF链断裂教训）：**

当同一个持仓文件有多个事件更新时，**必须检查先验链的一致性**：

```
错误：每个事件各自写自己的先验，忽略上一条的后验
  → 05-19 付鹏：先验53%（错，应为60%）
  → 05-20 蒋宇飞：先验49%（错，链已断）

正确：逐条传播
  → 05-18 后验=60% → 05-19 先验=60% → 05-19 后验=56%
  → 05-20 先验=56% → 05-20 后验=...
```

**检查方法：** positions/{资产}.md 里每条更新的「先验」= 上一条的「后验」？如果不等，链断了，需要修复。

**🔄 价格校准（2026-05-20 新加 — 用历史净值验证贝叶斯方向）：**

每个事件写入后，查一下当日净值变化，判断价格反应是否符合预期：

```
例：05-13 特朗普访华（电池利好）→ 当日电池ETF +3.43% ✅ 符合
例：05-14 渗透率破60%（大利好）→ 当日电池ETF -3.31% ⚠️ 利率利空压制
```

- 价格反应符合预期 → 贝叶斯方向合理
- 价格反预期 → 可能有未知因素在定价，需要找原因
- **不过拟合：** 看大趋势（涨/跌/震荡），不纠结精确百分点

**铁规：改任何一个文件后必须对着Step 8的清单过一遍。**

### Step 5: 生成日报 — 从positions/读取数据

**每个资产的数据源：** `~/.hermes/external_memory/positions/{资产名}.md`

读取方式：
1. 从 `positions/*.md` 读取该资产的事件链+贝叶斯最新状态
2. 从 `05-投资观点与持仓讨论.md` 读取上行/下行空间判断
3. 从 `23-贝叶斯更新日志.md` 获取聚合视图
4. 输出「今日贝叶斯更新」区块

格式见「🔥 日报格式铁律」章节。

读取SRT内容，提炼后在聊天框直接回复，格式见「输出格式」章节。

### Step 6: 多源对比 — 只陈列差异，不分析判断

如果是同话题，对比各博主的观点差异、信息差、独特角度。只陈列事实差异，不加判断。

### Step 7: 输出三层格式日报 → 直接回复用户

按「三层格式铁律」输出：陈列 → 机会成本标记 → 反向思考提示。不要加"我的综合分析"。

### Step 5: 删除视频 + 推送持仓信息给 OpenClaw

**🔥 删除视频源文件：**
```bash
rm -f /tmp/video_download.mp4 /tmp/video_download_*.mp4
```
（转文字完成后视频文件不再需要，节约硬盘）

**📋 推送博主语料到video_digest.json（供P&L归因用）：**
如果视频分析结果中包含与用户持仓相关的内容，写入 `~/.hermes/output/video_digest.json`。
报告整合由Hermes完成（见 skill:weekly-holdings-track），小龙虾的职责收窄为验证数据点和推送渠道。

推送语法（必要时通知小龙虾）：
```bash
openclaw agent --message "需要验证：芯片ETF今日净值是否为3.3419？" --session-id main --json
```
注意：**不要加 `--deliver`**，否则会报 "Channel is required" 错误。

---

**🧹 最后清理：杀掉所有本流程打开的 Chrome 进程：**
```bash
pkill -f "google-chrome.*--remote-debugging" 2>/dev/null || true
```

## 🔴 最高优先级跟踪：芯片回调入场机会（2026-05-16 用户确立）

> **用户说这个最重要，每天日报必须检查。** 见 `chip-pullback-watch-tracklog.md`（外部记忆根目录）。

**核心逻辑：** 习近平飞美国（国事级缓和信号）→ 国产替代过热预期降温 → 芯片ETF回调 → 但国产替代基本面没变 → 回调=入场机会。

### 每日检查清单（日报时必跑）

| # | 检查项 | 方法 |
|:--|:-------|:-----|
| 1 | 020628最新净值 | 天天基金API `curl -s 'https://fundgz.1234567.com.cn/js/020628.js'` |
| 2 | 另一个芯片ETF净值 | 确认代码后用同API |
| 3 | 近期走势方向 | 连续跌了几天？跌幅多少？ |
| 4 | 博主是否提到国产替代降温 | 重点看闭眼看世界(国际形势)、飞阅/宋鸿兵(财经)、拿幸(AI) |
| 5 | 中美关系具体新闻 | 习近平访美进展、关税谈判、高层会晤 |
| 6 | 芯片情绪判断 | 博主还在吹芯片还是开始谨慎？ |

### 触发条件
- 🟢 **入场信号（越强越买）：** 020628连续跌3天 + 博主提国产替代降温 + 有实际中美缓和新闻 + 跌幅>大盘（杀溢价）
- 🔴 **逻辑证伪信号（放弃假设）：** 中美反而恶化（加税/制裁加码）→ 国产替代政策加速出台 → 芯片不跌反涨

**关联标的：** 020628 汇添富科创板芯片ETF联接A（已有¥1,502，+24.57%）
**完整跟踪：** `chip-pullback-watch-tracklog.md`

## 🔵 低频率跟踪：恒生科技（2026-05-16 用户确认）

**策略：** 不每天盯。**等右侧信号**——跟养殖ETF一样，磨底差不多了但不左侧抄底。

**监测频率：** 不主动每天盯，但设置新闻触发规则：
- 美联储降息/加息/暂停
- 中美关系重大变化
- 腾讯/阿里等核心成分股财报暴雷或超预期
- 恒生科技指数单周涨跌>5%

**光环属性：** 国内互联网最强的一批→两头挨打（美股强被抽血，美股弱被带崩）→但流动性拐点来了它涨最快。
**详细分析：** `外部记忆/05-投资观点与持仓讨论.md` 的「恒生科技」节。

## 定时任务与时间线 (cronjob)

### ⏰ 每日时间线（2026-05-21 更新 — 加入新浪新闻Step 0）

```
09:00  宋鸿兵抖音监控（独立预警，不等待日报）— 已完成
**13:00  Step 0: 新浪财经搜各持仓新闻 → 写入events/当天**
**13:00  Step 1-3: 全量博主视频监控→下载→转文字→分析→写 video_digest.json**
**13:30  Step 4: 新浪新闻 + 博主观点 → 联合分析 → 贝叶斯更新**
15:30  Hermes P&L计算 + 事件归因 + 贝叶斯更新 + 出日报（≤5行）→ 推给大好人
      小龙虾职责：验证净值数据点、推送微信渠道（短任务）
周日  Hermes 串起整周 → 叙事串联 + 梯队复盘 + 博主共识 → 周报
```

**关键注意事项：**
- 原来全量博主监控没有被自动化（只有宋鸿兵），2026-05-13 已补上 13:00 的全量任务
- 13:00 跑完后必须写 `~/.hermes/output/video_digest.json` + 通知小龙虾
- 不要等到 15:30 才跑——小龙虾需要 digest 来写日报

### 当前定时任务列表

| 任务名 | 时间 | 内容 | 新增于 |
|--------|:----:|:-----|:------|
| 宋鸿兵抖音监控 | 每天 9:00 | 独立预警，不等日报 | 之前 |
| **全量博主视频总结+推小龙虾** | **每天 13:00** | **全量博主→下载→分析→video_digest.json→通知小龙虾** | **2026-05-13** |
| 中期选举日日盯盘 | 每天 18:00 | 纳指/恒生科技/AI监控，9月后高频模式 | 2026-05-13 |
| 锻炼提醒 | 一三五 10:00 | 推电瓶车走路 | 之前 |
| 长期目标每周提醒 | 每周日 10:00 | 闲鱼/学历/拍摄提醒 | 之前 |
| OpenClaw 主动反思（promote） | 每周日 10:00 | `openclaw memory promote --apply` | 之前 |
| 外部记忆周回顾 | 每周日 11:00 | 扫描外部记忆文件，检查待办/提醒 | 之前 |
| 中期选举市场监控 | 每周一 10:00 | 中期选举相关市场走势 | 2026-05-13 |
| 原油监控（付鹏观点验证） | 每周三 10:00 | 油价+库存+停战进展，验证付鹏论 | 2026-05-13 |
| **博主观点两周跟踪** | **每14天一次（cron: 7d3a624367c8）** | **扫外部记忆05的博主预测→对比现实走势→更新验证状态→出跟踪简报** | **2026-05-14** |

## 🗄️ 存储策略（2026-05-12 决定）

当前所有分析报告存为纯MD文件在 `~/桌面/每日视频总结/`。16个文件时 ripgrep 搜文件名秒出。

| 阶段 | 方案 | 原因 |
|------|------|------|
| 当前 (<500文件) | **纯MD + ripgrep** | 零维护零成本，关键词匹配够用 |
| 未来 (>500文件 且 语义检索刚需) | **Sqlite-Vector** 或 写 `search_videos.py` 本地脚本 | 上向量库需要额外embedding API费用，优先级低 |

**替代方案（如果以后需要）：**
- `search_videos.py` 脚本（grep/ripgrep后端）— 比向量库省心省钱，零API费用
- OpenClaw 自带 `openclaw memory search`（FTS+向量搜索），但只索引自己的工作区文件，不建议强行改它的配置

详见 `06-环境备忘.md` 的「存储策略备忘」章节。

## 📁 文件夹结构

所有输出到 `~/桌面/每日视频总结/`：

```
📁 每日视频总结/
├── 📄 YYYY-MM-DD_博主名分析.md    ← 各博主分析
├── 🗒️ 博主名字幕.srt               ← 原始字幕备查
├── 📄 YYYY-MM-DD_信息简报.md       ← 整合后的简报（邮件内容）
```

## 涉及的工具和脚本

- `~/.hermes/scripts/douyin-monitor.py` — **抖音博主监控主脚本（纯API方式，2026-05-14重写）**。硬编码10个博主的SEC_UID，支持 `--single "博主名"` 单博主模式。不走浏览器。
- `/tmp/douyin_cookies.txt` — 抖音cookie文件，含sessionid即有效。过期周期3-7天。过期时手动：`yt-dlp --cookies-from-browser chrome --cookies /tmp/douyin_cookies.txt --skip-download "https://www.douyin.com/video/1"`
- `~/.hermes/douyin_state/` — 每个博主的独立状态文件（已处理视频ID列表）
- `~/.hermes/output/video_digest.json` — 当日digest，供小龙虾15:30日报用
- `~/.hermes/scripts/video_topic_filter.py` — 视频主题过滤器。提供 `should_download()` 和 `filter_video_list()` 两个接口
- `~/.hermes/scripts/video_caption_auto.py` — **已弃用** Playwright 转文字（需显示，改用 Docker exec 方式） ⚠️ 页面已被替代
- `~/.hermes/scripts/cron_health_check.sh` — **管道健康检测脚本（2026-05-22新增）**。每6小时自动检查所有cron任务状态，有失败告警用户。

## 📜 技能整合历史

| 日期 | 动作 | 说明 |
|:----|:-----|:-----|
| 2026-05-16 | `social-media-monitor` → 合入本技能 | 完全重叠的抖音监控内容、脚本、参考文献已合并至此。原技能已归档至 `.archive/`。 |

### 三阶过滤管道（2026-05-18 确立 — 防信息过载）

不是每条信息都触发贝叶斯更新。设三级闸门：

```
Gate 1: 相关性过滤
├─ 是否涉及任一持仓资产？ → 通过
└─ 是否涉及宏观拐点（美联储/中美/地缘）？ → 通过
└─ 以上皆否 → 丢弃（仅记日记，不触发贝叶斯）

Gate 2: 证据等级评估
├─ 高（多源共识/坚实逻辑+数据） → 进入贝叶斯
├─ 中（单一博主+坚实逻辑） → 暂存，等第2条来源确认后更新
└─ 低（纯观点无逻辑/重复观点） → 仅存档，不触发更新

Gate 3: 变化幅度阈值
├─ 置信度变化 ≥ 10pp → 记录为一次有效贝叶斯更新
├─ 置信度变化 < 10pp → 仅记备注，不生成正式日志
└─ 同资产同日多条信息 → 合并为一次更新
```

**输出：** 日均通过Gate3的更新约1-3项，其余正常过滤。

---

## 🧠 贝叶斯更新工作流（2026-05-18 大好人确立）

> 核心思想：每项资产有独立贝叶斯链。新信息过三关(Gate1相关/Gate2证据等级/Gate3变化≥10%) → 更新后验概率 → 重算盈亏比 → 调仓位建议。

**每天日报生成时顺带执行，不额外调API。** 详见 `references/bayesian-update-workflow.md`。

### 日报中的「今日贝叶斯更新」区块

在现有三层格式后追加：

```
━━ 今日贝叶斯更新 ━━
🔄 更新 N项：
  【资产名】P(上行):X%→A% | 证据:[摘要] | 仓位:[动作] | [验证标记]
➡️ 无更新 M项：今日无相关信息
```

### 更新日志存储

`~/.hermes/external_memory/23-贝叶斯更新日志.md` — 纯追加，每次更新按标准格式写入。

### 关联文件

| 文件 | 内容 |
|------|------|
| `references/bayesian-update-workflow.md` | 完整贝叶斯更新工作流（三阶过滤+日志格式+修正规则+月校准） |
| `references/three-gate-filter.md` | 三阶过滤管道详解（相关性/证据等级/变化阈值 — 防信息过载） |
| `references/net-value-is-outcome.md` | 净值是果不是因 — 核验规则与月校准流程 |
| `references/positions-directory.md` | positions/目录结构（L3互锁文件）与日报读取方式 |

---

## 关联参考文件

| 文件 | 内容 |
|------|------|
| `references/video-content-filter.md` | 完整过滤关键词列表、信任博主白名单、调用方式 |
| `references/economic-cycle-monitoring.md` | 银行+猪周期联动框架、分批建仓模板、"三问"投资评估标准 |
| `references/openclaw-memory-research.md` | OpenClaw 自带 memory/dreaming/memory-wiki 功能研究 |
| `references/daily-briefing-cost-estimation.md` | Token 成本估算明细 |
| `references/douyin-api-monitor.md` | 抖音纯API监控方案（2026-05-14最终确认，已验证可行） |
| `references/douyin-api-download-workaround.md` | yt-dlp 失效时通过API直链下载的备用方案 |
| `references/opportunity-cost-framework.md` | 每日日报机会成本排序框架（四维度+仓位规则+报告结构） |
| `references/batch-transcribe-pipeline.md` | 批量转录管道详细步骤（从social-media-monitor吸收） |
| `references/blogger-position-tracking.md` | 博主观点追踪指导（从social-media-monitor吸收） |
| `references/blogger-biweekly-tracker.md` | 博主观点双周跟踪（从social-media-monitor吸收） |
| `references/blogger-selection-process.md` | 筛选新博主完整流程（从social-media-monitor吸收） |
| `references/douyin-download-method.md` | 抖音视频下载方法详解（从social-media-monitor吸收） |
| `references/fund-holdings-query.md` | 基金持仓信息查询（从social-media-monitor吸收） |
| `references/portfolio.md` | 投资组合参考（从social-media-monitor吸收） |
| `references/wall-street-chen-sijin-us-stock-risk.md` | 华尔街陈思进美股风险分析（从social-media-monitor吸收） |
| `references/huang-renxun-cmu-2026-speech.md` | 黄仁勋CMU 2026演讲分析（从social-media-monitor吸收） |
| `references/workflow-2026-05-11.md` | 工作流历史参考（从social-media-monitor吸收） |
| `templates/analysis-report.md` | 视频分析报告模板（从social-media-monitor吸收） |
| `scripts/download_by_topic.py` | 按主题+博主匹配下载抖音视频（从social-media-monitor吸收） |
| `scripts/download_douyin_videos.py` | 批量抖音视频下载脚本（从social-media-monitor吸收） |
| `scripts/video-caption-pipeline.py` | 自动字幕生成管道脚本（从social-media-monitor吸收） |
| `scripts/batch-transcribe-videocaptioner.sh` | 批量VideoCaptioner转录脚本（从social-media-monitor吸收） |

> 批量转录管道的详细步骤（下载→复制容器→ffmpeg提音频→ASR→取回→分析→推送）见 `references/batch-transcribe-pipeline.md`。
> 转录分析完成后按 `references/analysis-interlocking-workflow.md` 的8步闭环入库，不能跳步。所有文件必须用全中文书写（代码块除外）。
> 完整视频下载脚本（按主题匹配+按博主匹配）见 `scripts/download_by_topic.py` 和 `scripts/download_douyin_videos.py`。
> 批量转录自动化脚本见 `scripts/batch-transcribe-videocaptioner.sh`。

## 🚨 铁律：管道存活检查（2026-05-22 新增 — 8天崩溃教训）

### SKILL.md文件大小直接破坏cron任务（最高优先级）

本skill约77KB。Hermes cron加载时，AI必须全文阅读后才能执行任务。
- SKILL.md > 30KB → cron极大概率超时断连，报 `RuntimeError: Connection error`
- 后果：cron看起来"跑了"（状态=error），但实际**一行脚本都没执行**
- 2026-05-14~05-22实证：每日13:00全量博主cron连续8天超时，0条视频被下载/转录/入库

**修复方法：** cron prompt必须自包含且精简（≤50行），禁止加载本skill的完整内容。
不要在该cron的skills列表里列出daily-briefing。

✅ 正确做法 — 精简版cron prompt模板：
```
【每日视频监控任务 - 精简版】
今天日期：$(date +%Y-%m-%d)

Step 1：运行 python3 /home/fw/.hermes/scripts/douyin_monitor.py
Step 2：读取报告 ~/桌面/每日视频总结/$(date +%Y-%m-%d)_监控报告.md
Step 3：有新视频→下载+转录。没有→输出 [SILENT]
Step 4：分析→写 events/→更新thinkers/→贝叶斯更新
Step 5：推给小龙虾：openclaw agent --session-id main --message "..." --timeout 120
Step 6：清理 rm -f /tmp/*.mp4 /tmp/*_全文.txt /tmp/*.srt
```

### cron中AI不会自动执行脚本（2026-05-22 发现）

cron任务中，**AI经常跳过"运行脚本"的指令，改为读缓存/digest文件。**
实证：宋鸿兵监控cron的prompt说"执行douyin_monitor.py"，但AI响应是"从digest中提取了5条宋鸿兵新视频"——它根本没跑脚本，读的是过时的digest。

**修复：** cron prompt必须明确要求先terminal执行脚本，把真实输出作为输入。不要相信AI会主动跑脚本。

### 转录管道存活检查（日报前必须做）

每天日报前验证最近一次转录文件的时间戳：
```bash
ls -lt ~/桌面/每日视频总结/ | head -5
```
- 如果最新文件 > 3天前 → 管道断了，先修管道再出日报
- 13:00 cron报error → 立即检查root cause（大概率SKILL.md太大）

### 推给小龙虾必须在日报前完成

用户铁律：
1. 13:00全量监控分析完 → 立即推给小龙虾（不等日报）
2. 内容：事件摘要 + 受影响持仓 + 贝叶斯调整
3. 格式：写明完整版式要求，不要只给结论不给事由
4. 语法：`openclaw agent --session-id main --message "..." --timeout 120`

### save_state已知bug：旧视频重复标记为"新"

douyin_monitor.py的save_state上限不够时，旧视频溢出后重新标记为"新"。
**修复（2026-05-22）：** known_ids[:100] → known_ids[:200]

## ⚠️ Pitfalls

- ⚠️ **🧠 博主信息入库流程请参照 `skill:thinker-info-to-belief`** — 该技能详细描述了信息分层(事实/洞察/框架)→events写入→贝叶斯更新(以前P→现在P)→互锁验证的完整步骤。本技能中的「八步互锁闭环」是概览，「thinker-info-to-belief」是详细执行手册。两技能应配合使用。

- ⚠️ **🏗️ positions/目录是L3贝叶斯互锁文件（2026-05-18建立）** — 每项持仓在 `~/.hermes/external_memory/positions/{asset}.md` 有独立文件，事件+概率合一。日报时从此处读取完整贝叶斯链。详见 `20-三层互锁架构设计.md`。

- ⚠️ **Cookie文件格式坑（2026-05-20 修正）：** 桌面 `~/桌面/douyin_com_cookie_最新.txt` 是raw header格式（`key=value; key=value`），不是Netscape格式。`douyin-monitor.py` 的 `get_cookie_str()` 已改为双格式兼容：先试MozillaCookieJar.load()，失败则直接读raw字符串。修复前fallback路径→返回True但没复制cookie→get_cookie_str()报LoadError崩溃。修复后fallback先复制桌面cookie到/tmp/douyin_cookies.txt再返回True。
- ⚠️ **全量下载+转录已验证（2026-05-20）：** 完整管道走通：API获取play_addr→curl下载（不传cookie，只传Referer）→docker cp→ffmpeg提音频→transcribe_new.py(BIJIAN ASR)→docker cp取回→清理。5.7分钟/38MB视频全程约2分钟。
- ⚠️ **CDP不可用时桌面cookie是可靠保底：** 桌面 `douyin_com_cookie_最新.txt` 含sessionid，直接读即可。无需启动Chrome CDP。见 `local-chrome-cdp-bridge` 技能的「兜底方案」章节。
- ⚠️ **监控仅覆盖抖音，不包含B站/YouTube。** 宋鸿兵等博主的部分视频发在B站而非抖音（2026-05-19验证）。如果用户反馈"XX视频没被监控到"，先确认视频平台——不要在抖音里找B站的内容。目前未实现B站/YouTube监控。
- ⚠️ **B站API本机被严重限流**，浏览器也超时。需要B站视频时只能靠用户手动分享链接。

- ⚠️ **📧 发邮件技能已就绪（2026-05-18）** — 通过 `skill:email-sender` 一键发送。QQ邮箱 SMTP_SSL smtp.qq.com:465，授权码 `eordxzfcwxadciag`。如需发日报直接调用。

- ⚠️ **🛡️ Hindsight守护已部署（2026-05-18）** — `~/.hermes/scripts/hindsight_guardian.sh` 每3分钟 cron 自动巡检，杀多余进程保健康进程。不再叠罗汉卡死电脑。

- ⚠️ **🚨 净值是果，信息是因（2026-05-18 大好人纠正）**

- ⚠️ **🚨 净值是果，信息是因（2026-05-18 大好人纠正）** — 净值/价格是贝叶斯核验工具，不是推理原料。贝叶斯概率应从信息层（新闻/政策/博主观点/数据报告）推导，不能从净值反推。净值只用于月校准：对比月初P(上行)预测vs月末实际走势。

- ⚠️ **🚨 不瞎编概率，注明数据来源（2026-05-18 大好人纠正）** — 每条概率更新必须注明数据来源。来源不明的概率=瞎编，比不编更坏。正确做法：「信息不足→写'信息不足'，不编数字」。概率表必须加「数据来源」列。

- ⚠️ **🚨 AI在cron任务中会编造数据（2026-05-18发现）** — 当cron提示词说"用工具查实时数据"时，AI经常**忽略工具指令**，直接用训练数据编造价格/数字。**修复：** cron提示词必须包含大红字警告"绝对不要用你的训练数据推测当前价格！宁缺毋滥！获取不到就写获取失败"。更好的做法：让cron先跑脚本拉真实数据，把脚本输出注入到prompt中，不给AI编的机会。详见今日会话关于原油cron的重写。
- ⚠️ **🚨 推给小龙虾前必须先筛选** — 发现108条新视频≠全部推给小龙虾。先filtered_digest.json只推持仓相关的（通常30-40%），无关的跳过。用户原话："将来于无关紧要的东西就不要管它"

- ⚠️ **多模型咨询（2026-05-15 用户确立）** — 涉及日报/周报框架、归因方案等结构性设计时，不能只问一个模型。任何单一模型都有幻觉/讨好倾向。至少咨询2个不同模型（如DeepSeek V4 Pro + Qwen-max + Hermes-3），提炼共识后落地。

- ⚠️ **🚨 digest 过时陷阱（2026-05-14 发现并修复·双层修复）** — **第一层：** 旧版digest只在发现新视频时重写，state更新后无新视频对比→digest变死文件。**第二层：** 旧state格式 `{"last_video_ids": [...]}` 只存ID不存标题描述，即使改用state重建digest，标题也是占位符。**修复：** state格式改为 `{"videos": [{"aweme_id","title","desc","create_time"}, ...]}`（`save_state()`传入整个filtered列表）；digest改为每次从state取每个博主最新5条重建（不管有无新视频）。**旧格式state需手动删除才能触发重建。**
- ⚠️ **2026-05-20 确认：CDP只用于cookie提取（约0.5秒，不打开抖音页面），监控/下载/转录全程无浏览器。** 详见「完整流程」章节的「Cookie获取」。
- ⚠️ **全量信任博主也会发无关内容** → 宋鸿兵偶尔发《论语》/文化/哲学类视频（如2026-05-14的「世界礼崩乐坏，我们更应该读懂《论语》」），岩松笔记部分视频偏纯方法论与持仓无关。下载前仍需要快速扫标题，不要因为「信任」就不看。<｜end▁of▁thinking｜>
- ⚠️ **此机器有间歇性 DNS 解析失败问题** (`Temporary failure in name resolution`)。BIJIAN ASR 需解析 `member.bilibili.com`，抖音 API 需解析 `www.douyin.com`，DeepSeek 需解析 `api.deepseek.com`。若某步骤失败，重试一次通常可恢复。这是系统性问题（7.1G 内存的旧机器 + 境内网络），不是目标服务的问题。
- ⚠️ **🚨 skill文件过大导致cron超时（2026-05-22 发现+修复）** — daily-briefing SKILL.md 约77KB，当cron job加载完整skill时，AI光读指令就需要1000+行，之后实际执行还没开始就超时断连。**这导致每日13:00的cron连续8天失败，没有转录任何视频。** 修复方案：创建一个精简版skill（`daily-cron-exec`），只含执行步骤和核心铁律，不包含全部文档和参考。cron job只加载精简版。详见 skill:daily-cron-exec。

- ⚠️ **🚨 强模型兜底铁律（2026-05-19 用户强要求）** — 碰到搞不定的事（B站API限流/cookie加密/未知调试），**不要硬死磕烧token**。3次工具调用没结果 → 立刻 `delegate_task` 派更强模型（Claude Sonnet / GPT-4等）。同一问题禁止尝试超过5次工具调用。
- ⚠️ **🚨 事件链写入 events/ 必须在写入 positions/ 之前（2026-05-19 修正）** — 一条新信息来了，先判断影响哪些持仓→写入 events/{日期}.md（一个事件只写一次，列全所有受影响持仓）→ 再按 events/ 的贝叶斯建议更新 positions/*.md。原因：同一个事件写在多个持仓文件里会不一致，events/ 是唯一来源。
- ⚠️ **报告必须是整合版** → 小龙虾出的报告必须同时包含持仓数据+视频新闻，不能分开两份发。大好人要看到的是完整画面。
> ⚠️ **抖音用户主页URL会触发CAPTCHA** → 不要用浏览器/CDP访问用户主页，改用API `/aweme/v1/web/aweme/post/?sec_user_id=ID` 直接调接口
- ⚠️ **宋鸿兵账号曾误配到但斌** → 真实账号是「宋鸿兵观天下」，sec_uid 为 `MS4wLjABAAAAzaye_V0qtP4d7m77UywUBRq7xB9CRiLaeGPfg79hLtQ`。`抖音主页.txt` 中已修正，脚本中硬编码的值是正确的。
- ⚠️ **yt-dlp 提取cookie经常失败** → `Failed to parse JSON` 是常见错误，不影响已有cookie使用。脚本已内置回退逻辑：yt-dlp失败 → 直接用已有 `/tmp/douyin_cookies.txt`。
- ⚠️ **Cookie文件有时效性** → 约3-7天过期。过期时API返回412。手动执行 `yt-dlp --cookies-from-browser chrome --cookies /tmp/douyin_cookies.txt --skip-download "https://www.douyin.com/video/1"` 即可刷新。
- ⚠️ **下载视频时不要传Cookie** → CDN返回 400 Bad Request (Request Header Or Cookie Too Large)。用curl + 仅Referer头。
- ⚠️ **视频URL有时效性** → API返回的play_addr几分钟后失效。拿到后立即curl下载，不能有任何延迟。
- ⚠️ **旧视频URL已过期** → 几天前的视频play_addr返回400，正常现象。每天13:00跑当天新视频即可。
- ⚠️ **首次运行所有视频标记为"新"** → 之后只检测增量。状态文件在 `~/.hermes/douyin_state/{博主名}.json`。
- ⚠️ **抖音API返回列表置顶在前** → 脚本已做 `sort(key=create_time, reverse=True)`，确保最新视频排前面。
- ⚠️ **🚨 永久假阳性缺陷：save_state 只存 top 20，但新视频检测对比的是完整 state** → `save_state()` 写 `filtered[:20]`（共 29 条），导致最老的 9 条视频永远不被收录进 state，每次运行都重复标记为"新"。对于更新频率低的博主（如宋鸿兵），这些老视频会无限循环出现。**修复方向：** 方案 A — 扩大 `save_state` 的切片上限到 `filtered[:30]` 或 `filtered[:len(filtered)]`；方案 B — 修改新视频检测逻辑，用 create_time 时间戳做阈值而非 ID 集合比对（只取最近 30 天内的"新"）。
- ⚠️ **脚本输出不包含视频 URL** → `douyin-monitor.py` 只打印标题/描述/时间，不打印 `aweme_id` 或拼接后的 `douyin.com/video/{id}` 链接。如需在报告中提供可直接点开的视频链接，需手动从 `~/.hermes/douyin_state/{博主名}.json` 中提取对应 `aweme_id` 拼接。URL 格式：`https://www.douyin.com/video/{aweme_id}`。
- ⚠️ **抖音API JSON响应超过1MB时，terminal()工具stdout仅返回50KB导致JSON解析失败** → 不要用 `urllib` 直接 `json.loads(resp.read())` 通过 terminal 返回。应改为：`curl -s -o /tmp/api_file.json` 保存到文件，再用 `execute_code` 或 Python脚本直接从磁盘读取文件解析。当文件1.5MB时，stdout截断后只返回前50KB，控制字符清洗也救不回来。2026-05-20实测：4个API文件各1.0~1.7MB，通过terminal传递全部失败，改文件读取后全部成功。
- ⚠️ **全量信任博主也会发营销/课程推广视频** → 如蒋宇飞商业的部分视频（如"产业思维科技龙头"100秒视频仅509字转录，内容纯课程推广无数据），下载后分析价值极低。处理规则：如果转录文本<800字（约3分钟视频的正常信息量），且内容为课程推销/成功学话术，可直接跳过LLM分析步骤，不写入events/文件夹。节省token和处理时间。
- Playwright 必须用系统 Python 3.13（`/usr/bin/python3`），不是 Hermes venv
- VideoCaptioner 处理视频可能需要 5-15 分钟，定时任务要预留足够时间
- `openclaw agent --message --deliver --json` 在通道未配置时失败（报 "Channel is required"），推送持仓信息给小龙虾时需要去掉 `--deliver`
- `openclaw agent` 耗时可能超过30秒（需要等agent思考+生成），要设足够长的 timeout（建议≥90秒）
- 用户偏好：分析结果直接在聊天框回复，而不是保存到文件。除非用户明确要求保存到文件

## 📡 信息聚合：财联社 + RSS（2026-05-16 建立 — 按需使用，不设cron）

> **核心原则（2026-05-16 用户反复强调）：** 不做推送，不做定时任务，不做后台服务。工具留着，**用户问了才跑**。用户要看他自己会问，不要替他决定他什么时候要看。
>
> **用户原话：** "我不要每天早上8点看，我要我自己想看的时候就能在聚合信息平台上面看到信息"
>
> **工具必须融合到工作流里（2026-05-16 用户纠正）：** 不是搞一堆独立脚本放着吃灰。要能在用户问"今天芯片怎么跌了"或"今天有什么新闻"时，我直接用这些工具查数据然后回答他。

### 可用工具

| 文件 | 用途 | 调用方式 |
|:----|:-----|:---------|
| `~/.hermes/scripts/cailianshe_scraper.py` | Playwright爬虫抓财联社电报→提取文章→过滤投资关键词 | `python3 ~/.hermes/scripts/cailianshe_scraper.py` |
| `~/.hermes/scripts/rss_aggregator.py` | **Python RSS Web服务**（运行在localhost:8080，替代Miniflux）。feedparser → SQLite → web UI + JSON API。自动轮询 | `系统服务：python3 ~/.hermes/scripts/rss_aggregator.py`（已设为常驻进程） |
| `~/.hermes/scripts/cls_push.py` | 增量推送（仅推送未见过的文章，非新文章不输出） | 单独跑输出Markdown |
| `~/.hermes/scripts/cls_web.py` | **已停用** — 用户不允许开网页服务白烧token |

### 使用场景

当用户问以下问题时按需运行：
- "今天有什么新闻" → 跑 `cailianshe_scraper.py` 或 `rss_aggregator.py browse`
- "芯片怎么跌了/涨了" → 跑财联社查当天有没有相关触发事件，再跑 `rss_aggregator.py browse 芯片` 看RSS源
- "区块链出了什么事" → `rss_aggregator.py browse 全部 关键词`

### RSS聚合器用法

**Web UI（推荐）：** 浏览器打开 `http://localhost:8080`
- `/` 浏览文章
- `/feeds` 管理订阅源（添加/删除）
- `/search?q=关键词` 搜索文章
- `/refresh` 手动刷新所有源

**API：**
```bash
curl -s http://localhost:8080/api/stats     # 统计
curl -s http://localhost:8080/api/feeds     # 所有订阅源
curl -s http://localhost:8080/api/entries   # 最新文章
```

**手动添加源：**
```bash
curl -s "http://localhost:8080/add?url=FEED_URL&category=分类"
```

### 技术要点

| 要点 | 说明 |
|:----|:-----|
| 数据库 | SQLite，位置 `~/.miniflux/rss_aggregator.db` |
| 依赖 | 只需 `feedparser` (pip3 install) |
| 财联社 | curl返回418（anti-bot），必须用Playwright完整浏览器 |
| 运行时间 | 财联社约45秒（启动浏览器），RSS聚合约几秒 |
| VPN要求 | rsshub.app的源（财联社/华尔街见闻/第一财经等）被墙，需**机器上开VPN** |
| 直连可用 | 美联储RSS（`federalreserve.gov/feeds/press_monetary.xml`）无需VPN |

### 已知坑

- **不要设置cron自动跑** — 用户明确不要定时推送
- **不要开Web服务** — 用户说"别自作主张给我搭什么网页，给我白烧token"
- rsshub.app被墙，如机器无VPN则只能用到直连源（美联储等）
- Playwright首次安装需下载~175MB Chromium（国内可能超时），已装好不重装
- Miniflux apt版只支持PostgreSQL（需要sudo），官方GitHub版支持SQLite但下载慢

### RSS聚合服务现状（2026-05-16 更新）

**最终方案：** Miniflux 编译受阻（Go被墙+gcc依赖）→ Docker镜像pull被墙 → 改为纯Python web版，已稳定运行。

**现状：**
- ✅ Python RSS聚合服务运行在 `http://localhost:8080`
- ✅ 自动每15分钟轮询所有源
- ✅ 有web UI + JSON API
- ✅ 不需要任何系统级依赖（Python feedparser + sqlite3）

### 国内网络环境下的软件安装限制（2026-05-16 实测）

此机器（境内网络，无sudo）的安装约束：

| 目标 | 状态 | 原因 |
|:----|:----|:-----|
| Go (go.dev/dl) | ❌ 被墙 | TLS连接失败 |
| Go (USTC镜像) | ❌ 重定向到dl.google.com被墙 | 国内镜像也走Google CDN |
| Miniflux 2.3.0二进制 | ❌ 无SQLite支持 | 静态编译不含CGO，需要从源码编译 (-tags sqlite) |
| Miniflux Docker镜像 | ❌ Docker pull超时 | Docker Hub被墙 |
| Docker国内镜像(华为/阿里) | ❌ 需登录 | 企业级镜像服务 |
| apt install（sudo） | ❌ 需要交互式密码 | 无密码sudo权限 |
| snap install | ❌ 需要sudo | 权限不足 |
| pip install --user | ✅ 可用 | Python虚拟环境 |
| curl下载GitHub Release | ✅ 可用但慢 | ~35KB/s，适合小文件 |
| npm install | ✅ 可用 | 全局安装到~/.npm-global |

**核心结论：** 在这个环境里，能直接下载执行的东西用 `curl -L` 从GitHub下，需要编译/系统级安装的走不通。



## 旧的 财联社电报爬虫 章节（已废弃/合并到上方）

> **用户需求（2026-05-16 明确多次）：** 一个他能**自己浏览**的信息聚合平台，不依赖我推送或他问我答。他想看的时候打开就能看。  
> **现状（2026-05-16）：** 用户从其他AI找到了方案——**Miniflux via Docker**（自托管RSS阅读器，web UI，REST API可对接我）。Docker已装但pull超时（被墙），需机器开VPN才能拉镜像。脚本已就绪，等用户确认VPN/Docker方案后由我配置Miniflux+导入RSS源。  
> **我的职责：** 不主动推信息，不自动跑服务。用户确认方案后我来做一次性的配置落地。

### 已就绪的脚本（随时可用）

| 文件 | 用途 | 调用方式 |
|:----|:-----|:---------|
| `~/.hermes/scripts/cailianshe_scraper.py` | Python Playwright 爬虫，抓财联社电报页→提取文章→过滤投资关键词→输出Markdown | `python3 ~/.hermes/scripts/cailianshe_scraper.py` |
| `~/.hermes/scripts/daily_aggregator.py` | 聚合器：财联社 + 美联储RSS → 合并日报 | `python3 ~/.hermes/scripts/daily_aggregator.py` |
| `~/.hermes/scripts/cls_push.py` | 增量推送脚本：每2小时跑一次，只推送未见过的文章 | 待用户确认推送平台后启用 |
| `~/.hermes/scripts/cls_web.py` | 本地Web服务（端口8899）：打开浏览器即可浏览聚合内容 | `python3 ~/.hermes/scripts/cls_web.py` |

### 过滤规则

脚本内置投资关键词：
- 黄金/原油/天然气/芯片/半导体/AI/养殖/猪肉/猪价/港股/A股/美股/大盘/指数
- 美联储/央行/利率/加息/降息/中美/地缘/外汇/人民币/美元/汇率
- 政策/国务院/发改委/贸易/关税/数据要素/算力

### 技术要点

| 要点 | 说明 |
|:----|:-----|
| 财联社曲线 | curl返回418（anti-bot），必须用Playwright完整浏览器 |
| 运行时间 | 约45秒（启动浏览器+渲染JS+提取文本） |
| 缓存 | Chromium缓存在 `~/.cache/ms-playwright/chromium-1217/`，已装好 |
| 美联储RSS | 标准ATOM，`urllib` 直接拉取 |
| 输出格式 | Markdown，按时间排序，投资相关过滤后单独标注 |

### 已知坑
- Playwright首次安装需下载~175MB Chromium，国内网络可能超时。已装好，不需重装
- 下载时不要传Cookie到CDN（返回400）
- 财联社URL有时效性，旧视频play_addr几分钟后失效
- 物价信息每天刷新，不用缓存旧数据
