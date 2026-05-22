---
name: web-research-china
description: "Search the web from Chinese network environments — search engine availability (SogovsGooglevsBing), anti-spider workarounds, fallback strategies, and reliable Chinese data sources (Douban, Baidu Baike, Zhihu)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, china, network, search, web-scraping]
    related_skills: [docker-deployment-china, social-media-monitor]
---

# Web Research from China

## Overview

Searching the web from a China-based network (cron environment, IP ~117.x.x.x) is fundamentally different from a standard global network. Many international search engines and APIs are blocked, slow, or CAPTCHA-protected. This skill documents which search engines work, which don't, the workarounds for anti-spider protections, and the reliable Chinese data sources.

**Key insight from this session (2026-05-16):** When every search engine fails, the fallback that actually works is `curl` to Sogou (搜狗) with proper User-Agent headers + parsing HTML snippets (`h3` elements, `str-text` divs) from the raw response.

## When to Use

- You need to search the web from a China-based cron job or terminal session
- Google, Wikipedia, DuckDuckGo, or Bing International are timing out or returning empty
- Browser navigation (CDP/Chrome) is timing out
- You need to research a Chinese-language topic or a product's availability in China
- You need to query Chinese platforms (Douban, Baidu Baike, Zhihu)

## Search Engine Availability (from China, as of 2026-05)

| Engine | Availability | Speed | Anti-Spider Risk | Best For |
|--------|:-----------:|:-----:|:----------------:|:--------:|
| **Sogou (搜狗)** `sogou.com` | ✅ Works via curl | Medium | Medium (throttled after ~5 queries) | Primary fallback |
| **Bing China** `cn.bing.com` | ✅ Works via browser | Fast | CAPTCHA (Cloudflare) | Single queries via browser |
| **Baidu (百度)** `baidu.com` | ✅ Works | Fast | Low | Standard Chinese web search |
| **Douban (豆瓣)** `douban.com` | ✅ Works | Fast | Low | Movies, books, music |
| **Baidu Baike (百度百科)** | ✅ Works | Fast | Low | Encyclopedia/reference |
| **Zhihu (知乎)** `zhihu.com` | ⚠️ Works with iPhone UA via curl | Medium | WAF blocks desktop UA + all headless browsers | Use `cookie-extractor` + `waf-bypass` skills |
| **Bing International** `bing.com` | ⚠️ Partial | Slow | CAPTCHA | Only for international queries |
| **Google** `google.com` | ❌ Blocked/Timed out | N/A | N/A | Do not attempt |
| **Wikipedia (English)** | ❌ Blocked/Timed out | N/A | N/A | Do not attempt directly |
| **DuckDuckGo** `lite.duckduckgo.com` | ❌ Timed out | N/A | N/A | Do not attempt |
| **TMDB API** | ❌ Timed out | N/A | N/A | Do not attempt |
| **Whats-on-Netflix** | ❌ Empty results | N/A | N/A | Returns only navigation, no actual content |

## Effective Search Techniques

### 1. Sogou via curl (Primary Fallback)

The most reliable programmatic search method:

```bash
curl -sL "https://www.sogou.com/web?query=<URL-ENCODED-QUERY>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --max-time 15
```

**Anti-spider behavior:** After ~3-5 queries, Sogou redirects to `antispider` page. Mitigations:
- Rotate User-Agent strings
- Add small delays between requests
- Accept that you'll eventually get blocked — extract as much as possible from early queries
- Use a `&page=1` or refine query to be more specific per request

**Extracting results from HTML:**

```python
import sys, re, html
content = sys.stdin.read()

# Extract h3 elements (result titles)
results = re.findall(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL)
for r in results:
    text = re.sub(r'<[^>]+>', '', r)
    text = html.unescape(text.strip())
    if text:
        print(f'Result: {text}')

# Extract snippets (str-text class divs)
snips = re.findall(r'<p[^>]*class=\"[^\"]*str[^\"]*\"[^>]*>(.*?)</p>', content, re.DOTALL)
for s in snips:
    text = re.sub(r'<[^>]+>', '', s)
    text = html.unescape(text.strip())
    if len(text) > 15:
        print(f'Snippet: {text}')

# Extract result links
links = re.findall(r'href=\"(https?://[^\"]+)\"[^>]*>', content)
for l in links[:10]:
    if 'sogou' not in l and len(l) > 20:
        print(f'Link: {html.unescape(l)}')
```

### 2. Baidu via curl

Baidu is more permissive but serves dynamic content. For title extraction:

```bash
curl -sL "https://www.baidu.com/s?wd=<URL-ENCODED-QUERY>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --max-time 15
```

Try to extract `h3` elements similarly. Note: Baidu also serves some content via JS rendering, so `curl` may not capture everything.

