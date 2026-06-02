【L1已清空·2026-06-01】完整备份→~/.hermes/external_memory/L1-完整记忆备份.md。恢复=逐条memory(action='add')写回。L2=hindsight_recall("关键词"),端口9177。L1.5=hindsight_recall("L1.5:关键词")。【跑监控流程】主框架=~/.hermes/external_memory/监控统筹框架.md→按模块路由表顺序走子模块(工作流模块/抓取/阶段一.md等)→状态文件=/tmp/monitor_state.json。不准跳步不准私自改。
§
消费因子禁止规则正确理解：禁止把中国居民消费因子套到全球定价的工业商品和避险资产上（如有色/黄金），不是"消费因子不重要"。消费因子对可选消费（白酒/奶茶）和猪企右侧布局判断很重要。判定三问：买家是谁/定价权在哪/需求弹性多大。
§
看门狗机制：background terminal运行bash脚本(~/.hermes/scripts/watchdog.sh)，检查L1.5心跳超时(2分钟)写ATTENTION_FLAG到/tmp/hermes_watchdog_flag。主agent在每个阶段入口/工具调用后检查flag，读到flag→立即中断→回读L1.5恢复。看门狗检查父进程PID，主agent挂了自动退出。统筹框架加约8行描述。
§
Cookie提取2026-06-02验证结论：yt-dlp impersonate方案无效（发新请求到TikTok返回登录页无cookie）。CDP Storage.getCookies是唯一可行方案。yt-dlp仅用于B站视频下载（配合Netscape cookie），不用于cookie提取。环境准备.md的--format netscape参数已修正为--netscape。monitoring-pipeline skill引用已修复。但cookie-extractor skill有重复的"三层次存储系统"章节需要清理（patch SKILL.md失败，需要edit而非patch）。