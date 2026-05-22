# 知乎话题监控编排器

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`topic-monitor`（develop分类）

## 一句话

组合 cookie提取 + WAF绕过 + 知乎文章读取 三个积木，完成搜索→读帖→分析→长期跟踪全流程。

## 架构（三层积木）

```
通用积木层（不挑网站）
├── local-chrome-cdp-bridge — CDP提取cookie（Chrome v147+，本机唯一方案）
├── cookie-extractor        — 旧方案，Chrome < v147用
├── waf-bypass              — 手机UA绕WAF

平台层（网站专用）
└── zhihu-reader            — 读知乎帖子/回答

编排层（本技能）
└── topic-monitor           — 组合上面做搜索+读帖+分析+归档
```

## 工作流

### Phase 0: 加载积木

先加载：`local-chrome-cdp-bridge` → `waf-bypass` → `zhihu-reader`

本机Chrome v147+，CDP是唯一cookie提取方案。不要试yt-dlp。

### Phase 1: 搜索话题

```bash
curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" \
  -H 'User-Agent: Mozilla/5.0 (iPhone ...) Safari/604.1' \
  'https://www.zhihu.com/api/v4/search_v3?q={关键词}&limit=10'
```

筛选：点赞>5 或 回答>3，时间近，标题命中核心关键词。

### Phase 2: 读帖

按 zhihu-reader 流程：
1. 确认cookie有效（`~/桌面/zhihu_com_cookie_最新.txt`）
2. 用手机UA绕过封禁
3. 优先用API读（answers API最稳定），读全文加 `?include=content`

### Phase 3: 分析

三维分析框架：
- **叙事一致性** — 回答之间观点是否打架？
- **逻辑链检验** — 论据硬不硬？（数据/案例/推理）
- **反常检测** — 跟主流相反的异见？新角度？

### Phase 4: 归档

分析结果写入 `external_memory/thinkers/{thinker-name}.md`

同时写入L2记忆（hindsight_retain）方便跨会话检索。

## 铁律

1. 编排器不含任何平台实现代码，只编排下层技能
2. 关键流程存两份：技能 + 外部记忆
3. 每次任务第1步：加载已有技能，别从零造轮子
4. 新信息按 宏观→中观→微观 三层分层写入框架，不对位不存

## 涉及文件

- 博主数据源：`thinkers/INDEX.md`（唯一主数据源）
- 宏观框架：`00-宏观传导框架.md`
- 持仓文档：`positions/*.md`
- 贝叶斯日志：`23-贝叶斯更新日志.md`
- 事件链：`events/*.md`
