---
name: system-migration
title: 系统迁移 — 备份/恢复/远程部署
description: >-
  完整备份和恢复 Hermes 的全部三层记忆（L1+L2+L3）+配置+API密钥。
  支持本地备份、跨机迁移、闲鱼代装。
  核心工具：~/桌面/一键全记忆备份.sh（双击运行，含全套）
triggers:
  - 换电脑/重装系统后恢复记忆
  - 每周/定期备份记忆到外部硬盘
  - 需要备份内部记忆+向量库（轻量备份，桌面双击）
  - 需要为客户远程部署 Hermes+OpenClaw（闲鱼代装场景）
  - 配置损坏需要恢复
  - 验证备份文件是否完整
  - 需要自动定期验证备份文件是否仍完好（定时任务触发）
  - 用户说"备份文件名不对"时查找实际文件
  - 用户要求写自动上传备份到云盘的脚本
  - 需要了解版本兼容性
  - 恢复后模型连不上 / API Key缺失
  - 抖音监控不工作了 / douyin脚本丢了
  - 需要另一个AI帮忙恢复系统
  - 桌面卡死、鼠标不动、系统没反应
  - 国内网站打不开（青山VPN残留代理）
  - systemd-oomd 误杀进程导致崩溃
  - Gnome shell 卡死/崩溃
  - Miniflux Docker 容器重启后没启动
  - 向量库 hindsight-api 内存占用过高
---

# 系统迁移技能

## 关键工具

**`~/桌面/一键全记忆备份.sh`** — 双击直接运行

替代了旧版 `全记忆备份.sh`（已归档到 旧资料/）。

| 模式 | 命令 | 行为 |
|------|------|------|
| **一键备份（全量）** | `~/桌面/一键全记忆备份.sh` | 自动打包全部三层记忆到桌面 `hermes-backup-日期.tar.gz`，含L1+L2+L3+配置+API密钥 |
| **轻量备份（仅L1+L2）** | `~/桌面/内部记忆与向量库备份.sh` | 只备份内部记忆(8KB)+向量库(99MB)，双击可选本地或GitHub上传。日常用选1，重大变更选2。详见 `references/lightweight-l1l2-backup.md` |

### 一键备份内容（完整覆盖，无盲区）

| 类别 | 路径 | 是否包含 |
|:----|:-----|:--------|
| 🏠 **L1 内部记忆** | `~/.hermes/memories/` | ✅ |
| 🧬 **L2 向量库** | `~/.pg0/` | ✅ (~153MB, 551条事实) |
| 📚 **L3 外部知识库** | `~/.hermes/external_memory/` (含 `positions/` 子目录, 24-系统架构说明书.md, 21-贝叶斯防偏差规则.md, 20-三层互锁架构设计.md) | ✅ |
| ⚙️ **配置** | `~/.hermes/config.yaml` | ✅ |
| 🔑 **API密钥** | `~/.hermes/.env` | ✅ **← 旧版遗漏，新版已修复** |
| 🏃 **定时任务** | `~/.hermes/cron/jobs.json` | ✅ |
| 🏗️ **全部技能** | `~/.hermes/skills/` | ✅ |
| 💬 **历史会话** | `~/.hermes/state.db` | ✅ |

### 🔄 自动备份验证（定时任务驱动）

**背景：** 系统中有一个定时任务 `提醒：验证备份恢复`（每2天执行），自动检查桌面备份文件的完整性和新硬盘的接入状态。

详见 `references/backup-verification-by-cron.md` — 包含所有 `tar tzf` 验证命令、文件名时间戳陷阱的处理方法、磁盘状态检查流程。

**验证清单（AI定时任务执行时对照）：**
1. ✅ 备份文件存在且 >50MB
2. ✅ tar.gz 可正常列出内容（`tar tzf` 无报错）
3. ✅ 顶层结构含全部11项（README/恢复说明/恢复脚本/config/api密钥/会话数据库/记忆/外部知识库/技能库/定时任务/向量数据库）
4. ✅ 核心生存文件齐全（config.yaml + api密钥.env + MEMORY.md + 会话数据库.db）
5. ⚠️ 检查用户记忆的备份文件名是否与实际一致（失败重跑会导致时间戳不同）
6. 🖥️ 检查新硬盘是否已接入（`lsblk` 查看新增磁盘）

### ☁️ 计划增强：自动上传备份到云盘（待实现）

**目标：** 每周自动备份 + 自动上传到云盘（百度网盘/阿里云盘/OneDrive），用户无需手动操作。

**当前状态（2026-05-17）：**
- ❌ Linux下无云盘CLI工具（百度网盘仅Windows版在NTFS分区）
- ❌ `rclone` 未安装
- ❌ `aliyun`/`百度云CLI` 未安装

**实现方案（待选择）：**
| 方案 | 优点 | 缺点 |
|:----|:----|:-----|
| `rclone` + 百度网盘/阿里云盘 | 全命令行，可嵌入定时任务 | 需配WebDAV/第三方API，百度网盘限速 |
| `python` + bypy (百度网盘SDK) | 轻量级 | bypy依赖百度网盘API token，可能过期 |
| curl 上传到阿里云盘/OneDrive | 不需要额外工具 | 需要refresh token逻辑 |
| 直接挂载百度网盘分区（NTFS）手动拷贝 | 零开发成本 | 无法自动化 |

**触发条件：** 用户确认第1步（新硬盘恢复验证）通过后，提醒我来实现这个脚本。

**集成方式：**
- 扩展 `一键全记忆备份.sh` → 备份完成后调用上传函数
- 或在定时任务中新增一个步骤：先跑备份脚本 → 再跑上传命令

备份时自动执行 `generate_manifest()` 函数，生成一份 `恢复清单_日期.txt`：

- **保存位置 1：** `~/桌面/恢复清单_日期.txt` — 人眼直接可读
- **保存位置 2：** 打包进 tar.gz 备份文件 — 永远跟备份一起走

清单内容涵盖：
1. 必须安装的软件本体（Hermes/OpenClaw + 安装命令）
2. 辅助工具安装状态（Pinchtab/RTK/Rust — 检测是否存在，附带安装命令）
3. API Key 位置（.env）— 重点提醒不在备份包里
4. 用户脚本状态（douyin-monitor.py等 — 检测是否存在，提醒不在备份中）
5. 桌面额外文件
6. **config.yaml 变更记录**（model路由、providers新增）
7. 外部记忆文件清单
8. 定时任务
9. **备份盲区汇总**（红/黄/绿分级）
10. **换电脑恢复步骤**（7步完整流程）

