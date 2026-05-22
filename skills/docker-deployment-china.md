---
name: docker-deployment-china
description: Deploy and manage Docker containers from Chinese network environments — registry mirrors, ghcr.io fallback, sudo password handling, resource limits, and auto-restart.
---

# Docker Deployment in China

Deploying Docker containers from a Chinese network requires special handling — Docker Hub (`docker.io`) is frequently blocked or 429-rate-limited, and international bandwidth is slow.

## Registry Mirror Configuration

Commonly working mirrors (as of 2026-05):

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.sjtug.sjtu.edu.cn",
    "https://docker.1ms.run"
  ]
}
```

Apply changes:
```
sudo cp daemon.json /etc/docker/daemon.json
sudo systemctl daemon-reload && sudo systemctl restart docker
```

## Pulling Images — Priority Order

1. **GHCR (`ghcr.io`)** — most reliable from China when Docker Hub fails
2. **Alibaba Cloud** (`registry.cn-hangzhou.aliyuncs.com`) — if image is mirrored there
3. **Docker Hub via mirrors** — from daemon.json, but may 429

```
# Preferred first attempt:
docker pull ghcr.io/weifeng2333/videocaptioner:latest
```

## Sudo Password Pattern

This system requires password for sudo. Use:
```
echo '19931121./f' | sudo -S docker <command>
```

## Background Pull (Slow Network)

When ghcr.io is accessible but slow (>60s), pull in background:
```
echo 'password' | sudo -S docker pull ghcr.io/username/repo:tag &
```
Use `notify_on_complete=true` in terminal tool to get notified when done.

## Container Deployment with Resource Limits

Standard deployment template:
```
echo 'password' | sudo -S docker run -d \
  --name <name> \
  --restart unless-stopped \
  --cpus="1" \
  --memory="1g" \
  -p <host-port>:<container-port> \
  <image>
```

## Pitfalls

- **Registry mirrors 429**: Common — switch mirror or use ghcr.io
- **Sudo strips env vars**: `sudo` may not preserve `https_proxy`/`http_proxy`. Explicitly set or clear them
- **Health check delay**: Some containers take 15-30s to report healthy
- **Streamlit ports**: Typically runs on **8501** internally, not 8000 — check exposed ports in `docker inspect` and map both if needed
- **Timeouts from China**: ghcr.io pulls can take 300s+ — use background pull
- **Password auth fails**: `sudo -S` reads from stdin; `echo` pipes password, then `2>&1` to capture stderr
- **Port 8000 may not be HTTP**: Some containers expose port 8000 internally but it doesn't respond to HTTP (curl returns exit 56 — connection accepted but no data). This is normal — the service might use a different protocol or only respond via internal Streamlit backend. **Verify containers by port presence (`ss -tlnp | grep <port>`) not by curl**. The actual web UI is often on a different port (e.g., 8501 for Streamlit).
- **Stale proxy env vars block API access**: System may have `https_proxy`/`HTTPS_PROXY` env vars pointing to a dead proxy (e.g., `127.0.0.1:9674`). If the proxy service is down, `curl` to API endpoints (DeepSeek, etc.) will hang/timout. Fix: `export https_proxy="" http_proxy=""` before running curl, or use `--noproxy '*'`.

## Verification

```
sudo docker ps --filter name=<name> --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
sudo docker stats <name> --no-stream
sudo docker logs <name> --tail 20
```

## Restart Policy: `docker update` vs `--restart` at creation

Set at creation:
```bash
docker run -d --restart=always --name mycontainer image
```

Set on existing container:
```bash
docker update --restart=always mycontainer
```

**Pitfall:** `docker start` does NOT accept `--restart` flag. If you use `docker start` to restart an exited container after reboot, the restart policy is NOT reset — it persists from `docker create`/`docker run`. If the container has no restart policy, it won't survive the next reboot. Always use `docker update --restart=always` after `docker start`.

## Example: Miniflux Deployment (RSS Reader)

Miniflux requires PostgreSQL. Deploy as two linked containers:

```bash
# 1. PostgreSQL
docker run -d \
  --name miniflux-db \
  --restart=always \
  -e POSTGRES_USER=miniflux \
  -e POSTGRES_PASSWORD=miniflux \
  -e POSTGRES_DB=miniflux \
  postgres:16-alpine