### 3. Douban Search (Movies/Books)

Direct search endpoint — works well for Chinese media:

```bash
curl -sL "https://search.douban.com/movie/subject_search?search_text=<URL-ENCODED-TITLE>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  --max-time 15
```

The `<title>` tag will confirm if results exist (e.g. "气体人 - 电影 - 豆瓣搜索").

### 4. Baidu Baike (Reference)

```bash
curl -sL "https://baike.baidu.com/item/<URL-ENCODED-TERM>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  --max-time 15
```

### 5. Browser (CDP/Chrome) — Use with Caution

The browser tool is **unreliable** from China networks:
- Google navigation consistently times out (`CDP command timed out: Page.navigate`)
- Bing China works but may trigger CAPTCHA
- Sogou redirects to anti-spider page
- **Bilibili (B站) is heavily rate-limited** — API returns -799 ("请求过于频繁"), browser navigation also times out after 60s. Even with 15s+ delays between requests, the IP gets blocked. Direct curl to B站 space/search API returns empty after 2-3 queries. Workaround: search via Sogou (v.sogou.com) to find B站 video titles, then ask user for direct link.
- **Bilibili CDN/WAF** — The machine's IP (境内, ~117.x.x.x) appears to be flagged by Bilibili's CDN. Any programmatic access is blocked after a few requests, making automated B站 monitoring infeasible without a proxy/CDP session with real user login.

**When browser IS useful:**
- Loading search results that have already been obtained (following links)
- Loading Chinese sites that render JS content
- Navigating Bing International version (click "国际版" button)

## What to Do When Everything Fails

### Progressive Fallback Strategy

```
Level 1: curl to Sogou → extract h3 titles + str-text snippets
  ↓ (if blocked by anti-spider)
Level 2: curl to Baidu → extract h3 titles
  ↓ (if empty)
Level 3: curl to specific site (Douban/Baike/Zhihu) directly
  ↓ (if all curl fails)
Level 4: Browser navigation to Bing China → click "国际版" → search
  ↓ (if CAPTCHA blocks)
Level 5: Accept limited results. Report what you found with caveats.
```

### Key Signals That a Search Engine is Blocked

| Signal | Meaning |
|--------|---------|
| Empty response from curl | Connection refused or DNS blocked (Google, Wikipedia) |
| Anti-spider page / redirect | Bot detected (Sogou after 3-5 queries) |
| "请解决以下难题以继续" / Cloudflare checkbox | CAPTCHA (Bing) |
| CDP command timed out | Browser navigation blocked (Google) |
| `<title>` tag shows "N/A" or search engine homepage | No results parsed |
| Only navigation elements in snapshot (search bar, login, footer) | Results loaded but JS-rendered and not captured |

## Pitfalls

1. **Don't waste time on Google.** It will always time out from this network. Go straight to Sogou/Baidu/Bing China.
2. **Wikipedia is not accessible.** Use Baidu Baike for Chinese reference or try Wikipedia API (may also be blocked).
3. **Sogou has a low query limit.** Make your queries count — refine keywords before running. After anti-spider kicks in, you can try rotating User-Agent or using a different search engine.
4. **Bing China requires CAPTCHA for programmatic access.** Allow extra time for manual CAPTCHA or use the "国际版" toggle.
5. **Empty HTML from search results doesn't mean "no results".** It may mean the page renders via JavaScript. Check `<title>` tag for confirmation of page type.
6. **Search result URLs (href) from Sogou are sometimes relative or obfuscated.** Look for `https?://` patterns to find actual result links.
7. **Don't try to load full article pages from search results.** Many sites (3DM, Gcores, 1905) return "page not found" or login walls when accessed without proper session/cookies.
### 🚨 财联社搜索关键词盲区（2026-05-20 踩坑教训）

**错误做法（本会话踩坑）：** 搜芯片ETF新闻时，只搜了关键词"芯片ETF"——漏掉了黄仁勋随特朗普访华、苏姿丰表态、GTC Taipei预告等重大宏观事件。这些事件对芯片ETF影响比普通行业新闻大得多。

**正确做法：搜索关键词必须覆盖三层：**

```
第1层：基金/资产名称（"芯片ETF"）
第2层：宏观政治事件（"黄仁勋访华" "特朗普访华" "苏姿丰" "GTC"）
第3层：产业链上下游（"存储芯片" "HBM" "MLCC" "英伟达中国"）
```

**实操规则：**
1. 先用基金名搜（"芯片ETF"）→ 快速浏览近2天结果
2. 再用行业/宏观关键词搜（"英伟达中国" "半导体政策"）→ 搜遗漏的大事件
3. 对比两轮结果看有没有漏掉的大事
4. 如果有明显的大事件没出现在基金名搜索中 → 说明关键词不够宽

