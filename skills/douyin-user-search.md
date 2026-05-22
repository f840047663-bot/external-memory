---
name: douyin-user-search
title: 抖音用户搜索与sec_uid提取
description: 通过Chrome CDP在抖音搜索用户并提取sec_uid。适用于已知用户名但不知道sec_uid的场景。注意：成功率依赖当前反爬策略，有时会触发验证码。
trigger: 需要将抖音博主加入监控列表但不知道sec_uid时
---

# 抖音用户搜索与sec_uid提取

## 适用场景

需要将新博主加入 `douyin-monitor.py` 的监控列表，但只知道用户名（如"蒋宇飞商业"），`sec_uid`（如 `MS4wLjABAAAA...`）未知。

## 核心流程

### 方式A：用户分享链接（最稳）

```bash
# 用户从抖音APP分享主页链接，格式一般是：
# https://www.douyin.com/user/MS4wLjABAAAA...
# 直接从链接提取 sec_uid
echo "https://www.douyin.com/user/MS4wLjABAAAA..." | grep -oP 'user/\K[A-Za-z0-9_-]+'
```

### 方式B：CDP搜索（有时会触发验证码）

使用 `~/.hermes/scripts/douyin-search-user.sh`（已打包好）：

```bash
bash ~/.hermes/scripts/douyin-search-user.sh "用户名"
```

**原理：**
1. 连接Chrome CDP（端口9222）
2. 先访问抖音首页建立session
3. 导航到 `https://www.douyin.com/search/{encoded_name}?type=user`
4. 等待页面渲染后提取用户链接中的 sec_uid

**注意：** 抖音反爬策略经常变化。如果返回"验证码中间页"或只显示页脚，说明被拦截了。此时只能走方式A。

### 方式C：直接API查询（有时能用）

```bash
COOKIE=$(cat /tmp/dy_cookies.txt 2>/dev/null || cat ~/桌面/douyin_com_cookie_最新.txt)
curl -s "https://www.douyin.com/aweme/v1/web/discover/search/?keyword=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"用户名\"))')&type=1" \
  -H "Cookie: $COOKIE" -H "User-Agent: Mozilla/5.0" --connect-timeout 10
```

但抖音API经常改端点，此方式不稳定。

## 加监控步骤

拿到 sec_uid 后：

```bash
# 1. 编辑监控脚本
nano ~/.hermes/scripts/douyin-monitor.py
# 在 BLOGGERS 列表中添加：
# {"name": "用户名", "sec_uid": "MS4wLjABAAAA...", "trust": True},

# 2. 验证
python3 ~/.hermes/scripts/douyin-monitor.py --single "用户名"

# 3. 应该能看到视频列表输出
```

## 已收录的sec_uid格式

`MS4wLjABAAAA...` — 约40-60个字符的base64-like字符串

## 铁律

1. 方式B/C失败时不要反复重试 → 会触发更严格的风控
2. 方式A（用户分享链接）是最可靠的方法
3. 找到新博主后不仅加监控，还要建 thinker 档案
