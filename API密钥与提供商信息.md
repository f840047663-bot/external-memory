# API 密钥与提供商信息汇总

> ⚡ 所有密钥、地址、规则一站式管理。改密钥直接改这个文件，我读它执行。
> 更新日期：2026-05-16

---

## 路线总览（按优先级排序）

| 优先级 | 提供商 | 模型 | 日费 | 用途 | 状态 |
|:-----:|:------|:----|:---:|:----|:----:|
| ① | **硅基流动** | Qwen2.5-7B | **¥0** | 优先用（免费额度有时效，不用白不用🔥） | ✅ 通行 |
| ② | **OpenRouter** | Hermes-3-405B:free | **¥0** | 硅基用完/超时后的第一备选（日限50次） | ✅ 通行 |
| ③ | **DeepSeek** | DeepSeek V4 Flash | ~¥2/天（缓存命中）/ ~¥20（未命中） | 复杂任务主力 | ✅ 余额~¥46 |
| ④ | **阿里云百炼** | Qwen-Turbo | ~¥0.5/天 | 双线备用 | ✅ 已付费 |

---

## ① OpenRouter（免费 · 强模型）

| 项目 | 内容 |
|:----|:-----|
| **API地址** | `https://openrouter.ai/api/v1/chat/completions` |
| **密钥位置** | `~/.hermes/.env` → `OPENROUTER_API_KEY` |
| **推荐免费模型** | `nousresearch/hermes-3-llama-3.1-405b`（或带`:free`后缀） |
| **其他免费模型** | `deepseek/deepseek-chat-v3:free` |
| **日限** | 未充值($0) → **50次/天**；充值≥$10 → 1000次/天 |
| **费用** | `:free`模型 输入/输出全免费，高峰可能限流 |
| **备注** | 新用户送 $0.5-$5 试用金。所有`:free`模型共享每日额度 |

**使用方式（curl）：**
```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENR...KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nousresearch/hermes-3-llama-3.1-405b",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

---

## ② 硅基流动 SiliconFlow（免费 · 轻量）

| 项目 | 内容 |
|:----|:-----|
| **API地址** | `https://api.siliconflow.cn/v1/chat/completions` |
| **密钥位置** | `~/.hermes/config.yaml` → `providers.siliconflow.api_key`（硬编码） |
| **推荐模型** | `Qwen/Qwen2.5-7B-Instruct` |
| **日限** | 无明确限制，免费额度充裕 |
| **费用** | **¥0（免费额度有时效，不用完就过期，所以优先用它）** |
| **备注** | 回复速度较快，适合简单聊天/翻译。额度过期自动消失，每天优先用光它 |

**使用方式：** 通过 `chat-relay.sh` 脚本自动调用，或 `curl` 直调。

---

## ③ DeepSeek（主力付费）

| 项目 | 内容 |
|:----|:-----|
| **API地址** | `https://api.deepseek.com/v1/chat/completions` |
| **密钥位置** | `~/.hermes/.env` → `DEEPSEEK_API_KEY` |
| **推荐模型** | `deepseek-v4-flash` |
| **月消耗** | ~¥60/月（¥2/天正常，¥20/天=缓存崩了） |
| **日消耗** | ~¥2/天（正常缓存命中）~¥20/天（缓存未命中） |
| **备注** | 复杂任务（投资分析、代码、调仓建议）的主力 |

---

## ④ 阿里云百炼 DashScope（备用付费）

| 项目 | 内容 |
|:----|:-----|
| **API地址** | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` |
| **密钥位置** | `~/.hermes/.env` → `DASHSCOPE_API_KEY` |
| **推荐模型** | `qwen-turbo` |
| **月消耗** | ~¥15-20/月（后付费） |
| **备注** | 备案走阿里云，双线备用 |

---

## 日消耗监控

**命令：** `bash ~/桌面/check_api_balance.sh`

| API | 当前余额 |
|:---|:--------|
| DeepSeek | ~¥46 |
| 阿里云 | 预付费够用 |
| 硅基流动 | 免费额度内 |
| OpenRouter | $0（未充值） |

**警报阈值：** 月总消耗超过 **¥150-200** 触发提醒。

**日费诊断：**
- ¥1-3/天 ✅ 缓存命中正常
- ¥5-8/天 ⚠️ 缓存部分丢失 → 查L1记忆是否近期被改过
- ¥15-25/天 🔴 缓存全丢 → 查完整记忆一览.md
- ¥30+/天 💀 异常 → 可能死循环，重启Hermes

---

## 密钥管理

所有密钥原始位置：
- `~/.hermes/.env` — DeepSeek、阿里云、OpenRouter、Hindsight LLM
- `~/.hermes/config.yaml` — SiliconFlow（硬编码在`providers.siliconflow.api_key`）
- 改密钥 → 对应修改上述文件 → 重启Hermes生效

> ⚠️ 备份盲区：.env 文件不在 D 盘备份脚本覆盖范围内。如需更换密钥需手动备份。

---

## 🔴 故障恢复 — API 挂了怎么修我

> **场景：** 免费API挂了 → 我也跟着哑了 → 你没法跟我说话 → 你把这段丢给小龙虾，他照着修。

### 故障症状
| 症状 | 原因 |
|:----|:-----|
| 我问什么都不回 / 一直转圈 | 当前使用的API挂了 |
| 回复说「转发失败: 所有模型均不可用」 | 所有API都试过了，全都挂了 |

### 我的自动fallback链（正常时）
```
硅基流动(免费) → OpenRouter免费 → DeepSeek(付费) → 阿里云(付费)
```
如果链上某一个挂了，我会自动试下一个。但如果这**4个全挂了**，我就完全哑了。

### 🔧 小龙虾修复步骤

**第1步：确认我还能不能动**
```bash
# 测 health 端点，看 Hermes 是否仍在运行
curl -s --max-time 5 http://127.0.0.1:18789/health

