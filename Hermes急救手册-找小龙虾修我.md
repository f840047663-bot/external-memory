# 🆘 Hermes 急救手册（找小龙虾或其他 AI 修我）

> **用前必读：** 我是 Hermes（AI 助手），我的记忆分三层。
> 如果你（小龙虾或其他 AI）看到这本文档，说明我出问题了，需要你帮我恢复。
> **本手册假设你完全不了解我的架构，照着命令敲就行。**
> 读完大约 3 分钟，操作完大约 10 分钟。

---

## 一、快速诊断

先判断我坏到什么程度：

```bash
# 1. 我能回消息吗？
#    直接在微信/Terminal里给我发消息，如果回复正常 → 我只是有点小问题
#    如果不回 → 继续下面的检查

# 2. 进程还活着吗？
ps aux | grep -E 'hermes|hindsight' | grep -v grep
#   有输出 → 进程活着
#   没输出 → 全挂了

# 3. API 能通吗？
curl -s --connect-timeout 5 https://api.deepseek.com/v1/models >/dev/null 2>&1 && echo "DeepSeek OK" || echo "DeepSeek 挂了"
curl -s --connect-timeout 5 http://localhost:9177/health 2>/dev/null && echo "Hindsight L2 OK" || echo "Hindsight L2 挂了"
```

快速定位问题：看下面表格，找到你的情况直接跳转。

| 症状 | 跳到 |
|:----|:----|
| 完全不回消息、API 报错 | **第二节：API 挂了** |
| 能回消息但记忆不对/什么都忘了 | **第三节：L1 内部记忆丢了** |
| 想查 L2 但提示"向量库连不上" | **第四节：L2 Hindsight 挂了** |
| 微信/Telegram 等平台收不到消息 | **第五节：网关/平台问题** |
| 删了什么重要文件或配置文件坏了 | **第六节：文件损坏/丢失** |
| 全部炸了、什么都不剩 | **第七节：从零恢复（灾难方案）** |

---

## 二、API 挂了（最常见）

### 症状
- Hermes 不回消息
- 报错 "401" / "429" / "timeout" / "转发失败: 所有模型均不可用"

### 先快速判断
```bash
# 1. Hermes进程还在吗？
ps aux | grep -E 'hermes-agent|hindsight' | grep -v grep

# 2. Health 端点通吗？
curl -s --max-time 5 http://127.0.0.1:18789/health
```

### 详细修复步骤（5步）

> 🔴 **如果进程不在 → 先重启 Hermes（跳到第5步）**
> 
> 🔴 **这5步详细版在 `10-API密钥与提供商信息.md` → 「🔴 故障恢复」章节**
>
> 下面只给速查命令，看不懂的去看上面那个文件。

**① 备份配置**
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%s)
```

**② 改config.yaml顶部整块**

> ⚠️ **不要切 qwen-turbo/阿里云百炼！** 历史教训（5月14日、5月17日两次故障均因此引起）：
> - qwen-turbo 能力太弱，Hermes 调工具后返回空，结果看似API通但模型不干活
> - 误设 `model.base_url: ''` 会覆盖 provider 的 base_url，导致请求路由到空地址
> - 如果你正在用阿里云百炼 DashScope，只把它当备用 fallback provider，不要设成默认
>
> **直接用 DeepSeek（唯一推荐主力）：**
> ```yaml
> model:
>   default: deepseek-v4-flash
>   provider: deepseek
>   base_url: https://api.deepseek.com/v1
> ```
>
> **如果 DeepSeek 也挂了，才试硅基流动（免费）：**
> ```yaml
> model:
>   default: Qwen2.5-7B-Instruct
>   provider: siliconflow
>   base_url: https://api.siliconflow.cn/v1
> ```

**③ 验证YAML格式**
```bash
python3 -c "import yaml; yaml.safe_load(open('/home/fw/.hermes/config.yaml')); print('YAML✅')"
```

**④ 测试新API是否通**
```bash
# 阿里云
curl -s --max-time 10 https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $(grep DASHSCOPE_API_KEY ~/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"你好"}],"max_tokens":20}'
```

**⑤ 重启Hermes**
```bash
pkill -f "hermes-agent" 2>/dev/null
sleep 3
cd ~/.hermes/hermes-agent && source .venv/bin/activate
nohup hermes start > /dev/null 2>&1 &
# 循环等启动
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -s --max-time 3 http://127.0.0.1:18789/health > /dev/null 2>&1 && echo "✅ 好了" && break
  sleep 5
