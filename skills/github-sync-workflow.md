---
name: github-sync-workflow
description: GitHub项目同步流程 — 当配置/文件变更后，自动或手动同步到GitHub私有仓库，确保两台机器（A→B）数据一致。
---

# GitHub 项目同步流程（GT哈勃）

> 用于：配置变更后、新增技能/文件后、或手动触发同步。

## 一、架构

```
机器A（主用机）
  │
  ├─ external_memory/  ← 自动commit（每30分钟）→ GitHub
  ├─ config.yaml       ← 手动同步（改完就推）
  ├─ skills/           ← 手动同步（有变更就推）
  └─ scripts/          ← 手动同步（有变更就推）
         │
         ▼
GitHub 私有仓库 (github.com/f840047663-bot/external-memory)
         │
         ▼
机器B（克隆体/备用机）→ 定期git pull
```

## 二、外部记忆自动同步（无需手动）

已设置cron `外部记忆自动存档`，每30分钟自动commit+push。

```bash
# 查看状态
cd ~/桌面/Hermes外部记忆 && git status

# 查看最近一次自动commit
git log --oneline -3

# 手动触发一次同步（如果等不及30分钟）
cd ~/桌面/Hermes外部记忆 && git add -A && git diff --cached --quiet || git commit -m "manual $(date '+%m-%d %H:%M')" && git push
```

## 三、配置变更后必须手动同步

**触发条件：** 改了以下任意文件：

| 文件 | 路径 | 频率 |
|:----|:----|:----|
| `config.yaml` | `~/.hermes/config.yaml` | 每次改完立刻推 |
| 技能文件 | `~/.hermes/skills/` | 新增/修改后 |
| 脚本文件 | `~/.hermes/scripts/` | 新增/修改后 |
| 桌面启动脚本 | `~/桌面/*.sh` | 新增/修改后 |

**同步命令：**

```bash
# Step 1: 进仓库目录
cd ~/桌面/Hermes外部记忆

# Step 2: 复制需要同步的配置/文件进仓库
# config.yaml → 复制到仓库中备份（不要直接git管理，因为是不同的位置）
cp ~/.hermes/config.yaml ./config.yaml.backup

# Step 3: 将自定义脚本复制到仓库
cp -r ~/.hermes/scripts/*.py ./scripts/ 2>/dev/null

# Step 3.5: ★ 备份Hermes技能 → 转为AI可读的flat文件
ls ~/.hermes/skills/*/*/SKILL.md 2>/dev/null | while read f; do
  skill_name=$(basename "$(dirname "$f")")
  cp "$f" "./skills/${skill_name}.md"
done

# Step 4: commit + push
git add -A
git diff --cached --quiet || git commit -m "sync: config/scripts update $(date '+%m-%d %H:%M')"
git push
```

## 四、克隆盘B同步

```bash
# 在机器B上
cd ~/桌面/Hermes外部记忆
git pull

# 恢复配置
cp ./config.yaml.backup ~/.hermes/config.yaml

# 复制脚本
cp ./scripts/*.py ~/.hermes/scripts/
```

## 五、GitHub远程仓库信息

| 项目 | 内容 |
|:----|:-----|
| 远程地址 | `github.com/f840047663-bot/external-memory` |
| 协议 | HTTPS + Token |
| Token位置 | `~/.config/gh/hosts.yml` 或环境变量 |

## 六、铁律

1. **改完配置立刻同步** — 不要等到下次，否则B机器拉到的还是旧版
2. **改配置前先备份** — `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d%H%M)`
3. **两台机器不同时在线** — 全靠GitHub做中转，所以同步要及时
4. **避免冲突** — 同一时间只有一台机器改同一文件，否则合并时会冲突

## 七、验证同步成功

```bash
# 检查远程是否是最新版
cd ~/桌面/Hermes外部记忆
git fetch
git log --oneline HEAD..origin/main | head -3
# 如果没有输出 = 已是最新
```