```

### ✅ 推荐方案：自定义Docker网络

**⚠️ 警告：** 此方案适用于 Miniflux 自身的基础部署，但**如果不配合 host 网络模式，Miniflux fetcher 会拒绝从自定义网络获取 RSSHub 的 feed**（返回 `refusing to access private network host`）。所以如果你要同时跑 RSSHub，直接跳到上面的「推荐方案：host 网络模式」。

基本部署如下：

```bash
# 创建共享网络
docker network create rss-net

# PostgreSQL
docker run -d --name miniflux-db --network rss-net --restart always \
  -e POSTGRES_USER=miniflux -e POSTGRES_PASSWORD=miniflux -e POSTGRES_DB=miniflux \
  postgres:16-alpine

# Miniflux
docker run -d --name miniflux --network rss-net --restart always \
  -e RUN_MIGRATIONS=1 -e CREATE_ADMIN=1 \
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 \
  -e "DATABASE_URL=postgres://miniflux:miniflux@miniflux-db/miniflux?sslmode=disable" \
  -e LISTEN_ADDR=0.0.0.0:8080 \
  -p 8080:8080 \
  miniflux/miniflux:latest
```

**要点：**
- 用 `--network rss-net` 使两容器在同一网络，`miniflux-db` 可被DNS解析
- 数据库连接用服务名 `miniflux-db` 而非IP
- ❌ 不要依赖 `--link` — 在自定义网络中不需要
- ❌ 不要依赖 `POLLING_PRIVATE_NETWORK` — 2.3.0版不生效

### 验证
```bash
docker ps --filter name=miniflux --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -s http://localhost:8080 | head -5
```

### ⚠️ 网络迁移陷阱
容器创建后**不能**用 `--network` 参数，必须：
```bash
docker network connect rss-net miniflux-db  # 将已有容器连入网络
```

### ⚠️ Miniflux API feed_id vs full object

Miniflux的 `POST /v1/feeds` API 在添加成功时返回 `{"feed_id": N}`（不是完整的feed对象）。当curl超时时，不是加源失败，而是fetcher验证feed内容花的时间长（特别是RSSHub需要Chromium渲染的路线）。**增加 `--max-time 60` 即可**。

要获取完整的feed信息（含title/category/status），用 `GET /v1/feeds` 单独查询。

### ⚠️ 重置Miniflux管理员密码

如果Admin密码不对（或因重构容器导致密码与已有数据库用户不匹配），直接改DB：
```bash
# 删除已有admin用户，重启miniflux会通过CREATE_ADMIN=1重新创建
docker exec miniflux-db psql -U miniflux -c "DELETE FROM users WHERE username='admin';"
docker restart miniflux
```

### ⚠️ 数据库密码不匹配
重建Miniflux容器后最常见的错误：
```
pq: password authentication failed for user "miniflux"
```
原因：新建容器时设置的密码与已有数据库不匹配。**记住初始设置的密码**，或用同一个密码重建数据库容器（会丢失数据）。

### 强制关机后恢复
强制关机（power loss）后，Docker容器exit code 255。恢复步骤：
```bash
docker start miniflux-db
sleep 5  # 等PostgreSQL启动
docker start miniflux
sleep 5
docker update --restart=always miniflux miniflux-db
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
```

### Docker daemon僵死恢复
当 `docker ps` 超时但 `pgrep dockerd` 显示进程存活时：
```bash
kill -9 $(pgrep dockerd)
# 等2秒，然后用background terminal重启
sudo dockerd &
sleep 5
# 验证
docker ps
```

## RSSHub 部署 + Miniflux 配合

RSSHub 提供 B站/36氪/虎嗅等平台的RSS转换。与其配合 Miniflux 的关键模式如下。

### 🔴 关键坑：Miniflux fetcher 拒绝私网地址

Miniflux 2.3.0 的 fetcher 会**检查目标IP是否为私有地址**（127.x.x.x / 10.x.x.x / 172.16-31.x.x / 192.168.x.x），即使设置了 `POLLING_PRIVATE_NETWORK=1` 或 `POLLING_ALLOW_PRIVATE_NETWORKS=1` 也**不起作用**。

**正确的环境变量是 `FETCHER_ALLOW_PRIVATE_NETWORKS=1`**（注意前缀是 `FETCHER_` 不是 `POLLING_`）。

但即使设了这个变量，通过自定义Docker网络访问（如 `http://rsshub:1200/`）仍然失败。只有 **host 网络模式**才能让 fetcher 稳定工作。

### ✅ 推荐方案：host 网络模式

