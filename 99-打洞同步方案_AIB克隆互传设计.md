# 打洞同步方案 — 两台Hermes克隆体互传内部记忆

> **状态：** 📋 方案已设计，暂未实施
> **创建：** 2026-05-22
> **原因：** 用户想以后两台Hermes通过Tailscale打洞，实时互传内部记忆

---

## 目标

两台Hermes实例同时运行，通过内网打洞（Tailscale）定期互传内部记忆，实现L1记忆同步。

## 架构

```
机器A（主用机）
  │ Tailscale IP: 100.x.x.1
  │
  │ ┌─ 内部记忆 (8KB) ──┐
  │ │ MEMORY.md         │ ←→ rsync 双向同步（每5分钟）
  │ │ USER.md           │
  │ ├─ state.db (83MB) ─┤
  │ │ 会话历史+内部记忆  │ ──→ rsync 单向同步 A→B
  │ ├─ 向量库 (276MB) ──┤
  │ │ ~/.pg0/           │ ⏸ 停服同步（重大变更时才做）
  │ └─ 外部记忆 (2.1MB) ─┘
  │    .md文件           │ ←→ GitHub自动同步（已实现）
  │
机器B（克隆体/备用机）
  │ Tailscale IP: 100.x.x.2
```

## 分层同步策略

| 层级 | 内容 | 大小 | 同步方式 | 频率 |
|:----|:----|:---:|:--------|:---:|
| L1 | MEMORY.md + USER.md | **8KB** | rsync 双向（互相同步） | 每5分钟 |
| state.db | 会话历史+内部记忆DB | **83MB** | rsync 单向（A→B） | 每小时 |
| L2向量库 | ~/.pg0/ | **276MB** | 停服打包+scp | 手动/重大变更 |
| 外部记忆 | .md文件 | 2.1MB | GitHub自动 | 每30分钟 |

## 关键设计决策

### 1. L1双向互传（8KB — 无脑传）
- 两边的MEMORY.md和USER.md相互覆盖
- 谁的最后修改时间新，就覆盖对方的
- 8KB的东西，不怕冲突

### 2. state.db单向同步（A→B）
- SQLite不支持两台同时写
- 机器A是主写入方，机器B是只读方
- 每整点从A rsync到B，覆盖B的state.db
- B的会话历史在同步前会被A的覆盖（B上的独立对话丢失）

### 3. 向量库停服同步（276MB）
- 两边都停hindsight-api
- tar.gz压缩 → scp传输 → 解压覆盖
- 重启服务
- 只做重大变更后手动触发

### 4. 外部记忆继续走GitHub
- 已实现，每30分钟自动commit+push
- 另一台git pull即可

## 实施步骤（等用户说搞时执行）

### 前置条件
1. 两台机器都装了Tailscale并能互ping
2. Tailscale IP已知

### 部署命令

```bash
# 机器A上执行（主用机）
# 1. 安装同步脚本
cat > ~/.hermes/scripts/sync-l1-to-b.sh << 'SCRIPT'
#!/bin/bash
# 每5分钟：把L1内部记忆同步到机器B
B_IP="100.x.x.2"  # ⚠️ 换成实际IP
rsync -avz --timeout=10 "$HOME/.hermes/memories/MEMORY.md" "$HOME/.hermes/memories/USER.md" "fw@$B_IP:.hermes/memories/"
SCRIPT
chmod +x ~/.hermes/scripts/sync-l1-to-b.sh

# 机器B上执行（克隆体）
cat > ~/.hermes/scripts/sync-l1-to-a.sh << 'SCRIPT'
#!/bin/bash
# 每5分钟：把L1内部记忆同步到机器A
A_IP="100.x.x.1"  # ⚠️ 换成实际IP
rsync -avz --timeout=10 "$HOME/.hermes/memories/MEMORY.md" "$HOME/.hermes/memories/USER.md" "fw@$A_IP:.hermes/memories/"
SCRIPT
chmod +x ~/.hermes/scripts/sync-l1-to-a.sh
```

### 定时任务配置

```bash
# 机器A crontab（每5分钟推送+接收）
*/5 * * * * bash ~/.hermes/scripts/sync-l1-to-b.sh
# 机器B crontab（每5分钟推送+接收）
*/5 * * * * bash ~/.hermes/scripts/sync-l1-to-a.sh
```

### 向量库手动同步命令

```bash
# 两边都停hindsight
systemctl --user stop hindsight-api

# A上打包
tar czf /tmp/pg0-backup.tar.gz -C ~ .pg0

# 传到B
scp /tmp/pg0-backup.tar.gz fw@B_IP:/tmp/

# B上恢复
cd ~ && tar xzf /tmp/pg0-backup.tar.gz

# 两边重启
systemctl --user start hindsight-api
```

## 注意事项

1. **state.db 单向**：B的本地会话在同步后丢失，B上跟用户的对话历史会被A的覆盖
2. **ssh密钥**：两边需要配好ssh免密登录（`ssh-copy-id`）
3. **Tailscale网速**：打洞后是P2P直连，通常比公网快，但取决于两边网络
4. **不要同时写同一个外部记忆文件**：Git能处理，但合并冲突需要人工解决
5. **开机自启**：两台机器的Tailscale应设为开机自启

## 回滚

如果同步导致一方记忆混乱：
```bash
# 从GitHub恢复外部记忆
cd ~/.hermes/external_memory && git pull

# 从本地备份恢复内存（如果做过）
ls ~/桌面/内部记忆与向量库备份_*/
```