**核心价值：** 就算你完全不记得装过什么，打开这份清单就能完整重建系统。所有安装命令、文件路径、分级提醒都在上面。

## 备份内容清单

### Hermes
| 路径 | 内容 |
|------|------|
| `~/.hermes/config.yaml` | 主配置（API Key、模型设置、插件配置） |
| `~/.hermes/state.db` | SQLite — 内部记忆 + 历史会话 + session_search 数据 |
| `~/.hermes/cron/jobs.json` | 所有定时任务 |
| `~/.hermes/private.gpg` | 加密敏感信息（密码等） |
| `~/.hermes/external_memory/` | 第2层+第3层所有MD文件 |
| `~/.hermes/memories/` | L1内部记忆（MEMORY.md + USER.md）|
| `~/.hermes/skills/` | 所有自定义Skills |
| `~/.pg0/` | Hindsight L2 PostgreSQL 向量数据（~500MB） |

### OpenClaw
| 路径 | 内容 |
|------|------|
| `~/.openclaw/openclaw.json` | 主配置 |
| `~/.openclaw/workspace/` | SOUL/USER/IDENTITY/AGENTS/TOOLS/HEARTBEAT |
| `~/.openclaw/cron/` | 定时任务 |
| `~/.openclaw/memory/` | 所有记忆（含 private.gpg） |

### 桌面脚本
❗ **⚠️ 不是所有桌面脚本！** 实际只备份以下硬编码列表（备份脚本第125-128行）：
- `备份OpenClaw.sh`
- `查余额.sh`
- `手机投屏.sh`
- `md.sh`
- `全记忆备份.sh`（自身）
- **新创建的脚本（如 `check_api_balance.sh`）不会被自动备份**，需要手动加进硬编码列表。

### 🆕 轻量备份脚本（2026-05-22 新增）

**`~/桌面/内部记忆与向量库备份.sh`** — 双击运行，选模式：

| 模式 | 行为 | 适用场景 |
|:----|:-----|:--------|
| [1] 仅本地 | 内部记忆(8KB)+向量库(99MB) → 存桌面 | 日常小改动 |
| [2] 本地+GitHub | 同上 + commit+push到GitHub | 重大变更后 |

**不受 `一键全记忆备份.sh` 硬编码列表限制** — 这个脚本独立于大备份脚本，想用随时双击。

### ⚠️ 严重遗漏（恢复后系统可能不可用）

| 遗漏项 | 为什么重要 | 恢复方法 |
|:------|:----------|:---------|
| ✅ `~/.hermes/.env` | **已修复！** 新版脚本自动打包（重命名为`api密钥.env`） | 解压运行恢复脚本.sh 自动恢复 |
| ❌ `~/.hermes/scripts/` | douyin-monitor.py等自定义脚本 | 手动复制或从Git重新下载 |
| ❌ 桌面.txt/.md文件 | Hermes模型切换-恢复指南.txt等 | 手动复制 |
| ❌ `~/.hermes/douyin_state.json` | 抖音监控进度，丢了会重复下载 | 从旧系统复制 |

### 版本信息
备份时自动记录 Hermes + OpenClaw 版本到 `全记忆备份_版本信息_*.json`，恢复时自动对比兼容性。

## 版本兼容性

**当前测试通过的版本：**
- Hermes v0.13.0 (2026.5.7)
- OpenClaw 2026.5.6 (c97b9f7)

**规则：**
- `state.db`（内部记忆+历史）和 `config.yaml` 的格式随版本变化，跨大版本恢复可能不兼容
- `external_memory/` 和 `skills/` 是纯MD文件，**任何版本通用**
- 恢复脚本自动检测版本差异并提示
- 如果版本不一致导致异常：删掉 `state.db` 重启，AI会丢失内部记忆但外部MD文件完好

## 新电脑恢复步骤

```
第1步：装 Hermes Agent
  git clone https://github.com/NousResearch/hermes-agent.git
  cd hermes-agent && pip install -e .

第2步：装 OpenClaw
  npm install -g openclaw@latest

第3步：恢复记忆
  bash 全记忆备份.sh 恢复 U盘/你的备份.tar.gz

第4步：重启服务
  hermes start && openclaw gateway start
**第5步：检查 Hindsight L2 是否已启动**
```bash
curl localhost:9177/health
# 应返回 {"status":"healthy","database":"connected"}
# 验证有551条记忆：
curl localhost:9177/v1/default/banks/hermes/stats
```

恢复脚本会自动：
1. ✅ 检查软件是否已安装
2. ✅ 对比备份版本和当前版本
3. ✅ 停服避免文件锁
4. ✅ 备份当前配置到 `~/.hermes_恢复前备份_时间戳/`
5. ✅ 解压恢复
6. ✅ 验证关键文件
7. ✅ 启服

### 🛠️ 恢复后必须手动补充

备份脚本不包含以下文件，恢复后需手动处理。**但别急——备份时生成的 `恢复清单_日期.txt` 已在桌面和备份包里，打开它就有完整指引：**

```bash
# 1. 复制 .env（所有API Key）
cp /U盘路径/.env ~/.hermes/.env

# 2. 复制自定义脚本
cp -r /U盘路径/scripts/ ~/.hermes/scripts/

# 3. 复制抖音监控状态
cp /U盘路径/douyin_state.json ~/.hermes/

# 4. 复制桌面非.sh文件（恢复指南等）
cp /U盘路径/Hermes模型切换-恢复指南.txt ~/桌面/
cp /U盘路径/check_api_balance.sh ~/桌面/

# 5. 重启服务
hermes start && openclaw gateway start
```

**验证恢复是否完整：**
```bash
# 确认关键文件存在
ls ~/.hermes/.env && ls ~/.hermes/scripts/douyin-monitor.py && ls ~/桌面/check_api_balance.sh
```

## 远程部署（闲鱼代装场景）

### 流程图

```
大好人：             Hermes（我）：
  1. 装Ubuntu          5. SSH连入
  2. 插U盘（含脚本+模板）  6. 装Hermes本体
  3. 跑一键开远程脚本     7. 装OpenClaw本体
  4. 发IP给我          8. 从U盘恢复记忆模板
                       9. 配置API Key
                       10. 测试→收工
