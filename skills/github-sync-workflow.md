# GitHub项目同步流程（GT哈勃）

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`github-sync-workflow`（devops分类）

## 架构

```
机器A（主用机）
  │
  ├─ external_memory/  ← 每30分钟自动commit→GitHub
  ├─ config.yaml       ← 改完手动同步
  ├─ skills/           ← 新增/修改后手动同步
  └─ scripts/          ← 新增/修改后手动同步
         │
         ▼
GitHub (github.com/f840047663-bot/external-memory)
         │
         ▼
机器B（克隆盘）→ git pull
```

## 自动同步（外部记忆）

已设置cron，每30分钟自动commit+push。

## 配置/技能变更后手动同步

```bash
cd ~/桌面/Hermes外部记忆

# 1) 备份config.yaml
cp ~/.hermes/config.yaml ./config.yaml.backup

# 2) 备份脚本
cp -r ~/.hermes/scripts/*.py ./scripts/ 2>/dev/null

# 3) 备份Hermes技能 → 做AI可读的备份文件
# 用以下命令打包所有技能成可读备份
ls ~/.hermes/skills/*/*/SKILL.md 2>/dev/null | while read f; do
  skill_name=$(basename $(dirname $f))
  cat "$f" > "./skills/${skill_name}.md"
done

# 4) commit + push
git add -A
git diff --cached --quiet || git commit -m "sync: $(date '+%m-%d %H:%M')"
git push
```

## 克隆盘B恢复

```bash
cd ~/桌面/Hermes外部记忆
git pull
cp ./config.yaml.backup ~/.hermes/config.yaml
cp ./scripts/*.py ~/.hermes/scripts/
```

## 铁律

1. 改完配置立刻同步，不等下次
2. 改配置前先备份
3. 同一时间只有一台机器改同一文件，避免冲突
4. 改完推送后在微信发"已同步"，通知对方
