---
name: blogwatcher
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool."
version: 2.0.0
author: JulienTant (fork of Hyaxia/blogwatcher)
license: MIT
platforms: [linux, macos, windows]
notes:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites: []
metadata:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring]
    homepage: https://github.com/JulienTant/blogwatcher-cli
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool (native binary, user reads for themselves)."
---

# Blogwatcher

Track blog and RSS/Atom feed updates with the `blogwatcher-cli` tool. Supports automatic feed discovery, HTML scraping fallback, OPML import, and read/unread article management.

## 🔍 Pre-flight check

**Always check if already installed before attempting installation:**

```bash
which blogwatcher-cli && blogwatcher-cli --version
```

If installed, skip installation entirely. This system already has it (7 feeds tracked as of 2026-05-18). Just add feeds directly.

To verify current state:
```bash
GODEBUG=netdns=go blogwatcher-cli blogs
GODEBUG=netdns=go blogwatcher-cli articles
```

## ⚡ Installation (this machine — native binary required, Docker OOMs)

> ⚠️ **Docker image (ghcr.io/julientant/blogwatcher-cli) crashes with `unable to open database file: out of memory (14)`** on this machine — Go SQLite inside the distroless container can't allocate memory. **Use native binary instead.**

### Step 1: Download binary (Chinese network — allow 3+ minutes)

```bash
# Linux amd64: ~6.7MB, download may take 3+ minutes from China
curl -L --max-time 300 -o /tmp/blogwatcher-cli.tar.gz \
  https://github.com/JulienTant/blogwatcher-cli/releases/download/v0.2.0/blogwatcher-cli_linux_amd64.tar.gz
cd /tmp && tar xzf blogwatcher-cli.tar.gz
mv blogwatcher-cli ~/.local/bin/blogwatcher-cli-native
chmod +x ~/.local/bin/blogwatcher-cli-native
```

### Step 2: Create wrapper with persistent DB path + DNS fix

> ⚠️ **DNS fix:** On Ubuntu with systemd-resolved (127.0.0.53), Go binaries get `server misbehaving` errors. Fix: add `GODEBUG=netdns=go` to force Go's built-in DNS resolver.

```bash
cat > ~/.local/bin/blogwatcher-cli << 'SCRIPT'
#!/bin/bash
export BLOGWATCHER_DB="$HOME/.blogwatcher-cli/blogwatcher-cli.db"
export GODEBUG=netdns=go
exec /home/fw/.local/bin/blogwatcher-cli-native "$@"
SCRIPT
chmod +x ~/.local/bin/blogwatcher-cli
```

### Step 3: Set up database directory and test

```bash
mkdir -p ~/.blogwatcher-cli
# Default DB dir may have wrong perms if previously used by Docker
sudo chown -R $USER:$USER ~/.blogwatcher-cli/ 2>/dev/null || true
blogwatcher-cli --version
# Expected: 0.2.0
```

### Step 4: Add feeds and test

```bash
blogwatcher-cli add "Feed Name" "https://example.com" --feed-url "https://example.com/feed.xml"
blogwatcher-cli blogs
blogwatcher-cli scan   # May timeout if feeds are dead
blogwatcher-cli articles  # List unread
```

### Alternative: Docker (use only for short-lived one-off scans)

If you only need a single scan without persistence, Docker still works:
```bash
docker run --rm ghcr.io/julientant/blogwatcher-cli scan --help
```

## Common Commands

### Managing blogs

- Add a blog: `blogwatcher-cli add "My Blog" https://example.com`
- Add with explicit feed: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- Add with HTML scraping: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- List tracked blogs: `blogwatcher-cli blogs`
- Remove a blog: `blogwatcher-cli remove "My Blog" --yes`
- Import from OPML: `blogwatcher-cli import subscriptions.opml`

### Scanning and reading

- Scan all blogs: `blogwatcher-cli scan`
- Scan one blog: `blogwatcher-cli scan "My Blog"`
- List unread articles: `blogwatcher-cli articles`
- List all articles: `blogwatcher-cli articles --all`
- Filter by blog: `blogwatcher-cli articles --blog "My Blog"`
- Filter by category: `blogwatcher-cli articles --category "Engineering"`
- Mark article read: `blogwatcher-cli read 1`
- Mark article unread: `blogwatcher-cli unread 1`
- Mark all read: `blogwatcher-cli read-all`
- Mark all read for a blog: `blogwatcher-cli read-all --blog "My Blog" --yes`

## Environment Variables