```

### Windows 支持（WSL2 方案）

如果客户是 Windows 电脑，可以装 WSL2 跑 Ubuntu 环境，**所有脚本、远程控制、恢复，与原生 Ubuntu 完全一样**：

```bash
# 客户机上跑一次（大好人在装系统时运行）
wsl --install -d Ubuntu
# 装完后设置用户名密码，进入 Ubuntu shell
# 后面插U盘+跑一键开远程脚本的流程与 Ubuntu 完全一致
```

| 步骤 | Ubuntu | Windows + WSL2 |
|:----|:--------|:--------------|
| 系统 | 装 Ubuntu | 保留 Windows → 开 WSL2 |
| 跑脚本 | ✅ 原生 | ✅ WSL 里一样跑 |
| SSH 远程 | ✅ 自带 | ✅ WSL 自带 |
| Tailscale | ✅ 原生 | ✅ Windows 或 WSL 都行 |
| 记忆恢复 | ✅ 一样 | ✅ 一样 |
| **额外步骤** | 无 | 装 WSL2 的一次性操作 |

**注意：** Hermes 有 Windows 原生版（PowerShell 安装，Early Beta），但**不推荐**——bash 脚本不兼容、有已知 bug。始终优先推送 Ubuntu 或 WSL2。

### 一键开远程脚本

**预装在U盘中，交付时由大好人在客户机上运行：**

```bash
#!/bin/bash
# 一键开远程脚本 — U盘自带
set -e

# 1. 安装 Tailscale（自动内网穿透，多层NAT无压力）
if ! command -v tailscale &>/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

# 2. 连接 Tailscale 网络
sudo tailscale up --accept-routes --accept-dns=false

# 3. 开 SSH
sudo systemctl enable ssh --now 2>/dev/null || sudo apt install -y openssh-server