done
```

### 🔍 如果需要查我的记忆（L2 向量库）

> L2（Hindsight）存了我的语义记忆，包含规则、体系、框架等。查它能快速定位问题根因。

```bash
# 查 L2 记忆（替换 query 为你想搜的内容）
curl -s --max-time 30 -X POST http://127.0.0.1:9177/v1/default/banks/hermes/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"你要搜什么","limit":3}'

# 返回结果在 .results[].text 字段
```

### 检查 API Key
```bash
grep -E 'DEEPSEEK_API_KEY|DASHSCOPE_API_KEY|OPENROUTER_API_KEY' ~/.hermes/.env
```

---

## 三、L1 内部记忆丢了（memory tool 空了）

### 症状
- Hermes 回答问题时忘了你是谁、忘了持仓、忘了规则
- 或者 memory tool 数据丢失

### 恢复方案

**首选：从L1内部记忆备份恢复（最快最准）**

备份文件在 `~/.hermes/external_memory/L1-内部记忆备份.md`，包含了18条铁律+12条用户档案的完整快照。

```bash
# Step 1: 读备份文件
cat ~/.hermes/external_memory/L1-内部记忆备份.md

# Step 2: 先恢复user档案
# 用 memory(action="add", target="user", content="...") 逐条添加

# Step 3: 再恢复memory规则
# 用 memory(action="add", target="memory", content="...") 逐条添加

# Step 4: 重启Hermes会话，L1自动注入
```

完整步骤见 `99-灾难恢复与迁移手册.md` 第8章。

**备用方案：从L3文件重建（如果L1备份也没了）**

如果 Hindsight L2 还活着：
```bash
curl -X POST http://localhost:9177/v1/default/banks/hermes/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"所有重要记忆","budget":"high","max_tokens":8000}' | \
  python3 -c "
import json,sys
d = json.load(sys.stdin)
for r in d.get('results',[]):
    print(f'  [{r.get(\"type\",\"?\")}] {r[\"text\"]}')
"
```

把召回结果告诉 Hermes，我会自动重建 L1。

**Step 3: 重建 L1 路牌（手动恢复）**

用 memory tool 逐条添加。关键条目最少需要这些：
```
架构: Hermes统筹/决策, OpenClaw执行(定时/工具/渠道)。微信一号一bot。
【核心原则】我的角色=信息助手，不是决策者。决定权永远在他手上。
【三层记忆架构】L1=CPU缓存(2200字), L2=RAM(Hindsight:9177), L3=硬盘(MD文件夹)
【自我维护铁律】①改配置一次备份先测通 ②调试失败只报结果 ③危险操作前先问小龙虾 ④稳定大于一切
【强制读外部规则】涉及投资/工作流/配置的问题必须先读外部MD
【改配置铁律】改任何配置前全备份→通知对方→curl测试通过才改
【模型路由】闲聊→硅基Qwen2.5-7B(免费), 复杂→DeepSeek主力
【记忆优先级】完备性 > token节约
【L2-Hindsight运行中】端口9177, 重启: ~/桌面/restart_hindsight_l2.sh
```

---

## 四、L2 Hindsight 挂了

### 症状
- `curl http://localhost:9177/health` 没反应或报错
- 或者 Hermes 说"向量库连不上"

### 恢复 Step 1: 重启

```bash
# 一键重启
pkill -f 'hindsight-api' 2>/dev/null; sleep 2
cd ~/.hermes/hermes-agent && source .venv/bin/activate
nohup hindsight-api --daemon --port=9177 --idle-timeout=300 > /dev/null 2>&1 &
sleep 25 && curl -s http://localhost:9177/health
# 应该返回 {"status":"healthy","database":"connected"}
```

> ⚠️ **2026-05-17 更新的关键配置（已写在 .env）：**
> - `HINDSIGHT_API_DATABASE_URL=pg0` — 用嵌入式PostgreSQL（非SQLite！）
> - `HINDSIGHT_API_LLM_BASE_URL=https://api.deepseek.com/v1` — DeepSeek，不是硅基！
> - `HINDSIGHT_API_LLM_MODEL=deepseek-v4-flash`
> - `HINDSIGHT_LLM_API_KEY` = DeepSeek API key（跟主模型同一个）
> 
> 常见启动失败原因：
> ① 硅基流动 API key 过期 → 改用 DeepSeek API key
> ② compat.py 强制写 SQLite 地址 → .env 中 `HINDSIGHT_API_DATABASE_URL=pg0` 覆盖