**检查清单：** 每次建事件链后自问"我搜索的关键词会不会漏掉宏观政治事件？"

### 6. 财联社电报搜索（持仓新闻的第一选择，不是备选）

**2026-05-20 用户纠正：** 之前我优先用百度/搜狗/Bing搜持仓新闻，全部失败或返回无关结果。用户指出财联社搜索才是正确的入口——精确到分钟的时间戳、无CAPTCHA、内容直接可读。

**从此以后，搜持仓新闻的第一选择是财联社搜索，不是百度/搜狗/Bing。**

```bash
browser_navigate(url="https://www.cls.cn/searchPage?type=telegram&keyword=<URL-ENCODED-KEYWORD>")
```

**为什么财联社比搜狗/百度好用（2026-05-20 实测确认）：**

2026-05-20 实测：财联社的搜索页面对浏览器友好（非headless、无CAPTCHA），内容最全。

```bash
# 浏览器导航到搜索页
browser_navigate(url="https://www.cls.cn/searchPage?type=telegram&keyword=电池ETF")

# 结果页面直接加载，有时间戳（精确到分钟）
# 每条结果包含：日期时间 + 标题 + 内容摘要
# 可翻页：&page=2, &page=3 ...
```

**为什么财联社比搜狗/百度好用：**
- 每条新闻都有精确到分钟的时间戳 → 可以按序排列
- 内容直接可见（不依赖JS渲染） → snapshot可读
- 搜索结果量极大（"共查询到5203篇相关电报"）
- 无CAPTCHA（浏览器环境）
- 可按关键词精确搜索（电池/锂电池/新能源等）

**适用于：** 为特定持仓搜索近期事件链（如电池ETF、芯片ETF等）

### ⚠️ 财联社翻页限制（2026-05-20 实战踩坑）

**实测发现：** 财联社搜索的 `&page=2/3/4` 参数**不翻到真正更早的内容**。page=1,2,3,4显示的结果完全相同（都是最近2-3天的新闻）。搜索"电池""锂电池""电池ETF"等关键词，最多回溯到约05-13（约7天前），无法通过翻页获取05-13之前的历史新闻。

**这意味着：** 财联社搜索只适合获取**最近1-2周**的新闻。如果需要更早的事件链（比如电池从04-17开始上涨的起点），必须用搜狗/百度补充搜索历史新闻。

**改进后的搜索策略：**
| 时间范围 | 工具 | 可靠性 |
|:--------|:-----|:------|
| 最近1周 | 财联社电报搜索 | ✅ 最佳，精确到分钟 |
| 1-4周前 | 搜狗curl（多层关键词）+ 东方财富 | ⚠️ 有限，但能覆盖大事件 |
| >1个月 | 搜狗+百度，关键词要宽 | ⚠️ 需要多轮尝试 |

**财联社 vs 其他方法的对比：**

| 方法 | 可靠性 | 时序精度 | 内容深度 | 推荐度 |
|:----|:------|:--------|:--------|:------|
| 财联社搜索 | ⭐⭐⭐⭐⭐ | 精确到分钟 | 电报摘要 | ✅ 首选 |
| 东方财富 | ⭐⭐⭐⭐ | 精确到天 | 完整新闻/研报 | ✅ 备用 |
| 百度/Sogou | ⭐⭐ | 精确到天 | 摘要有限 | ⚠️ 编码问题 |
| Bing中国 | ⭐⭐⭐ | 精确到天 | 摘要有限 | ⚠️ 需国际版 |

12. **财联社搜索是最可靠的财经新闻来源** — 当需要为特定持仓构建事件链时，第一选择是财联社电报搜索（browser + searchPage），不是百度/Sogou。财联社每页约20条，可翻页获取更早数据。已有成功案例：电池ETF 018926从05-13到05-20的完整事件链均来自财联社。|
12. **Zhihu WAF is impenetrable from this IP.** All methods fail: API (v4 public + authenticated), browser, curl, web.archive, google cache. Even if the user confirms an API approach "works personally", it may be blocked from this server. Accept this limitation and request user to copy-paste content directly.
13. **RSS via blogwatcher-cli:** `blogwatcher` was installed from crates.io via `cargo install blogwatcher`. Binary at `~/.cargo/bin/blogwatcher`. Installation took ~15 minutes on low-RAM machine. Not yet configured with feeds — see the `blogwatcher` package docs for feed subscriptions. For Chinese RSS, use `blogwatcher subscribe <feed_url>`.

## RSS Aggregation from China

### rsshub.app is BLOCKED