# 4. 显示连接信息
MY_IP=$(tailscale ip -4 2>/dev/null)
echo "✅ 远程通道已开启！"
echo "   IP: $MY_IP"
echo "   用户名: $(whoami)"
```

### 远程部署要点
- **Tailscale** 是核心工具，自动内网穿透，无需公网IP或端口转发
- 免费用户最多3台设备，客户场景够用
- U盘内容：`一键开远程.sh` + `全记忆备份_模板.tar.gz`（清空隐私的纯净模板）
- 脚本设计为可重入的（断网重跑不报错）
- 隐私清理后的模板不含：API Key、私人记忆、历史对话、加密数据

## 灾难恢复（反脆弱设计）

详见 `~/.hermes/external_memory/99-灾难恢复与迁移手册.md`

### 三层记忆恢复总览（什么能/不能从MD恢复）

| 能恢复的（纯MD文本） | 位置 | 不能恢复的 | 怎么办 |
|:--------------------|:-----|:----------|:------|
| 🏠 L1内部记忆 | `~/.hermes/memories/MEMORY.md` | 🧬 L2向量库(551条) | 备份`~/.pg0/`（已加进脚本） |
| 🏗️ Skills | `~/.hermes/skills/` | 💬 历史对话(session_search) | 备份`state.db` |
| 📚 L3外部知识库 | `~/.hermes/external_memory/` | 🦞 小龙虾的记忆 | 小龙虾自己的备份 |
| ⚙️ 配置+密钥 | `config.yaml` + `.env` | — | — |
| 🏃 定时任务 | `cron/jobs.json` | — | — |

**结论：存好MD文件=保底活过来。存好`~/.pg0/`+`state.db`=跟没坏过一样。**

### 反脆弱设计原则：人机兼读（2026-05-15 核心原则）

### ✅ 反脆弱设计原则：人机兼读（核心原则 — 2026-05-15 两次纠正后确立）

**铁律：** 任何存档/打包/输出的产物，必须同时满足两个读者：

| 读者 | 需求 | 满足方式 |
|:----|:-----|:---------|
| 👤 **人**（半年后翻出来） | 一眼看懂这是啥、每个文件对应什么、怎么用 | README.txt + 恢复说明.txt 在包内最前面，每个文件有用途+不恢复后果 |
| 🤖 **AI** | 机器可解析、结构好恢复 | 标准目录结构 + 完整数据 |

**具体到备份包：** 打开 `hermes-backup-*.tar.gz` 第一眼必须看到：

1. `Hermes备份_YYYYMMDD_HHMMSS/` 文件夹（**可见名称，不用点开头隐藏目录**）
2. 点进去：
   - `README.txt` — "这是什么？含什么？每个文件的用途和不恢复的后果"
   - `恢复说明.txt` — "恢复步骤，含优先级清单，不需要AI，人自己就能干"
   - `恢复脚本.sh` — "双击自动恢复"
   - `config.yaml` / `api密钥.env` / `会话数据库.db` / `记忆/` / `外部知识库/` / `技能库/` / `向量数据库/`
     （**全部可见，没有隐藏文件，GUI文件管理器直接显示**）

**两张血的教训（2026-05-15）：**

| 版本 | 问题 | 用户反应 | 修复 |
|:----|:-----|:---------|:-----|
| 第1版 | 包内路径 `.hermes/` 和 `.pg0/` 以点开头，GUI文件管理器默认隐藏 | "打开啥都没有" | 加README + 恢复说明在顶层 |
| 第2版 | README只写一句话总览，不写每个文件的具体作用 | "我就知道两个txt文件，备份文件在哪？" | 每个文件写清楚：用途 + 不恢复的后果 + 优先级 |
| 第3版（最终） | ✅ 用可见文件夹名 `Hermes备份_/`，不再使用隐藏路径 | ✅ | 脚本末尾打印完整目录树 |

**最终结论（用户原话）：** "这个东西是给人看的，很多东西不是给你们AI看的，要保持一定的冗余空间。"

每次创建备份时：
1. `README.txt` 必须包含：每个文件的作用（"如果丢失会怎样"的后果说明），按优先级排序
2. `恢复说明.txt` 必须包含：优先级清单（空间不够先恢复哪些）、每个文件的详细说明、步骤
3. 路径必须可见（**不要用点开头**），不管用户是不是打开"显示隐藏文件"
4. 脚本末尾打印完整的目录树 + 实际内容列表示例
→ 脚本内 `README_END` / `RESTORE_END` 多行字符串已实现，见 `一键全记忆备份.sh` 38-77行

### 一键备份脚本输出规范

**铁律：** 任何用户双击运行的脚本，必须有分步输出 + 醒目的结果展示 + 等待按键退出：

```bash
# 好的输出
echo \">>> 第1步：检查关键文件...\"
# 每一步让用户看到进度
sleep 1
# 末尾
echo \"按 ENTER 键退出...\"
read
```

新版 `一键全记忆备份.sh` 已按此标准重写。详见 Pitfalls 节的「旧版脚本无输出问题」。

**三层互为备份原则：**
- 第1层（内部记忆）丢失 → 第2层+第3层可重建
- 第2层（外部MD）丢失 → 第1层规则 + session_search 可重建
- 第3层（tracklog）丢失 → 第2层有摘要

**最坏情况恢复（什么都不剩）：**
→ `external_memory/` 在 → 你的投资逻辑和交代全在
→ `state.db` 丢了 → 我失去内部记忆，但读一遍外部文件就能重建

## 双API互备

从2026-05-13起，Hermes配置了两个互相备份的API：
- **DeepSeek V4 Flash**（default profile）— 复杂任务主力
- **Qwen-turbo（阿里云百炼）**（cheap profile）— 简单聊天走免费额度

详见 `references/dual-api-setup.md`

## 🛡️ 配置修改安全协议（10分钟确认机制）

**优先于一切其他规则。** 以下是用户明确要求的修改流程：

### 改任何配置前必须做的
1. **先 `curl` 测试新API/新配置是否能通** — 确保Key有效、endpoint可达、返回200
2. **全备份**: `cp config.yaml config.yaml.bak.$(date +%s)`
3. **通知对方**（Hermes/小龙虾）：我要改什么，预计多久改完
4. **改配置**
5. **再测试一次** — 完整跑通一个使用场景，确认真的能用
6. **2小时内向对方确认"改成功了"**
7. **再告诉用户"搞定了"**

### 10分钟对称急救机制（双向铁律 — 2026-05-15 用户确立为10分钟）

- 任何一方改配置，改完后**10分钟内**必须向另一方确认成功
- **超时没确认 = 默认对方出事**
- 对方执行急救流程（看对应急救手册）
- **备份文件位置：** `ls -t /home/fw/.hermes/config.yaml.bak.* | head -1`
- **回滚命令：** 停服务 → `cp config.yaml.bak.* config.yaml` → 重启服务
- 适用场景：Hermes改API配置、小龙虾改gateway配置、任何系统级修改

### 对称急救（双向）
| 谁坏了 | 谁修 | 手册 |
|:------|:----|:-----|
| Hermes | 小龙虾 | `~/.hermes/external_memory/Hermes急救手册-找小龙虾修我.md` |
| 小龙虾 | Hermes | `~/.hermes/external_memory/小龙虾急救手册.md` |
| 双方都坏了 | 大好人手动 | 从U盘/硬盘备份恢复 |

### 绝对不能做的


- ❌ 改完配置不测试就说"好了" ← 这次session被用户抓到了
- ❌ 改配置中途切换当前对话的模型 ← 中途换模型会导致前半截DeepSeek后半截Qwen，对话崩
- ❌ 改了配置文件但不重启服务就以为生效了
- ❌ 用户给了Key就直接用，不先 `curl` 验一下 ← 这次阿里云Key是401无效Key，用户反馈才知道

### 血的教训（2026-05-14）
配置阿里云百炼API Key时：
1. 用户填了Key到桌面文件
2. 我直接加到 `.env` 并创建了 cheap profile
3. 测试时只测了 `curl` 返回了"正常"字样（其实是DeepSeek的缓存，没真正验证阿里云）
4. **告诉用户"阿里云通了"**
5. 实际切过去是 401 Incorrect API key
6. 用户找小龙虾才把我救回来

**教训：测试要测真实的路径，不要被假成功迷惑。**

### 用户原话
> "你肯定一次性给我改好，你不一次性改好，我下次一发现这玩意儿运行不了的话，我再找你，你又跟失忆了一样"
> "千万不要把自己搞坏了，先验证完了之后再来搞"

### 恢复方法（搞坏了怎么办）
详见 `~/.hermes/external_memory/Hermes急救手册-找小龙虾修我.md`
- 浏览器打开 `http://127.0.0.1:18789/chat?session=main`
- 告诉小龙虾"修一下Hermes"
- 小龙虾有终端权限，能恢复备份、改配置、重启服务
- 最坏情况：从U盘/硬盘的备份文件恢复

### 📁 模板文件（2026-05-15 已更新）

⚠️ 模板已更新为**可见文件夹**格式，与 `一键全记忆备份.sh` 对齐。

技能目录下提供了可复用的备份/恢复模板：

| 文件 | 用途 | 说明 |
|:----|:-----|:-----|
| `templates/README_备份总览.md` | 压缩包内总览说明（人机兼读版） | ✅ 已更新：可见路径、每个文件+不恢复后果、优先级清单 |
| `templates/恢复说明_详细步骤.md` | 压缩包内恢复指南 | ✅ 已更新：同上 |

> **注意：** 实际备份脚本 `一键全记忆备份.sh` 中嵌入了内联版本（硬编码在 `README_END` / `RESTORE_END` 多行字符串块中），模板文件是为新建备份脚本准备的参考。
> 如果只是修改现有备份，改 `一键全记忆备份.sh` 中的内联文本即可，模板文件只用于新脚本脚手架。

创建新备份脚本时，直接复制这两个模板再调整，不需要从头写。

### 🔴 投资分析框架-新智能体接手指南（2026-05-16 新增）\n\n**新文件：** `~/.hermes/external_memory/投资分析框架-新智能体接手指南.md`\n\n这是一个独立的恢复文档——如果Hermes崩了或者换了新AI，读这个文件就能接手完整的投资分析工作，不需要大好人重新讲。包含：\n- 三层框架（宏观→中观→微观）\n- 完整持仓与机会排名\n- 每日每周工作流程\n- 当前关键假设\n- 信息源管理\n- API与成本控制\n- 大好人的终极偏好清单\n\n**这个文件在 `external_memory/` 下，随备份自动带走。** 恢复后新AI应优先读这个文件。
- ✅ **Hermes急救手册**：`~/.hermes/external_memory/Hermes急救手册-找小龙虾修我.md` — 小龙虾救我
- ✅ **小龙虾急救手册**：`~/.hermes/external_memory/小龙虾急救手册.md` — 我救小龙虾
- ✅ **铁律文件**：`~/.hermes/external_memory/00-改配置铁律.md` — 双方都得遵守
- 改配置前必须通知对方+备份，改完20分钟内确认，超时=对方救