```bash
# 1. PostgreSQL
docker run -d --name miniflux-db --network host \
  -e POSTGRES_USER=miniflux -e POSTGRES_PASSWORD=miniflux -e POSTGRES_DB=miniflux \
  --restart unless-stopped \
  postgres:16-alpine
sleep 5

# 2. RSSHub（带 Chromium 用于 B站等需要浏览器渲染的源）
docker run -d --name rsshub --network host \
  -e NODE_ENV=production \
  --restart unless-stopped \
  diygod/rsshub:chromium-bundled
sleep 5

# 3. Miniflux
docker run -d --name miniflux --network host \
  -e DATABASE_URL=postgres://miniflux:miniflux@127.0.0.1:5432/miniflux?sslmode=disable \
  -e RUN_MIGRATIONS=1 -e CREATE_ADMIN=1 \
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=test123 \
  -e FETCHER_ALLOW_PRIVATE_NETWORKS=1 \
  -e POLLING_SCHEDULER=entry_frequency \
  -e BATCH_SIZE=20 \
  --restart unless-stopped \
  miniflux/miniflux:latest
```

**要点：**
- 三个容器都在 `--network host` 上，通过 `127.0.0.1` 互相访问
- Miniflux 通过 `http://localhost:1200/` 访问 RSSHub
- `FETCHER_ALLOW_PRIVATE_NETWORKS=1` 让 Miniflux 允许 fetch 本地地址
- PostgreSQL 用 `127.0.0.1:5432` 而非 `miniflux-db` 域名（host 模式下无DNS解析）

### RSSHub 到 Miniflux 添加源

```bash
curl -s -X POST http://localhost:8080/v1/feeds \
  -u "admin:test123" \
  -H "Content-Type: application/json" \
  -d '{"feed_url":"http://localhost:1200/bilibili/hot-search","category_title":"B站热点"}'
```

需要先创建分类：
```bash
curl -s -X POST http://localhost:8080/v1/categories \
  -u "admin:test123" \
  -H "Content-Type: application/json" \
  -d '{"title":"B站热点"}'
```

### 自定义 Docker 网络方案（备用）

如果不想用 host 网络，可以用自定义网络 + 端口映射 + 公共网络访问模式。但 **不推荐**——fetcher拒绝私网是 Miniflux 2.3.0 硬编码行为，很难绕过。

### RSSHub Bilibili UP主追更（需要用户Cookie）

B站 `bilibili/user/video/:uid` 路由需要登录Cookie才能绕过WAF反爬。对 `rsshub` 容器设置环境变量：

```bash
docker rm -f rsshub
docker run -d --name rsshub --network host \
  -e NODE_ENV=production \
  -e BILIBILI_COOKIE_1="你的SESSDATA值" \
  --restart unless-stopped \
  diygod/rsshub:chromium-bundled
```

用户需要在浏览器登录B站 → F12 → Application → Cookies → bilibili.com → 复制 `SESSDATA` 的值。

注意：多个UP主追踪只需要一个 `BILIBILI_COOKIE_1`（一个登录态即可追踪任意用户）。

### 已确认可用的 RSSHub 路由（无需Cookie）

| 路由 | 说明 | 需要Playwright? |
|------|------|:---------------:|
| `/bilibili/hot-search` | B站热搜 | ❌ |
| `/bilibili/popular/all` | B站综合热门 | ✅ |
| `/36kr/news` | 36氪资讯 | ❌ |
| `/huxiu/article` | 虎嗅文章 | ❌ |
| `/github/trending/daily` | GitHub趋势 | ❌ |

### 需Cookie的B站路由

| 路由 | 说明 | 原因 |
|------|------|:----:|
| `/bilibili/user/video/:uid` | UP主视频更新 | WAF 412阻断 |
| `/bilibili/user/video-all/:uid` | UP主全部视频 | WAF 412阻断 |

## 资源限制（重要）

此机器为 **7.1GB RAM, Ivy Bridge CPU**。Docker daemon本身占用约200MB。每个额外容器都会加剧内存压力。限制原则：
- 非必要容器不要开机自启（用 `videocaptioner` 改为手动启动）
- Miniflux + PostgreSQL 约200MB，可接受
- 避免同时运行多个容器

## Example: VideoCaptioner Deployment

```
echo 'password' | sudo -S docker pull ghcr.io/weifeng2333/videocaptioner:latest
echo 'password' | sudo -S docker run -d \
  --name videocaptioner \
  --restart unless-stopped \
  --cpus="1" \
  --memory="1g" \
  -p 8000:8000 \
  -p 8501:8501 \
  ghcr.io/weifeng2333/videocaptioner:latest
```
