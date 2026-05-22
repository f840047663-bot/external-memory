---
name: hermes-10-config-optimizations
title: Hermes Agent 10项进阶配置优化
description: >-
  根据官方视频教程总结的10项Hermes Agent进阶配置优化要点，
  对照本系统当前实施状态。可逐项执行提升稳定性与token效率。
tags: [config, optimization, hermes, performance]
---

# Hermes 10项进阶配置优化 — 实施状态检查表

视频来源：Hermes Agent 官方进阶教程（2026-05-17 用户分享）
核心目标：从"会用"到"好用"，解决 ①agent复读 ②长任务卡死 ③token消耗快

## 实施状态总览

| # | 优化项 | 状态 | 改前 | 改后 |
|:-|:------|:----|:----|:----|
| ① | Hook机制 (SESSION_START/PRE_LLM/POST_LLM/SESSION_END) | ❌ 未实施 | `hooks: {}` | 需写脚本绑定 |
| ② | reasoning_effort | ✅ 已改 | 空 → `medium` | 简单省token，复杂切high |
| ③ | tool_use_enforcement | ✅ 已改 | `auto` → `true` | 强制调工具不嘴上答应 |
| ④ | 压缩策略 | ✅ 已改 | threshold 0.5→**0.6**, protect_last_n 12→**30** | 少压防丢上下文 |
| ⑤ | SOUL.md规则文件 | ✅ 已改 | 只有1行默认prompt | 加了4条Defaults规则 |
| ⑥ | 分层加载Skill | ✅ 天然支持 | — | — |
| ⑦ | skill_manage复用 | ✅ 已在用 | — | — |
| ⑧ | 并行子任务+worktree | ⚠️ 半开 | max_concurrent_children: 3 | worktree未配置 |
| ⑨ | 调试三板斧 | ✅ 基本有 | verbose/debug share/logging | — |
| ⑩ | 官方新Skill (arch/info) | ❌ 未装 | 未在库中 | 需从skills hub拉取 |

## 各优化项详情

### ① Hook机制（未实施）
四个生命周期Hook点可插入自定义脚本：
- `SESSION_START` — 会话开始时加载环境
- `PRE_LLM_CALL` — 调用模型前注入上下文（如Git分支状态）
- `POST_LLM_CALL` — 拿到模型回复后存档（如自动Git提交）
- `SESSION_END` — 会话结束时收尾

当前配置：`hooks: {}`，未启用。

### ② reasoning_effort（已实施）
```yaml
delegation:
  reasoning_effort: medium  # 默认为medium省token
```
- 复杂任务（投资分析/代码/调试）→ 手动设 `high`
- 简单任务 → `medium` 省token

### ③ tool_use_enforcement（已实施）
```yaml
agent:
  tool_use_enforcement: true  # 强制调用工具
```
- `auto` 模式下agent可能口头答应但不真调工具
- `true` 确保每次需要工具的任务都实际调用

### ④ 压缩策略（已实施）
```yaml
compression:
  enabled: true
  threshold: 0.6    # 以前0.5，现在到60%上下文才压缩
  target_ratio: 0.2
  protect_last_n: 30  # 保护最近30轮不压缩（以前12轮）
```
- 更高的threshold = 更少触发压缩 = 更多上下文保留 = 防复读
- 更多的protect_last_n = 最近对话不被压缩吞掉
- 代价：略微增加输入token量

### ⑤ SOUL.md规则文件（已实施）
```markdown
[Defaults]
- Before modifying code/scripts, always ask the user which specific file
- Never refactor large sections of code without explicit approval
- Keep responses concise; avoid repeating the user's own question back to them
- When unsure about a file path, check with the user before proceeding
```
路径：`~/.hermes/SOUL.md`

### ⑥ 分层加载Skill（天然支持）
Hermes 天然支持三层按需加载：
- 第一层：只加载Skill列表（少量token）
- 第二层：需要时加载Skill正文
- 第三层：按需加载子文档

### ⑦ skill_manage复用（已在用）
通过 `skill_manage` 将流程存为Skill，下次直接复用。
已在日常工作中使用。

### ⑧ 并行子任务+worktree（半开）
```yaml
delegation:
  max_concurrent_children: 3   # 已开
  max_spawn_depth: 1
  subagent_auto_approve: false
```
- `delegate_task` 可一次派发多个独立子任务并行
- worktree 配置未启用（需要Git工作流场景）

### ⑨ 调试三板斧（基本有）
- `verbose all` — 开启详细日志
- `debug share` — 一键打包日志+系统信息脱敏分享
- `gateway_timeout: 1800` — 30分钟超时自动断开

### ⑩ 官方新Skill（未装）
视频介绍了三个官方新Skill：
- `/architecture` — 一键生成系统架构图
- `/infographic` — 长文转信息图
- `hackathon` — AI开发挑战赛

当前系统中不存在，需要用户决定是否从skills hub拉取。

## 实施优先级建议

**立即见效（已实施 ✅）：** ②③④⑤
**下一个批次：** ① Hook机制（需写脚本，收益高）
**有场景再搞：** ⑧ worktree（需Git多项目场景）⑩ 新Skill（用户决定）

## 关联参考

- `references/cache-hit-rate-optimization.md` — 本用户专属的缓存命中率优化策略。当用户抱怨API花费高或要求提升缓存效率时，**优先读这个文件**再行动。不要提降模型规格——本用户的花费敏感度（末位优先级）和模型路由已有定论。