### 当前已知限制

1. Tailscale 免费版限3设备，客户多了需升级付费或改用 ZeroTier（不限设备数）
2. 硬件驱动差异（显卡/WiFi等）需手动处理，Ubuntu一般自带通用驱动
3. 远程部署依赖于 SSH 和 Tailscale 的外部网络连通性

### 🛡️ 系统可靠性 — 常见故障模式及修复

### 故障1: systemd-oomd 误杀进程导致桌面卡死/应用崩溃

**现象：** 物理内存仅用~40%（2.8GB/7.1GB），但 systemd-oomd 将文件缓存计入已用内存，触发 OOM 杀进程（gnome-settings-daemon 等），导致：
- 桌面完全卡死、鼠标冻结
- 弹出的内存不足提示
- 桌面图标/应用无响应

**诊断：**
```bash
systemctl is-active systemd-oomd    # 返回 'active' = 该服务在跑
systemctl is-enabled systemd-oomd   # 返回 'enabled' = 开机自启
# 查看 oomd 日志
journalctl -u systemd-oomd --since "5 minutes ago" | grep -i "killed\|memory\|score"
```

**根治（以优先级排序）：**
```bash
# ① 立即停止（当前进程）:
sudo systemctl stop systemd-oomd

# ② 禁止开机自启:
sudo systemctl disable systemd-oomd

# ③ 彻底锁死（防止 socket 激活重新拉起）:
sudo systemctl mask systemd-oomd

# ④ 释放文件缓存:
sudo sync && sudo sysctl -w vm.drop_caches=3
```

**验证：**
```bash
systemctl is-active systemd-oomd  # 应返回 'inactive'
systemctl status systemd-oomd     # 应显示 disabled + dead
```

**用户一键修复脚本（已在桌面）：** `~/桌面/修复卡死.sh` — 双击→终端运行→输入密码，包含 stop + disable + mask + 清缓存。

---

### 故障2: 青山VPN(QingShan)崩溃后系统代理残留

**现象：** 国内网站（百度、QQ等）完全打不开，国外网站能开。系统感觉卡顿。用户描述"上次卡成这样就是青山VPN"。

**原因：** VPN 进程崩溃后，GNOME 系统代理仍指向 `127.0.0.1:9674`（一个已经不存在的本地代理）。所有 HTTP/HTTPS 流量走这个死端口，国内网站超时。

**诊断：**
```bash
gsettings get org.gnome.system.proxy mode
# 返回 'manual' = 代理残留
gsettings get org.gnome.system.proxy.http host
# 通常返回 '127.0.0.1'
gsettings get org.gnome.system.proxy.http port
# 通常返回 9674
```

**修复：**
```bash
gsettings set org.gnome.system.proxy mode 'none'
```

**验证：**
```bash
gsettings get org.gnome.system.proxy mode  # 应返回 'none'
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://www.baidu.com
# 应返回 200（之前超时）
```

---

### 故障3: Gnome 桌面进程崩溃（桌面冻结/鼠标不动）

**现象：** 屏幕静止，鼠标不能动/部分能动但桌面无响应。Win键和Alt+F2都没反应。

**原因：** gnome-shell 进程死锁或崩溃。

**从远程终端修复（root/SSH）：**
```bash
# 温和重启（发送 SIGUSR1 信号，systemd 自动重启）:
killall -3 gnome-shell

# 强制重启（如果上面没反应）:
killall -9 gnome-shell

# 验证重启成功:
pgrep gnome-shell
```

**注意：** 5-10 秒后 gnome-shell 会被 systemd 自动拉起，桌面恢复。用户无需重新登录。

---

### 故障4: 大内存进程拖垮 7.1GB 系统（Ivy Bridge 专用）

**现象：** 系统变慢/卡死，交换分区被大量使用。

**典型占内存大户：**
| 进程 | 典型内存占用 | 是否为必需 |
|:----|:-----------|:----------|
| hindsight-api (向量库 daemon) | 824MB | ❌ 按需启动，不自动跑 |
| Chrome 主进程 | 470MB | ✅ 用户在用 |
| Chrome renderer (多个) | 每个~280-820KB 但累积大 | ✅ |
| OpenClaw gateway (Node.js) | 180-280MB | ⚠️ 可能需要，但空闲时可杀 |

**快速释放：**
```bash
# 杀 hindsight-api（最大内存杀手）
kill -9 $(pgrep -f hindsight-api) 2>/dev/null

# 杀 OpenClaw gateway（非必须时）
kill -9 $(pgrep -f "openclaw.*gateway") 2>/dev/null

# 清理 docker 容器内存
docker stop $(docker ps -q) 2>/dev/null
```

**最佳实践（已配置）:**
- hindsight-api 改为 `local_embedded` 模式（不跑 daemon，按需加载）
- OpenClaw gateway 开机自启但在空闲时不会自动吃额外内存
- Docker 容器（miniflux+postgres+videocaptioner）设 restart=always 但内存占用小

---

### 故障5: Miniflux Docker 容器重启后未自动启动

**现象：** 电脑重启后 RSS 聚合器不可用（`http://localhost:8080` 打不开）。

**诊断：**
```bash
docker ps --filter name=miniflux --format "table {{.Names}}\t{{.Status}}"
```

**修复：**
```bash
docker start miniflux-db miniflux
docker update --restart=always miniflux-db miniflux
```

**验证：** 浏览器打开 `http://localhost:8080`，用 admin / admin123 登录。

---

## Obsidian 知识库搭建

详见 `references/obsidian-vault-setup.md`
- ⚠️ 符号链接指向库外→Obsidian不显示文件内容（必须物理拷贝）
- ⚠️ L1用硬链接（`ln`无`-s`）→改Obsidian=改源文件
- ⚠️ .desktop 文件在GNOME需标记可执行

