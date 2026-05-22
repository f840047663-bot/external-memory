# 知乎文章/回答抓取器

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`zhihu-reader`（develop分类）

## 一句话

从知乎抓取完整帖子/回答内容。依赖CDP提取的cookie + 知乎API。

## 前置条件

- 知乎cookie已提取：`~/桌面/zhihu_com_cookie_最新.txt`
- 验证cookie有效：`curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" "https://www.zhihu.com/api/v4/me"`

## 核心API端点

| 用途 | 端点 |
|------|------|
| 搜索用户 | `https://www.zhihu.com/api/v4/search_v3?q={用户名}&limit=5` |
| 获取用户信息 | `https://www.zhihu.com/api/v4/members/{url_token}?include=name,headline,description` |
| 读用户文章列表 | `https://www.zhihu.com/api/v4/members/{url_token}/articles?limit=20&offset=0` |
| 读用户回答列表 | `https://www.zhihu.com/api/v4/members/{url_token}/answers?limit=20&offset=0&order=created` |
| 读单个回答 | `https://www.zhihu.com/api/v4/answers/{answer_id}?include=content` |
| 读专栏文章 | `https://zhuanlan.zhihu.com/p/{article_id}` |

## URL解析

```
https://www.zhihu.com/question/2036008867021186957    → question_id
https://www.zhihu.com/people/lrc-8/posts?page=1        → url_token = lrc-8
https://www.zhihu.com/api/v4/answers/2039402143422083320?include=content  → answer_id
```

## 抓取流程（优先级排序）

### 方式1：读用户文章列表（推荐）

```bash
# url_token 从搜索用户得到
curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15' \
  -H 'Accept: application/json' \
  'https://www.zhihu.com/api/v4/members/lrc-8/articles?limit=20&offset=0'
```

返回 `data[*].title, .url, .excerpt, .content`。`?include=content` 可带全文。

### 方式2：读用户回答列表

```bash
curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" \
  -H 'User-Agent: Mozilla/5.0 (iPhone ...) Safari/604.1' \
  -H 'Accept: application/json' \
  'https://www.zhihu.com/api/v4/members/lrc-8/answers?limit=20&offset=0&order=created'
```

返回 `data[*].question.title, .content, .voteup_count, .created_time`。

### 方式3：读单个回答全文

```bash
curl -s --cookie "$(cat ~/桌面/zhihu_com_cookie_最新.txt)" \
  -H 'User-Agent: Mozilla/5.0 (iPhone ...) Safari/604.1' \
  'https://www.zhihu.com/api/v4/answers/{ANSWER_ID}?include=content'
```

### 方式4：通过CDP浏览器读（兜底）

当知乎API返回有限内容时，直接用Chrome CDP打开链接：

```bash
# 提取完整页面文本
python3 ~/.hermes/scripts/cdp-get-page-text.py --url "https://zhuanlan.zhihu.com/p/{article_id}"
```

## 内容清洗（Python）

```python
import re
content = re.sub(r'<[^>]+>', '', raw_content)
text = content.replace('\n\n\n', '\n\n').strip()
```

## 排障清单

| 症状 | 原因 | 解法 |
|------|------|------|
| 4041 "荒原" | 帖子不存在/已删除 | 让用户确认链接 |
| 40362 WAF拦截 | IP被封 | 用手机UA + x-requested-with header |
| 空响应 | WAF静默拦截 | 确认用了手机UA和cookie |
| 无content只有metadata | 缺 `?include=content` | 加include参数 |
| AuthenticationInvalidRequest | cookie过期/z_c0缺失 | 重新跑CDP提取cookie |
| curl报"bad range" | `[*]`被shell展开 | URL用单引号包裹 |

## 依赖链

```
local-chrome-cdp-bridge（Chrome v147+唯一取cookie方式）
  ↓
zhihu-reader（本技能，调知乎API）
  ↓
topic-monitor（编排器，组合搜索+读取+分析+归档）
```