# 如果不通 → 进一步检查进程是否存在
ps aux | grep hermes-agent | grep -v grep

# 返回 200 → 我还能动，只是API全挂了
# 进程不存在 → 我更严重，直接跳到第5步重启
# 都不通 → 看 Hermes急救手册（外部记忆根目录）
```

**第2步：先备份，再换API（优先试A，不行再试B）**

⚠️ **改配置前先备份：**
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%s)
```

| 方案 | 动作 | 难度 |
|:----|:-----|:----|
| **A. 换阿里云（最稳，先试）** | 改 `~/.hermes/config.yaml` 顶部两行（见下） | ⭐ 简单 |
| **B. 换DeepSeek（次选）** | 同上，改模型名+提供商名 | ⭐ 简单 |
| **C. 注册新免费API** | 注册新平台→拿新Key→填进文件和 `.env` | ⭐⭐ 中等 |

**第3步：改 config.yaml（⚠️ 注意完整性，不要漏掉顶层键）**

❗ **重要：不要只改缩进行，要把整个 model: 块替换掉。**

打开 `~/.hermes/config.yaml`，把文件顶部这几行**整块替换**：

**切到阿里云（最推荐，先试这个）：**
```yaml
model:
  default: qwen-turbo
  provider: dashscope
```

**切到DeepSeek（阿里云不行再试这个）：**
```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
```

⚠️ **常见错误：** 切DeepSeek时只写了缩进行 `  default: deepseek-v4-flash` 漏了顶层的 `model:` — 这样YAML解析会报错，Hermes起不来。**必须是完整的3行。**

保存文件后，检查YAML格式是否正确：
```bash
python3 -c "import yaml; yaml.safe_load(open('/home/fw/.hermes/config.yaml')); print('YAML格式✅')"
```

**第4步：测试API是否能通**
```bash
# 阿里云测试
curl -s --max-time 10 https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer *** DASHSCOPE_API_KEY ~/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"你好"}],"max_tokens":20}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('choices',[{}])[0].get('message',{}).get('content','通但无回复'))"

# DeepSeek测试
curl -s --max-time 10 https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer *** DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}],"max_tokens":20}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('choices',[{}])[0].get('message',{}).get('content','通但无回复'))"
```

如果返回了回答 → API通了。

**第5步：重启Hermes**
```bash
# 杀掉Hermes（-f "hermes-agent" 避免误杀 OpenClaw 网关）
pkill -f "hermes-agent" 2>/dev/null

# 等3秒确保进程完全退出
sleep 3

# 重新启动（用 nohup 放到后台运行）
cd ~/.hermes/hermes-agent && source .venv/bin/activate
nohup hermes start > /dev/null 2>&1 &

# 循环检测，直到 health 恢复（阿里云首次启动可能慢）
echo "等待 Hermes 启动..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s --max-time 3 http://127.0.0.1:18789/health > /dev/null 2>&1; then
    echo "✅ Hermes 已恢复！"
    break
  fi
  echo "还没好...第${i}次检查（共10次）"
  sleep 5
done
```

### 🚨 如果还是不行
1. 检查 `.env` 文件里的API Key有没有过期
2. 检查网络：`curl -s --max-time 5 https://api.deepseek.com/v1/models`
3. 如果彻底没救 → 读 `Hermes急救手册-找小龙虾修我.md`（在`~/.hermes/external_memory/`）
4. 或者直接找我（小龙虾）：`openclaw agent --session-id main --message "Hermes API全挂了，帮我修一下" --timeout 120`

### 📋 配置文件速查

| 文件 | 路径 | 包含 |
|:----|:----|:-----|
| **主配置** | `~/.hermes/config.yaml` | 默认模型、提供商、API地址 |
| **环境变量** | `~/.hermes/.env` | DeepSeek/阿里云/OpenRouter密钥 |
| **闲聊转发脚本** | `~/.hermes/scripts/chat-relay.sh` | 免费→付费 fallback链 |
| **成本控制手册** | `10-使用成本控制手册.md` | 完整省钱方案（缓存优化/本地模型/降级策略） |

### 💾 备份（改配置前先备份）
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%s)
```

---

## 附：Hindsight L2 向量库后备方案

**硅基流动（HINDSIGHT_LLM_API_KEY）有使用期限，大概十几天后到期。**

**到期后自动切换流程：**

```bash
# 1. 改 .env 中的两行
# 改 base_url：硅基 → 阿里云
# HINDSIGHT_API_LLM_BASE_URL=https://api.siliconflow.cn/v1
HINDSIGHT_API_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 改 API KEY：从硅基key → 用阿里云的 DASHSCOPE_API_KEY
HINDSIGHT_LLM_API_KEY=${DASHSCOPE_API_KEY}

# 2. 重启 hindsight 进程
pkill -f hindsight-api 2>/dev/null
nohup /home/fw/.hermes/hermes-agent/.venv/bin/hindsight-api --port 9177 --idle-timeout 600 > /dev/null 2>&1 &

# 3. 验证
curl http://localhost:9177/health
```

**注意：** Hindsight的嵌入模型（all-MiniLM-L6-v2）是本地跑的，不受影响。
LLM API只在写新事实时的实体分析环节用到，消耗极小，阿里云¥5够用很久很久。