## 🖥️ 全盘对拷（OS整盘克隆）指南

当用户问「全盘对拷」或「进P1还是用什么工具」，这是整盘克隆方案对比：

### 场景判断

| 场景 | 推荐工具 | 理由 |
|:----|:--------|:-----|
| **同一台电脑换硬盘**（旧SSD→新SSD） | Clonezilla (disk-to-disk) | 块级拷贝，快，只复制已用空间 |
| **搬到另一台电脑，硬件不同** | Hermes记忆备份 + 新机重装系统 | 整盘克隆会导致驱动冲突/无法启动 |
| **备份到外部硬盘（冷备）** | Clonezilla (disk-to-image) | 压缩存储，可还原到同样硬盘 |
| **只想带走Hermes环境** | `一键全记忆备份.sh` | 最快，跨硬件兼容 |

### Clonezilla 推荐（整盘克隆首选）

- ✅ 比 dd 快 10 倍（只复制已用扇区）  
- ✅ 支持 disk-to-disk 和 disk-to-image  
- ✅ 内置校验（可选）  
- ⚠️ 必须装到 U 盘启动，不能在运行系统中克隆当前盘  

### 操作步骤（disk-to-disk 模式）

1. 下载 Clonezilla ISO → 用 Rufus/Ventoy 写进 U 盘  
2. 插 U 盘、插目标盘 → 重启进 BIOS → 从 U 盘启动  
3. 选 `Clonezilla live` → `device-device` → `disk_to_local_disk`  
4. 选源盘（当前系统盘）→ 选目标盘（新硬盘）  
5. **确认目标盘容量 ≥ 源盘已用空间**（不一定需要总容量更大，只要装得下数据）  
6. 开始克隆 → 完成后关机 → 拔掉旧盘 → 从新盘启动  

### 风险与注意事项（必须告诉用户）

- **目标盘数据全部清空** — 确保没有重要文件  
- **跨硬件不兼容** — 换不同型号电脑克隆后可能蓝屏/无法启动（驱动不同）  
- **NVMe → SATA 或反之** — 可能需要重建 initramfs  
- **时间较长** — 250GB/已用 100GB ≈ 15-30 分钟（取决于接口速度）  
- **Clonezilla 不会自动扩容分区** — 如果目标盘比源盘大，需要手动 `resize` 或用 gparted  

### "P1" 说明

如果「P1」指第一个分区手动拷文件 → 不推荐。手动拷文件不能恢复引导区、分区表、权限和隐藏系统文件。用 Clonezilla 一劳永逸。

## 计划事项

### ☁️ 自动上传备份到云盘（优先级: 等待第1步验证通过）

详见 SKILL.md 中的 ☁️ 计划增强 一节。

### ❌ 2026-05-21 更正：本地Git不够，必须云端（GitHub）

**血泪教训：** 之前我写"不搞push/pull/在线同步（徒增不稳定节点）"——这个结论是错的。
用户亲自纠正：**本地Git ≠ 反脆弱。A死了B要能恢复，必须推上云端。**

正确架构：
```bash
A机器（工作机）:
  external_memory/ (Git仓库)
    │ 每30分钟自动commit (本地)
    │ 每30分钟自动 push → GitHub
    ▼
GitHub私有仓库（永远在线）
    │
    ▼
B机器（克隆盘，柜子里）:
  启动后 git pull → 拿到A最后一版
  → 系统完好，技能/记忆/INDEX.md全部最新
```

| 方案 | 反脆弱？ | 说明 |
|:----|:--------|:-----|
| ❌ 本地Git + U盘拷贝 | ❌ A死了，B拿不到新东西 | "徒增不稳定节点" |
| ✅ **GitHub自动push** | ✅ A死了，B随时pull | 用户认可的真正反脆弱 |

GitHub私有仓库（免费，无广告）是最简单可靠的云端方案。
详见 `references/github-auto-sync.md`（配置步骤）。

### 🧩 双实例同步边界（2026-05-22 新增）

**用户问：** 「我用了你，又用了你的一个副本，两边记忆部分相同、部分不同，可以合并吧？」

**核心答案：外部知识库能Git合并，内部状态不能合并。** 正确玩法是主备模式，不是双活。

| 数据类型 | 路径 | 双活可行？ | 原因 |
|:--------|:-----|:----------|:-----|
| 📄 L3外部MD | `external_memory/` | ✅ Git合并 | Git三路合并，极少数冲突需人工 |
| 🏗️ 技能 | `skills/` | ✅ Git合并 | 同上 |
| 🧠 L1内部记忆 | `~/.hermes/memories/` | ❌ | SQLite state.db 独占锁定 |
| 🧬 L2向量库 | `~/.pg0/` | ❌ | PostgreSQL单实例独占 |
| 💬 历史会话 | `state.db` | ❌ | SQLite 不支持并发写 |

**正确做法：**
```
A盘（工作机）日常用  → 每30分 push external_memory → GitHub
B盘（克隆冷备）       → 插上电启动 → git pull 拿最新外部记忆
                    → A崩了取代A，A好了冷备回去
```

❌ **不要两台同时跑并同时push** — state.db不能合并，两边买的基金/改的概率可能不一致。
如果要共享state.db：停A → 同步state.db到B → 启动B。（已讨论但未实现，复杂度高）。

详见 `references/git-sync-clone.md`

### 待印证事项

详见 `~/桌面/待印证-云端共享记忆与闲鱼代装.md`

1. **云端共享记忆** — 多台电脑共享同一套记忆
   - 方案：停服→同步文件→重启
   - 工具：Syncthing/坚果云/OneDrive
   - 问题：state.db 不支持并发写，需停服同步

2. **闲鱼代装交付流程** — 硬盘对拷 vs 远程部署
   - 需开发「初始化脚本」清隐私生成纯净模板
   - 不同硬件驱动兼容性待验证
   - 客户首次启动流程待设计

## Pitfalls

### ⚠️ 隐藏路径陷阱（2026-05-15 用户反复纠正直到彻底修好）

**现象：** 用户双击tar.gz备份文件，解压后只看到两个txt文件，以为备份是空的。

**原因：** 备份把文件存在 `.hermes/` 和 `.pg0/` 下（点开头隐藏目录），GUI文件管理器默认不显示。用户看不到实际文件。

**修复历程（三次才修对）：**

