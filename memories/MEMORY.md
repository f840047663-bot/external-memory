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
P值数据完整性问题(2026-06-02发现)：Excel看板P值从一开始就算错了。备份文件里芯片显示P=57%，但事件链从基准50%累加只有41%，差16pp。7持仓全错。根因是最早计算时就错了。已修正。
§
Cron推送不走微信（静默吞消息），全走QQ邮箱SMTP到feng202210062126@qq.com。用户不看财报，直接查数据给结论（加仓/不加仓/等）。
§
持仓：电池009759/养殖008765/恒科009854/稀金008907/有色008826/原油162411。HALO：稀金=真，有色=半，其余方向性。原油cron(e0306ceafb3f)工作日16/17点事件+价格双驱动。
§
用户2026-06-03识别的存储/SSD投资机会：群联潘健成指出Flash供应仍严重不足，AI落地推动下半年至明年SSD大量采购，明年更紧张。用户判断：中期选举年大盘跌一波=买入时机，确定性高、盈亏比好。与现有芯片ETF(020628)是上下游关系。用户考虑加到看板事件链和待重仓监控。
§
用户核心设计原则：断点=归档到Excel表格才算。抓取脚本里断点更新必须删除，断点只在管道全部走完（下载→转录→分析→写看板）后由pipeline显式调用update_state()。抓取脚本scrape_all_platforms.py的断点更新已全部删除（2026-06-03修复）。
§
用户极度反感复杂化简单事情。要求严格按文档一步步来，不准跳步骤。整不明白就找V4 Pro一点点讨论。V4 Pro讨论归档到~/.hermes/external_memory/v4-discussions/目录，格式YYYY-MM-DD-问题类别-简短描述.md。
§
持仓盈亏联动已嵌入监控§4.2.3（必做）。脚本portfolio_pnl_linkage.py，技能portfolio-pnl-linkage，数据holdings_live.json。净值用联接基金代码拉fundgz API，不准用ETF代码。支付宝数据100%准。用完整基金名称，不用简称。
§
2026-06-07技能更新：
1. long-task-attention-management添加失败17(cron清空L1.5)和失败18(新会话无交接)
2. monitoring-pipeline添加cron L1.5误清空pitfall
3. cron job 6f2bdfc62adb已修复不准清空L1.5
4. 蒋宇飞180视频转录179/180完成
5. 知乎zhivrtgm API返回4041用户不存在
6. 抖音号63519776649/73030232544待解析
7. hindsight服务不稳定(500错误)