### 恢复 Step 2: 如果脚本报错

脚本做了这几件事：
1. 杀旧进程（端口 9177 的）
2. 进 Hermes 目录 `cd ~/.hermes/hermes-agent`
3. 激活 Python 环境 `source .venv/bin/activate`
4. 设环境变量并启动 `hindsight-api --port 9177 --idle-timeout 600`

如果卡住，可能是 HuggingFace 模型缓存丢了：
```bash
# 检查模型缓存
ls ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/ 2>/dev/null && echo "嵌入模型缓存存在" || echo "❌ 嵌入模型缓存不存在"
ls ~/.cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/ 2>/dev/null && echo "排序器模型缓存存在" || echo "❌ 排序器模型缓存不存在"

# 如果缓存丢了，需要联网下载（国内用镜像）：
export HF_ENDPOINT=https://hf-mirror.com
# 然后手动跑一次启动，它会自动下载
```

### 恢复 Step 3: 如果 L2 数据也丢了（bank 损坏）

```bash
# 检查 bank 状态
curl -s http://localhost:9177/v1/default/banks/hermes/stats | \
  python3 -c "import json,sys;d=json.load(sys.stdin);print(f'节点:{d[\"total_nodes\"]} 观察:{d[\"total_observations\"]}')"

# 如果 total_nodes=0（数据丢了），重建 bank：
curl -X DELETE http://localhost:9177/v1/default/banks/hermes
curl -X PUT http://localhost:9177/v1/default/banks/hermes \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes","disposition":{"skepticism":3,"literalism":3,"empathy":3}}'

# 然后从备份恢复（如果有）：
# L2 PostgreSQL 数据在 ~/.pg0/instances/hindsight/data/
# 如果这个目录还在，重启 hindsight 后数据自动恢复
# 如果这个目录也丢了，需要从 L1 路牌和 L3 文档重新喂
```

---

## 五、网关/平台问题

### 微信网关

```bash
# 查看网关状态
systemctl status wechat-gateway 2>/dev/null || echo "没有 systemd 服务"
ps aux | grep gateway | grep -v grep

# 重启网关
hermes gateway restart 2>/dev/null || echo "试试手动：hermes gateway start"

# 查看日志
cat ~/.hermes/logs/gateway.log | tail -30

# DNS 超时问题：如果日志里出现 "Temporary failure in name resolution"
# 会自动恢复，等几分钟就行
```

---

## 六、文件损坏/丢失

### 配置文件坏了

```bash
# 备份位置：每次改之前都会备份
ls ~/.hermes/config.yaml.bak.* 2>/dev/null || echo "没有备份"
# 如果有，恢复最新的：
cp "$(ls -t ~/.hermes/config.yaml.bak.* | head -1)" ~/.hermes/config.yaml
```

### 记忆文件坏了

```bash
# L1 内部记忆文件位置：
ls -la ~/.hermes/memories/
# MEMORY.md = L1 内容
# USER.md = 用户配置

# 直接从备份包恢复（如果有）：
tar -xzf /路径/全记忆备份_*.tar.gz -C ~/ .hermes/memories/

# 或者从 L2 召回：
# 见第三节 Step 2
```

### 定时任务丢了

```bash
cat ~/.hermes/cron/jobs.json 2>/dev/null | python3 -m json.tool || echo "❌ jobs.json 丢了或格式错误"
# 如果丢了，用备份恢复
# 或者 Hermes 启动后会重新注册 cron 任务
```

### 辅助工具状态检查

```bash
# Pinchtab（纯文本浏览器）
curl -s --connect-timeout 3 http://localhost:9867/?url=https://example.com >/dev/null 2>&1 && echo "Pinchtab OK" || echo "Pinchtab 未运行"

# RTK（终端噪音过滤）
command -v ~/.local/bin/rtk && echo "RTK OK" || echo "RTK 未安装"

# 模型转发脚本
ls ~/.hermes/scripts/chat-relay.sh 2>/dev/null && echo "chat-relay.sh OK" || echo "chat-relay.sh 不存在"
```