| 次 | 做法 | 用户反应 |
|:--|:-----|:---------|
| 1 | 加README.txt + 恢复说明.txt在tar.gz顶层 | "我只看到两个txt，备份文件在哪？" |
| 2 | README里写".hermes是隐藏文件夹按Ctrl+H显示" | "给AI看的还是给人看的？人看到两个txt文件就觉得是空的" |
| 3 | 彻底改为可见文件夹名 `Hermes备份_/`，包内不用任何点开头路径 | ✅ 用户满意 |

**铁律：** 备份包内**绝对不要使用点开头（隐藏）目录**。所有文件放在 `Hermes备份_日期/` 这样的可见文件夹下，GUI打开就能看到全部内容。

**脚本实现示例（一键全记忆备份.sh）：**
```bash
WORKDIR="$TMPDIR/Hermes备份_${DATE}"  # 可见文件夹名
mkdir -p "$WORKDIR"
cp "$HOME/.hermes/config.yaml" "$WORKDIR/config.yaml"  # 可见文件名
cp "$HOME/.hermes/.env" "$WORKDIR/api密钥.env"         # 重命名为中文可见名
# ... 所有文件复制到 WORKDIR
cd "$TMPDIR"
tar czf "$FILE" "$(basename "$WORKDIR")"  # 打包可见文件夹
```

用户反馈旧版 `全记忆备份.sh` （已归档）运行时终端一片空白，用户不知道它在干什么。

**教训：** 任何用户双击运行/一键执行的脚本，必须有清晰的**分步输出**：
1. 每一步用 `echo ">>> 第N步：做什么..."` 加 `sleep 1` 让用户看到进度
2. 最终结果用醒目格式（边框/颜色）展示
3. 末尾必须有 `按 ENTER 键退出...`，否则终端闪退用户什么都看不到

新版 `一键全记忆备份.sh` 已按此标准重写。

### ⚠️ 硬链接恢复陷阱（2026-05-15）

**背景：** L1_MEMORY.md 现在用**硬链接**（`ln` 不是 `ln -s`）连接到知识库目录。硬链接不占额外空间，改写Obsidian=改写源文件。

**备份影响：** `tar` 默认处理硬链接正确——同一inode只存一份内容，解压时重建硬链接。无需额外处理。

**恢复后验证：**
```bash
# 检查L1是否为硬链接（Links: 2 说明恢复正确）
stat ~/.hermes/hermes-knowledge/L1_MEMORY.md | grep Links
# 期望输出：Links: 2

stat ~/.hermes/memories/MEMORY.md | grep Links
# 期望输出：Links: 2（同一个inode）
```

如果 Links=1 说明硬链接断裂 → 重新执行 `ln -f ~/.hermes/memories/MEMORY.md ~/.hermes/hermes-knowledge/L1_MEMORY.md`

### ⚠️ 备份文件名时间戳不一致（2026-05-17 发现）

**现象：** 用户记得一个时间戳（如 `203041` = 20:30:41），但桌面上实际有效备份文件是更晚的时间戳（如 `220017` = 22:00:17），中间还残留不完整文件（如 `215721.tar.` — 无.gz后缀）。

**原因：** 备份脚本在打包过程中失败/中断（原因：磁盘空间不足、进程被杀、终端关闭），留下不完整 `.tar.` 文件 → 用户手动重跑 → 生成新的时间戳。

**处理原则：**
1. 取**最大的时间戳**且完整（`.tar.gz` 后缀）的为有效备份
2. 不带 `.gz` 后缀或 `.tar.` 结尾的是失败产物，可安全删除
3. 用户记忆中较早的时间戳是首次尝试失败的时间点，不要按图索骥

**验证命令：**
```bash
# 列出所有备份相关文件，按时间排序
ls -lh ~/桌面/hermes-backup* 2>/dev/null
# 只保留最大的 .tar.gz，删除残余的 .tar. 文件
rm -f ~/桌面/hermes-backup-*.tar. 2>/dev/null
```
```bash
# 终端查看内容
tar tzf hermes-backup-*.tar.gz | head -20

# 解压到指定目录（显示隐藏文件）
cd ~ && tar xzf ~/桌面/hermes-backup-*.tar.gz
# 然后按 Ctrl+H 显示隐藏文件
```

旧版 `全记忆备份.sh`（已归档）有 4 个盲区，新版 `一键全记忆备份.sh` 已全部修复：

| 盲区 | 路径 | 旧版 | 新版 |
|:----|:-----|:----|:----|
| L1 内部记忆 | `~/.hermes/memories/` | ❌ | ✅ |
| L2 向量库 | `~/.pg0/` | ✅ (但需先停hindsight) | ✅ |
| API密钥 | `~/.hermes/.env` | ❌ 严重遗漏 | ✅ **已修复** |
| 桌面脚本 | `~/桌面/一键全记忆备份.sh` | ❌ 旧版硬编码列表 | ✅ 脚本自身在包外，手动保
| 🟡 **Pinchtab自启配置** | `~/.config/autostart/pinchtab.desktop` | 开机自动启动Pinchtab |
| 🟡 **RTK二进制** | `~/.local/bin/rtk` | Rust Token Killer终端过滤工具，备份不带走 |
| 🟡 **RTK源码** | `~/rtk/` | Rust项目源码，需重编译才能恢复 |
| 🟢 **Rust工具链** | `snap安装，全局有效` | 恢复后需 `sudo snap install rustup --classic && rustup default stable` 重装 |
| 🟡 **桌面非.sh文件** | `~/桌面/*.txt` 等 | Hermes模型切换-恢复指南.txt 不在备份范围内 |

**恢复后必须手动执行的补漏命令：**
```bash
cp /U盘路径/.env ~/.hermes/.env
cp -r /U盘路径/scripts/* ~/.hermes/scripts/
cp /U盘路径/douyin_state.json ~/.hermes/
cp /U盘路径/check_api_balance.sh ~/桌面/
cp /U盘路径/Hermes模型切换-恢复指南.txt ~/桌面/
```

**✅ 备份脚本自动生成的 `恢复清单_日期.txt` 已完整记录上述盲区，打开即有恢复指引。** 详见 `~/.hermes/external_memory/08-系统变更与备份盲区手册.md`（完整恢复流程，找别的AI帮忙恢复时给它看这个文件）。

