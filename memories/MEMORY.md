【L1已清空·2026-06-01】完整备份→~/.hermes/external_memory/L1-完整记忆备份.md。恢复=逐条memory(action='add')写回。L2=hindsight_recall("关键词"),端口9177。L1.5=hindsight_recall("L1.5:关键词")。【跑监控流程】主框架=~/.hermes/external_memory/监控统筹框架.md→按模块路由表顺序走子模块(工作流模块/抓取/阶段一.md等)→状态文件=/tmp/monitor_state.json。不准跳步不准私自改。
§
消费因子禁止规则正确理解：禁止把中国居民消费因子套到全球定价的工业商品和避险资产上（如有色/黄金），不是"消费因子不重要"。消费因子对可选消费（白酒/奶茶）和猪企右侧布局判断很重要。判定三问：买家是谁/定价权在哪/需求弹性多大。
§
看门狗机制：background terminal运行bash脚本(~/.hermes/scripts/watchdog.sh)，检查L1.5心跳超时(2分钟)写ATTENTION_FLAG到/tmp/hermes_watchdog_flag。主agent在每个阶段入口/工具调用后检查flag，读到flag→立即中断→回读L1.5恢复。看门狗检查父进程PID，主agent挂了自动退出。统筹框架加约8行描述。
§
Cookie提取2026-06-02验证结论：yt-dlp impersonate方案无效（发新请求到TikTok返回登录页无cookie）。CDP Storage.getCookies是唯一可行方案。yt-dlp仅用于B站视频下载（配合Netscape cookie），不用于cookie提取。环境准备.md的--format netscape参数已修正为--netscape。monitoring-pipeline skill引用已修复。但cookie-extractor skill有重复的"三层次存储系统"章节需要清理（patch SKILL.md失败，需要edit而非patch）。
§
监控统筹框架.md（474行原版）已确认保持不动。2026-06-02尝试基于V4 Pro建议拆分模块（目标≤150行调度器+4阶段模块），但结论是拆分反而违背用户"LLM只读1个文件"的核心要求，且原版已跑通。已回滚到原版。备份仍在backup_0602_原版.md。
§
监控框架架构决策(2026-06-02)：统筹框架必须≤150行，只做调度器（断点+防漂移+决策树+开关+路由表+自检）。阶段一抓取/阶段二转录/阶段三分析/阶段四收尾各自独立成模块，统筹框架只传返回值不塞细节。原版474行已跑通，备份在监控统筹框架_backup_0602_原版.md，有问题随时回滚。拆分方案必须先跟V4 Pro多轮讨论，一条一条过，不准直接改。
§
P值数据完整性问题(2026-06-02发现)：Excel看板P值从一开始就算错了。备份文件里芯片显示P=57%，但事件链从基准50%累加只有41%，差16pp。7持仓全错。根因是最早计算时就错了。已修正。