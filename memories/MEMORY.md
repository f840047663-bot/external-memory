【L1已清空·2026-06-01】完整备份→~/.hermes/external_memory/L1-完整记忆备份.md。恢复=逐条memory(action='add')写回。L2=hindsight_recall("关键词"),端口9177。L1.5=hindsight_recall("L1.5:关键词")。【跑监控流程】主框架=~/.hermes/external_memory/监控统筹框架.md→按模块路由表顺序走子模块(工作流模块/抓取/阶段一.md等)→状态文件=/tmp/monitor_state.json。不准跳步不准私自改。
§
消费因子禁止规则正确理解：禁止把中国居民消费因子套到全球定价的工业商品和避险资产上（如有色/黄金），不是"消费因子不重要"。消费因子对可选消费（白酒/奶茶）和猪企右侧布局判断很重要。判定三问：买家是谁/定价权在哪/需求弹性多大。
§
看门狗机制：background terminal运行bash脚本(~/.hermes/scripts/watchdog.sh)，检查L1.5心跳超时(2分钟)写ATTENTION_FLAG到/tmp/hermes_watchdog_flag。主agent在每个阶段入口/工具调用后检查flag，读到flag→立即中断→回读L1.5恢复。看门狗检查父进程PID，主agent挂了自动退出。统筹框架加约8行描述。
§
监控统筹框架.md（474行原版）已确认保持不动。2026-06-02尝试基于V4 Pro建议拆分模块（目标≤150行调度器+4阶段模块），但结论是拆分反而违背用户"LLM只读1个文件"的核心要求，且原版已跑通。已回滚到原版。备份仍在backup_0602_原版.md。
§
P值数据完整性问题(2026-06-02发现)：Excel看板P值从一开始就算错了。备份文件里芯片显示P=57%，但事件链从基准50%累加只有41%，差16pp。7持仓全错。根因是最早计算时就错了。已修正。
§
邮件用cronjob create+run触发，系统deliver投递，不准Python SMTP直发（login会Connection closed）。用户反感重复问已配好的授权码。用户不看财报，直接查数据给结论。
§
断点铁律：断点=归档到Excel才算。看板没写=断点不准动。cron管道bug(6/8)：断点先更新看板没写→数据永久丢失。总看板严禁运行日志/操作小结。cron输出必须主动检查。
§
用户极度反感复杂化简单事情。要求严格按文档一步步来，不准跳步骤。整不明白就找V4 Pro一点点讨论。V4 Pro讨论归档到~/.hermes/external_memory/v4-discussions/目录，格式YYYY-MM-DD-问题类别-简短描述.md。
§
持仓盈亏联动已嵌入监控§4.2.3（必做）。脚本portfolio_pnl_linkage.py，技能portfolio-pnl-linkage，数据holdings_live.json。净值用联接基金代码拉fundgz API，不准用ETF代码。支付宝数据100%准。用完整基金名称，不用简称。
§
真实持仓(2026-06-05,总29,716元)：电池7,220(+6%)/稀金5,872(+0.85%)/有色4,781(-0.41%)/恒科4,535(-5.95%)/养殖3,878(-12.49%)/芯片3,332(+3.93%)/AI 99元。金银珠宝+黄金ETF也是持仓。银行已清。现金比例极高(远超持仓)。资金分配计划里的百分比≠真实持仓。用户持仓逻辑：恒科=南向资金托底+估值修复+HALO+AI溢出。有色/稀金=工业复苏HALO。养殖=产能出清后回归(最大仓位，坚决不减)。黄金/金银珠宝=纯HALO+价值锚定。稀金(锂/稀土)≠黄金。
§
CDP Chrome(/tmp/chrome-debug)启动后总是ERR_PROXY_CONNECTION_FAILED——继承系统代理设置但代理未运行。每次浏览器CDP ID都变，需curl http://127.0.0.1:9222/json/version获取新ID并更新config.yaml cdp_url。要能上网必须用户关代理或重启Chrome加--proxy-server="direct://"参数。知乎WAF封服务器IP(curl也被拦)，所以CDP是唯一知乎通路。