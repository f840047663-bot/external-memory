---
name: zhihu-reader
description: 专用 — 读取知乎帖子/回答的完整内容。依赖 cookie-extractor（提cookie）和 waf-bypass（手机UA绕WAF）。本技能只含知乎API端点和解析方式
---

# Zhihu Reader

## 🧩 整体架构（三层积木）

```
通用积木层（不挑网站）
├── cookie-extractor           — 从Chrome偷cookie（Chrome < v147）
├── local-chrome-cdp-bridge    — ⭐ CDP提取cookie（Chrome v147+，本机唯一方案）
├── waf-bypass                 — 手机UA绕WAF

平台层（网站专用）
└── zhihu-reader               — 读知乎帖子

编排层
└── topic-monitor              — 组合上面做话题搜索+分析+归档
```

## ⚡ 本机特殊说明

**本机 Chrome 已升级到 v147+，CDP 是唯一可行的 cookie 提取方案。** 提取后cookie存于 `~/桌面/{domain}_cookie_最新.txt`。

```bash
# 每次需要知乎 cookie 时，直接执行（不要试 yt-dlp）
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --test

# 或直接用桌面上最新的 cookie 文件
curl -H "Cookie: $(cat ~/桌面/zhihu_com_cookie_最新.txt)" "https://www.zhihu.com/api/v4/me"
```

**铁律：** cookie 提取、WAF 绕过、内容读取，三个步骤拆成独立技能文件，互不依赖。任何一个换了不影响其他。关键流程同时存技能+外部记忆双份。

## ⚠️ 致命陷阱：忘记已有技能 = 灾难

**2026-05-18 教训：** 用户昨天（2026-05-17）已经建立了完整的 cookie-extractor / waf-bypass / zhihu-reader 三件套，存好了 `~/桌面/zhihu_cookie.txt`。我今天完全忘记了这些，从零开始试图破解 Chrome v147 加密，浪费了一整天。

**每次知乎相关任务，第1步检查：**
```bash
# 1. 已有的技能目录
cat ~/.hermes/external_memory/00-技能目录.md 2>/dev/null | head -30

# 2. 桌面已有的脚本和cookie
ls ~/桌面/*cookie* ~/桌面/*提取* ~/桌面/*Cookie* 2>/dev/null

# 3. Hermes技能目录
ls ~/.hermes/skills/devops/cookie-extractor/ ~/.hermes/skills/develop/zhihu-reader/ 2>/dev/null
```

## 知乎 API 端点

| 用途 | 端点 |
|------|------|
| 读问题下的回答 | `https://www.zhihu.com/api/v4/questions/{question_id}/answers` |
| 读问题 feeds（推荐） | `https://www.zhihu.com/api/v4/questions/{question_id}/feeds` |
| 读单个回答 | `https://www.zhihu.com/api/v4/answers/{answer_id}` |
| 读专栏文章 | `https://zhuanlan.zhihu.com/p/{article_id}` |
| 取当前用户 | `https://www.zhihu.com/api/v4/me` |
| 搜索 | `https://www.zhihu.com/api/v4/search_v3?q={关键词}` |

## 从 URL 提取 ID

```
https://www.zhihu.com/question/2036008867021186957
                               └─ question_id ─┘

https://www.zhihu.com/question/2016832855842522430/answer/2039402143422083320
                               └─ question_id ─┘         └─ answer_id ─┘
```

## 读取流程

**优先顺序：** 方式 B（单回答）> 方式 C（answers API）> 方式 A（feeds API，最不可靠）

### 方式 C（推荐）：读问题下所有回答 — answers API

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' \
  -H 'Accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest' \
  'https://www.zhihu.com/api/v4/questions/{QUESTION_ID}/answers?include=data[*].content,author.name,voteup_count,comment_count,created_time&limit=5&offset=0&order=default'
```

✅ 最稳定。已验证支持 offset 分页，返回 `paging.totals` 含总回答数。

### 方式 B（精确）：读单个回答

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' \
  -H 'Accept: application/json' \
  'https://www.zhihu.com/api/v4/answers/{ANSWER_ID}?include=content'
```
✅ 最精准。要求 `?include=content`，否则只返回 metadata。

### 方式 A（备用）：读问题 feeds

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' \
  -H 'Accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest' \
  'https://www.zhihu.com/api/v4/questions/{QUESTION_ID}/feeds?include=data[*].content,voteup_count,author.name,comment_count,created_time&limit=5&offset=0&order=default'
```
⚠️ 已知问题：某些 question_id 下 feeds API 返回空，但 answers API 正常。先用方式 A 如果失败立刻切方式 C。

## 内容提取（Python）

```python
import re, json
content = re.sub(r'<[^>]+>', '', raw_content)
text = content.replace('\n\n\n', '\n\n').strip()
```

## 排除清单

| 症状 | 原因 | 解法 |
|------|------|------|
| 4041 "荒原" | 帖子不存在/已删除 | 让用户确认链接 |
| 40362 WAF | IP被封 | 用 waf-bypass 的手机 UA |
| curl 报 "bad range" | `[*]` 被 shell 展开 | URL 用单引号包裹 |
| 空响应 | WAF 静默拦截 | 确认用了手机 UA 和 x-requested-with header |
| 返回只有 metadata 无 content | 缺 `?include=content` | 加 include 参数 |
| Curl 收到 `AuthenticationInvalidRequest`（code:100） | Chrome v147+ cookie 未提取到 z_c0 | 参见顶部依赖链，切到 local-chrome-cdp-bridge |
| cookie 文件有 zhihu 条目，但 curl API 返回未登录错误 | yt-dlp 提取了 44 个非登录 cookie，但 z_c0 在 185 个未解密的里面 | 不要被 "Extracted 44 cookies" 欺骗，直接切 CDP |

## 参考

- 完整端到端示例见今日会话日志
- `cookie-extractor` 技能：提 cookie
- `waf-bypass` 技能：绕 WAF