All flags can be set via environment variables with the `BLOGWATCHER_` prefix:

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Path to SQLite database file |
| `BLOGWATCHER_WORKERS` | Number of concurrent scan workers (default: 8) |
| `BLOGWATCHER_SILENT` | Only output "scan done" when scanning |
| `BLOGWATCHER_YES` | Skip confirmation prompts |
| `BLOGWATCHER_CATEGORY` | Default filter for articles by category |

## Example Output

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

---

## 🚀 进阶：RSSHub 集成 — 跟踪 B站/知乎/小红书 博主

本机已运行 RSSHub Docker 容器（端口 1200），可将社交平台用户主页转为 RSS Feed。

### 支持的转换格式

| 平台 | RSSHub 路由 | 示例 |
|:----|:-----------|:----|
| **B站用户视频** | `/bilibili/user/video/{uid}` | `http://127.0.0.1:1200/bilibili/user/video/2267573` |
| **知乎用户动态** | `/zhihu/people/activities/{user_id}` | `http://127.0.0.1:1200/zhihu/people/activities/chen-jun-89-17` |
| **小红书用户笔记** | `/xiaohongshu/user/{user_id}` | `http://127.0.0.1:1200/xiaohongshu/user/abc123` |
| **微博用户** | `/weibo/user/{uid}` | `http://127.0.0.1:1200/weibo/user/123456` |
| **今日头条用户** | `/toutiao/user/{uid}` | `http://127.0.0.1:1200/toutiao/user/123456` |
| ❌ 抖音 | 不支持 | RSSHub 无此路由 |

### 添加方法

**方法 A：手动加（单条）**
```bash
GODEBUG=netdns=go blogwatcher-cli add "B站-UP主名" "https://space.bilibili.com/UID" --feed-url "http://127.0.0.1:1200/bilibili/user/video/UID"
```

**方法 B：批量脚本（推荐）**
桌面上有两个文件，用户粘贴链接 → 双击运行即可。详见 `references/desktop-rss-setup.md`。

### ⚠️ RSSHub 注意
- RSSHub 爬取目标站速度较慢（B站 / 知乎可能需要 30s-3min 首条抓取）
- 添加 feed 本身是秒级的（blogwatcher 只存 URL，不验证）
- `scan` 时如果未超时，等待 RSSHub 返回即可获得新内容

## Pitfalls

- ⚠️ **Docker image OOMs on SQLite** — `create migration driver: unable to open database file: out of memory (14)` is a Go SQLite allocation failure in the distroless container. **Always use the native binary** on this machine.
- ⚠️ **BLOGWATCHER_DB must be explicitly set** — Without it, the binary may try to write to a defunct default path. Always use the wrapper script above which exports `BLOGWATCHER_DB`.
- ⚠️ **Binary download from GitHub is slow from China** — Allow 3-5 minutes for the 6.7MB tarball. Do not cancel early.
- ⚠️ **Most Chinese financial RSS feeds are dead** — Sina, WallStreetCN, 财联社, 新华社, 凤凰 all returned 404 or timeout. Only 36kr.com RSS is confirmed alive (tech news). RSSHub instances may work if accessible.
- ⚠️ **`scan` may timeout on dead feeds** — If a feed URL returns 404 or hangs, `blogwatcher-cli scan` will stall until timeout. Use `blogwatcher-cli scan "Single Feed Name"` to scan one at a time and identify dead ones.
- ⚠️ **Database directory permissions** — If Docker previously created `~/.blogwatcher-cli/` as root, `chown` it back to the user or delete and recreate the directory.
- ⚠️ **No `sudo` access on this machine** — Write all binaries to `~/.local/bin/`, not `/usr/local/bin/`.
- ⚠️ **Go binary × systemd-resolved DNS failure** — On Ubuntu with systemd-resolved (127.0.0.53), Go binaries may get `server misbehaving` DNS errors. Fix: prepend `GODEBUG=netdns=go` to force Go's built-in DNS resolver. Example: `GODEBUG=netdns=go blogwatcher-cli scan`. This bypasses systemd-resolved's stub resolver.

- Auto-discovers RSS/Atom feeds from blog homepages when no `--feed-url` is provided.
- Falls back to HTML scraping if RSS fails and `--scrape-selector` is configured.
- Categories from RSS/Atom feeds are stored and can be used to filter articles.
- Import blogs in bulk from OPML files exported by Feedly, Inoreader, NewsBlur, etc.
- Database stored at `~/.blogwatcher-cli/blogwatcher-cli.db` by default (override with `--db` or `BLOGWATCHER_DB`).
- Use `blogwatcher-cli <command> --help` to discover all flags and options.