All feeds proxied through `rsshub.app` (e.g., `https://rsshub.app/cls.cn/telegraph`, `https://rsshub.app/wallstreetcn/news`) are unreachable from this machine — DNS resolves but TCP connection times out. Do not rely on rsshub.app for any scheduled/automated feeds.

**Working alternatives:**
- **Direct RSS feeds** (e.g., 美联储 `federalreserve.gov/feeds/press_monetary.xml`) — ✅ work via `feedparser` + `urllib`
- **Python `feedparser` library** — install via `pip3 install feedparser`, handles RSS 2.0 / Atom
- **Miniflux via Docker** — Docker pull from `miniflux/miniflux:latest` times out from China even with VPN on phone; needs Docker proxy/VPN configured on **host machine**
- **Native Go binary** — GitHub releases have SQLite support only when compiled with `-tags sqlite`. Pre-built `miniflux-linux-amd64` binary from releases page does NOT include SQLite support (statically linked, CGO disabled). `go build -tags sqlite` needs Go + gcc + libsqlite3-dev. Download from `go.dev` fails from China (TLS `unexpected eof`). Mirrors (USTC, Aliyun) also fail — they redirect to `dl.google.com` which is blocked. **Without root `sudo` to install Go via apt, or a functional system-wide VPN, compiling Miniflux with SQLite is impractical.**

### Python RSS Aggregator (Reliable Fallback)

When Miniflux compilation is blocked by network/sudo constraints, a Python-based aggregator using built-in modules works reliably:

```
Schema: feeds (id, title, url, category) + entries (id, feed_id, guid, title, url, content, published, read)
Stack:  sqlite3 (built-in) + feedparser (pip3) + http.server (built-in)
Port:   8080
Poll:   Background thread every 900s via daemon thread
```

**Capabilities:**
- Web UI at `http://localhost:8080/` (article browsing, feed management, search)
- JSON API at `/api/feeds`, `/api/entries`, `/api/stats`
- `feedparser` installed, socket default timeout 30s
- Add feed: `curl http://localhost:8080/add?url=<RSS_URL>`
- Refresh all: `curl http://localhost:8080/refresh`

**Chinese feeds confirmed working (2026-05):**
| Feed | URL | Status |
|------|-----|--------|
| 人民网-时政 | `http://www.people.com.cn/rss/politics.xml` | ✅ 100+ entries |
| 网易 | `http://www.163.com/rss/` | ✅ 200 status (0 entries — no-op format) |

**Accessible Chinese sites for scraping:** Baidu, Sina, 163.com work. Google, GitHub (direct), Reddit, most international news RSS (BBC, NYT, FT, Reuters) and Wikipedia all time out from this machine.

**To add more feeds:**
```bash
# Test first
python3 -c "
import socket, feedparser
socket.setdefaulttimeout(15)
f = feedparser.parse('URL')
print(len(f.entries), 'entries, status:', f.get('status'))
"
# Then add via API
curl 'http://localhost:8080/add?url=URL'
```

**Script location:** `~/.hermes/scripts/rss_aggregator.py`

### Docker from China

`docker pull` from Docker Hub consistently times out. Workarounds (none work without sudo or functional VPN):
- `registry-mirrors` in `/etc/docker/daemon.json` — needs sudo
- `HTTP_PROXY` env var — needs proxy configured on host
- User claims VPN can be turned on — but VPN may be on phone only, not Ubuntu machine

### Browser-Based Scraping with Playwright (Anti-Bot Workaround)

Some Chinese financial/news sites (e.g., 财联社 `cls.cn/telegraph`) return HTTP 418 to plain `curl`. **Playwright** reliably bypasses this with full browser rendering:

```bash
pip3 install playwright
playwright install chromium   # ~175MB, may timeout from China; pre-cached at ~/.cache/ms-playwright/
```

**Pattern:**
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(user_agent="...").new_page()
    page.goto("https://site.com", wait_until="networkidle", timeout=30000)
    data = page.evaluate("() => document.querySelectorAll('...')...")
    browser.close()
```

**Performance:** ~30-45s per run. Python package v1.59.0 installed 2026-05-16.
**Example:** `~/.hermes/scripts/cailianshe_scraper.py` — scrapes 财联社 telegraph with investment keyword filter.

## Verification

- [ ] Did you try curl to Sogou first with proper User-Agent?
- [ ] Did you parse h3 elements + str-text divs from the HTML?
- [ ] If Sogou blocked, did you fall back to Baidu or a direct site query?
- [ ] Did you check `<title>` tag on search result pages to confirm the page is showing results?
- [ ] For media topics, did you try Douban (movies) or Baidu Baike (reference)?
- [ ] Did you note which search engines worked/didn't for reproducibility?