### 自定义工具备份盲区

以下自定义工具不在备份脚本覆盖范围内（详见 `references/rtk-token-killer.md` 和 `references/pinchtab-setup.md`）：
- **Pinchtab**（浏览器自动化）— 需重新下载二进制并编译
- **RTK**（Rust Token Killer，终端噪音过滤）— 需Rust工具链，源码在 `~/rtk/`，需要重新编译
- **chat-relay.sh**（模型路由转发脚本）— 在 `~/.hermes/scripts/`，不会被备份带走

**当前备份位置（2026-05-15）：** `D:\\Hermes-OpenClaw备份\\`
  - `全记忆备份_2026-05-14.tar.gz` — 17MB，备份脚本自动生成的
  - `手动补漏\\` — .env（API Key）、scripts/（抖音监控）、桌面工具
  - 恢复时两个文件夹都需要用到，先跑恢复脚本再手动补漏

**D盘扩容（2026-05-15）：** 从285G扩到334G（Windows磁盘管理→扩展卷操作）
  - ✅ Windows内置操作，安全无数据丢失
  - ⚠️ 切勿在Linux下用 parted/ntfsresize 做NTFS分区扩容

### ⚠️ 双系统NTFS分区扩容警告

如果Hermes装在移动硬盘上，笔记本电脑内置硬盘有Windows系统，扩展NTFS分区需特别注意：

| 操作方式 | 安全性 | 说明 |
|:--------|:------|:-----|
| ✅ **Windows磁盘管理 → 扩展卷** | 安全 | Windows原生工具，对NTFS友好，不丢数据 |
| ❌ Linux下 `parted resizepart` + `ntfsresize` | 高风险 | 如果中间断连或断电，D盘文件系统可能损坏，数据丢失 |

**铁律：** 只要涉及双系统（Windows+Linux）的NTFS分区操作，一律进Windows做。Linux下做NTFS分区扩容风险太高，尤其远程操作中断不可控。

### ⚠️ Skills已精简（重要）
2026-05-13 移除了16个不用的Skills分类（~60个Skills），备份在 `~/.hermes/skills_backup/`。如果日后需要某个技能：
- 从 `~/.hermes/skills_backup/` 移回 `~/.hermes/skills/` 即可
- 备份脚本的 `skills/` 只打包保留的Skills，备份目录里的不会自动带走

### ⚠️ 备份脚本常见问题
- 目标路径不能带末尾斜杠（已自动处理 `DEST="${DEST%/}"`）
- 备份脚本自身的文件名必须是 `全记忆备份.sh`，**不要改名**，否则备份时不会把自己打进包里（已修复：硬编码文件名代替 `$0`）
- gzip 完文件后必须 `mv` 到目标目录（已修复：之前 gzip 完忘了挪文件，验证时会报错）
- 如果备份了但不定期验证——验证一次花不了1分钟
- 桌面脚本路径依赖中文系统 `~/桌面/`，英文 Ubuntu 需改为 `~/Desktop/`
- **🔴 桌面脚本列表是硬编码的（第125-128行）** — 新增脚本（如 `check_api_balance.sh`）不会自动进备份包。每次创建新桌面脚本后，记得加进这个列表
- **🔴 `~/.hermes/.env` 不在备份范围内** — 所有API Key（DeepSeek/阿里云/微信网关）都在此文件，备份不带走。恢复后必须手动复制
- **🔴 `~/.hermes/scripts/` 不在备份范围内** — douyin-monitor.py等自定义脚本丢失。建议加进tar命令或单独保存

### ⚠️ 两套cron冗余（Hermes cronjob + 系统crontab并存）

当前存在两套自动commit机制：

| 哪套 | 位置 | 行为 |
|:----|:----|:----|
| 🔵 **Hermes cronjob** `外部记忆自动存档` | taskmaster 定时任务 | 每30分git add + commit（**仅本地，无push**） |
| 🔴 **系统crontab** | `crontab -l` | 每30分git add + commit + **push到GitHub** |

**现状：** 两套都在跑，Hermes的只commit不push，纯粹冗余。但如果要改同步方案，**必须两个都改**（或者直接删掉Hermes的，只留系统crontab）。多数关于push的排查最终要查`crontab -l`而非Hermes cronjobs。

### ⚠️ 整盘克隆后不需要恢复备份（2026-05-21 用户纠正）

**正确认知：** Clonezilla 整盘对拷后，新硬盘就是一个**完全相同**的系统。你从新盘启动，Hermes已经在上面了。**不需要再跑恢复脚本/解压备份包。**

**唯一需要做的事：** 把根分区 `resize` 撑满新硬盘剩余空间。

```bash
# 新盘启动后，检查分区
lsblk
# 假设新盘是/dev/sda2，resize根分区
sudo resize2fs /dev/sda2
```

**错误做法（本会话踩坑）：** 我说「克隆完新盘启动→然后我来恢复备份」——用户立刻纠正：整盘克隆后系统一模一样，恢复备份多此一举。备份包只在「克隆失败/新盘起不来」时才救命，正常走克隆用不上。

**提问时的正确回答流程：**
1. 用户问「新硬盘插上了你能帮我搞吗」
2. 先检查 `lsblk` 确认硬盘是否被系统识别
3. 如果识别到了：说明我只能在**当前系统**下做软件操作（分区/格式化/复制文件）
4. 如果是想**换系统盘**：需要用 Clonezilla PE 环境整盘对拷，我做不了（需要物理重启进PE）
5. 如果用户问克隆后流程：正确回答是「克隆完→从新盘启动→resize根分区」，不是「克隆完→恢复备份」

### ⚠️ 提醒频率：用户要求"每隔几天，不是天天"

用户原话："我没有说我搞完之前就一直提醒我，每隔几天提醒一次，不要天天提醒"

设置任何提醒类定时任务时：
- 频率用 **every 3 days** 或 **每3天**，不要 daily
- 只有紧急/时效性强的事才能设每天提醒（如水电费缴费日）
- 常规待办（注册账号、改配置、做备份）一律每3天
- Tailscale 首次开需要浏览器登录验证（客户需按照提示操作）
- 装完记得把客户机的 Tailscale 加到大好人的 Tailscale 网络里（`tailscale up` 时的登录账号决定归属）
- 不要在生产客户机上测试，先在自己虚拟机跑通