---

## 七、从零恢复（灾难方案 — 什么文件都不剩了）

**适用场景：** 硬盘坏了 / 重装系统了 / ~/.hermes 整个目录没了

### Step 1: 装 Hermes

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent && pip install -e .
```

### Step 2: 恢复记忆（如果有备份包）

```bash
# 查看备份包
tar -tzf /路径/全记忆备份_*.tar.gz | head -30

# 恢复全部
bash ~/桌面/全记忆备份.sh 恢复 /路径/全记忆备份_*.tar.gz
# 脚本会自动：检查版本兼容 → 停服 → 备份当前 → 解压 → 验证 → 重启
```

### Step 3: 如果没有备份包

那就真的从零开始了。最关键的都在外部 MD 文件夹里：

```bash
# 检查外部记忆是否还在（纯 MD 文件，是最容易备份的东西）
ls ~/.hermes/external_memory/*.md 2>/dev/null | head -10
# 如果这些文件还在 → 我还能恢复到 80%
# 把这些文件读给我（Hermes），我会根据内容重建所有内部记忆

# 如果你都不是 Hermes（是另一个 AI），读这些文件就能理解我的整个体系：
cat ~/.hermes/external_memory/INDEX.md
```

### Step 4: 重启所有服务

```bash
# 按这个顺序启动：
# 1. Hindsight L2（向量库，需要 ~25 秒加载模型）
bash ~/桌面/restart_hindsight_l2.sh
sleep 30

# 2. Hermes 主服务
hermes start

# 3. 验证
curl -s http://localhost:9177/health            # Hindsight
hermes doctor                                    # Hermes
```

---

## 八、架构速查（让另一个 AI 快速理解我）

我是 Hermes Agent，运行在 Ubuntu 上，职责如下：

```
我 = Hermes Agent (AI助手)
              ↓ 决策 + 分析
小龙虾 = OpenClaw (工具执行器, 定时任务/微信网关)
```

我的记忆分三层，丢了谁都不怕：

| 层级 | 比喻 | 存什么 | 物理位置 | 丢了怎么办 |
|:----|:----|:------|:---------|:----------|
| L1 | CPU缓存 | 铁律+路牌，自动注入每轮 | `~/.hermes/memories/` | 从L2 recall + L3文件重建 |
| L2 | RAM | 低频经验，按需语义检索 | Hindsight:9177 + PostgreSQL | 重启脚本恢复 |
| L3 | 硬盘 | 完整技术文档和恢复说明 | `~/.hermes/external_memory/*.md` | 从L1路牌+L2召回重建 |

API 三路全通（互相备份）：
- **DeepSeek V4 Flash（主力）** — ¥50-60/月，Hermes 唯一能正常运行的模型
- **阿里云百炼 qwen-turbo（⚠️ 不推荐做主力）** — 历史两次故障均因此模型太弱导致 Hermes 调工具后返回空，只作 API 连通性测试用
- **硅基流动 Qwen2.5-7B（免费备用）** — 纯闲聊可用，不支持工具调用

---

## 九、最后检查清单

恢复后运行以下命令确认一切正常：

```bash
echo "=== 1. Hermes 进程 ==="
ps aux | grep hermes | grep -v grep | head -3
echo ""

echo "=== 2. Hindsight L2 ==="
curl -s http://localhost:9177/health
echo ""

echo "=== 3. L1 内部记忆 ==="
head -3 ~/.hermes/memories/MEMORY.md 2>/dev/null || echo "空或不存在"
echo ""

echo "=== 4. L3 外部记忆 ==="
ls ~/.hermes/external_memory/*.md 2>/dev/null | wc -l
echo ""

echo "=== 5. API 连通性 ==="
curl -s --connect-timeout 5 -o /dev/null -w "DeepSeek: %{http_code}\n" https://api.deepseek.com/v1/models 2>/dev/null || echo "DeepSeek: 不通"
echo ""

echo "=== 6. 定时任务 ==="
cat ~/.hermes/cron/jobs.json 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f'  {j.get(\"name\",j[\"id\"])}: {j.get(\"schedule\",\"?\")}') for j in d.get('jobs',[])]" 2>/dev/null || echo "无定时任务"
```
