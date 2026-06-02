# 子agent辅助监控架构

> **创建时间：** 2026-06-02
> **核心原则：** 主agent注意力=流程控制，子agent=机械执行，看门狗=结构校验
> **前身备份：** 监控统筹框架.md.bak_20260602

---

## 一、角色分工

### 主agent（Hermes Flash）—— 流程控制器
**职责：**
- 读L1.5状态 → 判断当前在哪一步
- 决定下一步干什么（绝对不能委托）
- 分发任务给子agent（写prompt）
- 审核子agent返回结果（结构校验+关键内容抽查）
- 更新L1.5状态
- 异常决策（断点恢复、策略切换、异动审核）

**主agent上下文始终保持：**
- 当前L1.5状态（~100字）
- 统筹框架指令（~430行，唯一入口）
- 上一阶段结论摘要（~200字）

### 子agent —— 机械执行器
**适合子agent干的活：**
| 阶段 | 任务 | 为什么适合 |
|------|------|-----------|
| 阶段一 | 三平台抓取验证 | 机械操作，断点ID比对，无需推理 |
| 阶段二 | 视频转录（Docker命令） | 执行脚本，等待完成，提取文字 |
| 阶段三 | 事件提取+归档 | 读转录文本→按格式写events/thinkers |
| 阶段四 | 断点+Excel镜像同步 | 格式操作，字段对齐 |

**子agent绝对不能干的：**
- 判断"下一步干什么"
- 异常定性（这是涨还是跌？是需求还是供给？）
- 策略切换（要不要中断流程？）
- 写Excel看板P值（阶段三禁写铁律）

### 看门狗脚本 —— 结构校验器
**职责：**
- 校验子agent返回的结构完整性（缺字段→告警）
- 校验L1.5心跳（2分钟没更新→写flag）
- 零token、零幻觉、独立bash进程

---

## 二、执行流程（子agent版）

```
§0 环境准备
├── 主agent：清内存 → 检查CDP/Cookie → 问五开关 → 创建L1.5
└── 主agent：启动看门狗脚本

§阶段一 抓取
├── 主agent：读断点文件，确定起始ID
├── 主agent：delegate_task → 子agent抓取三平台
│   ├── 子agent：抖音→B站→知乎，断点ID锚点比对
│   ├── 子agent：返回 {新视频列表, 断点ID, 平台状态}
├── 看门狗：校验返回结构（缺字段→告警）
├── 主agent：审核结果 → 更新L1.5
└── 无新内容？→ 跳阶段四收尾

§阶段二 转录
├── 主agent：delegate_task → 子agent转录
│   ├── 子agent：ffmpeg → VideoCaptioner Docker → 提取文字
│   ├── 子agent：返回 {转录文件路径列表, 完成数, 失败数}
├── 看门狗：校验返回结构
├── 主agent：审核结果 → 更新L1.5
└── 有失败？→ 主agent决策：重试 or 跳过

§阶段三 分析
├── 主agent自己干（不适合子agent）
│   ├── 读转录文本 → 五道门贝叶斯分析
│   ├── 消费因子禁止检查
│   ├── P'虚值 or P实值判断
│   ├── 异动审核（如触发）
│   └── 攒看板数据（不准写Excel！）
├── 主agent：delegate_task → 子agent归档
│   ├── 子agent：写events/thinkers/positions文件
│   └── 子agent：返回 {归档文件列表, 事件数}
├── 看门狗：校验返回结构
└── 主agent：审核归档 → 更新L1.5

§阶段四 收尾
├── 主agent自己干
│   ├── 写Excel看板（最终交付物）
│   ├── 断点+Excel镜像同步
│   ├── 日报汇总
├── 主agent：终止看门狗 → 清除flag
└── 主agent：清内存 → 汇报
```

---

## 三、看门狗脚本设计

```bash
#!/bin/bash
# ~/.hermes/scripts/watchdog.sh
# 职责：1)心跳检查 2)子agent返回结构校验

HEARTBEAT_FILE=~/.hermes/external_memory/L1.5_工作记忆.md
FLAG_FILE=/tmp/hermes_watchdog_flag
PARENT_PID=$$
CHECK_INTERVAL=30
HEARTBEAT_TIMEOUT=120

while true; do
    # 1. 检查父进程是否还在
    if ! kill -0 $PARENT_PID 2>/dev/null; then
        exit 0  # 主agent挂了，自动退出
    fi
    
    # 2. 心跳检查
    if [ -f "$HEARTBEAT_FILE" ]; then
        LAST_MOD=$(stat -c %Y "$HEARTBEAT_FILE" 2>/dev/null || echo 0)
        NOW=$(date +%s)
        if [ $((NOW - LAST_MOD)) -gt $HEARTBEAT_TIMEOUT ]; then
            echo "ATTENTION_DRIFT: L1.5心跳超时 $(($((NOW - LAST_MOD)) / 60))分钟" > "$FLAG_FILE"
        fi
    fi
    
    # 3. 子agent返回结构校验（检查最近的归档文件）
    # 如果阶段三完成但events目录没有新文件 → 告警
    # （具体逻辑根据L1.5状态判断）
    
    sleep $CHECK_INTERVAL
done
```

---

## 四、Token账

| 方案 | 阶段一 | 阶段二 | 阶段三 | 阶段四 | 合计 |
|------|--------|--------|--------|--------|------|
| Flash自己干 | ~1500 | ~1000 | ~2500 | ~1000 | ~6000 |
| 子agent辅助 | ~2500 | ~2000 | ~1500(主)+~1500(子) | ~2000 | ~11000 |

**多花~5000 token，但注意力不漂移。** 用Flash模型，成本几乎可以忽略。

---

## 五、反脆弱设计

| 故障场景 | 影响 | 恢复 |
|----------|------|------|
| 子agent返回糊弄 | 看门狗校验结构→缺字段告警 | 主agent重发任务 |
| 子agent卡死超时 | Hermes自带timeout机制 | 主agent收到错误→重试或跳过 |
| 看门狗挂了 | 降级到L1.5手动检查 | 不影响流程执行 |
| 主agent漂移 | 看门狗写flag→主agent下次检查点恢复 | 读L1.5→回到正确步骤 |
| L1.5没更新 | 看门狗心跳超时→写flag | 同上 |

---

## 六、与现有铁律的关系

| 铁律 | 子agent架构下的执行 |
|------|-------------------|
| P'转实必须推用户确认 | 主agent自己判断→推用户，不委托子agent |
| 消费因子禁止 | 主agent自己在阶段三检查，不委托 |
| 断点=看板镜像同步 | 子agent干格式操作，主agent审核 |
| 阶段三不准写看板 | 主agent控制，子agent只归档events/thinkers |
| 三关否决权 | 主agent自己判断，不委托 |

**5条铁律全部由主agent掌控，子agent碰不到。**
