邮件用cronjob create+run触发，系统deliver投递，不准Python SMTP直发（login会Connection closed）。用户反感重复问已配好的授权码。用户不看财报，直接查数据给结论。
§
【2026-06-16数据持久化铁律】events文件写完后必须立即写入数据库events表（investment.clean.db）。之前发生的6/10-6/15数据空白的根因是只写文件不写库。三步才算完成：写events文件 → 写数据库 → 回复用户。已固化到master-routing和monitoring-pipeline技能。
§
用户明确：他说"归档"=启动归档技能event-archive-three-link，按三处联动走（events一事件一文件+narratives提炼多空+看板同步双向引用）。不需要我猜。日常档案类问题找session_search查历史记录，不写L1。
§
真实持仓(2026-06-05,总29,716元)：电池7,220(+6%)/稀金5,872(+0.85%)/有色4,781(-0.41%)/恒科4,535(-5.95%)/养殖3,878(-12.49%)/芯片3,332(+3.93%)/AI 99元。金银珠宝+黄金ETF也是持仓。银行已清。现金比例极高(远超持仓)。资金分配计划里的百分比≠真实持仓。用户持仓逻辑：恒科=南向资金托底+估值修复+HALO+AI溢出。有色/稀金=工业复苏HALO。养殖=产能出清后回归(最大仓位，坚决不减)。黄金/金银珠宝=纯HALO+价值锚定。稀金(锂/稀土)≠黄金。
§
投资框架已定死为瑞·达利奥框架。每次阶段三分析时，自动审核持仓是否符合达利奥四象限配置（增长↑通胀↑/增长↑通胀↓/增长↓通胀↑/增长↓通胀↓），检查是否过度集中在单一象限。持仓分散度低于达利奥标准时主动提醒用户。
§
investment.db events表新增source_file列。软链接导出陷阱：桌面xlsx若为软链接则用户看不到内容，需rm再重新生成。Sheet2格式有两种（0606版三行分隔 vs 0614版行内|分隔）。160条事件/91KB=完整版本。
§
【2027危机拦截铁律 2026-06-12】用户要求：任何时候他说"加仓恒科/有色/稀金"，必须立即提醒"2027金融危机雷还没爆，不要搞这些东西"。这是硬拦截，除非他主动说"我不管2027危机，我就是要加"。此规则写入所有相关文件。
§
【2026-06-14 技能更新3项】：①subagent-dispatch-rules增加「督工模式」：子agent直接跑脚本不改代码，如实报告；增加「静默吞错误」bug模式排查。②monitoring-pipeline增加cdp-browser-reader.py参数失配陷阱（--url/--scroll不存在，2>/dev/null吞报错）。③local-chrome-cdp-bridge增加cdp-browser-reader.py实际参数说明章节。
§
【2026-06-15 用户反馈】cron输出"太简略"——只抓主线名，搞不懂发生了啥事。已补master-routing §十四Cron输出质量标准。看板有事件数据但列宽截断，视觉不友好。

020056c96303（每周情报搜索）DDGS连接失败，需要fallback到curl搜狗。

e89a23eb8584（PC恢复提醒）无实质内容，用户已确认。
§
【铁律·数据库路径固化】investment.clean.db 固定路径 = ~/.hermes/external_memory/investment.clean.db（即 /home/fw/.hermes/external_memory/investment.clean.db）。任何时候读数据库events表、查P值、查事件链，直接用这个路径。不准再find搜、不准再猜、不准再用session_search确认。这是唯一的真相来源库。
§
【数据库断点化 2026-06-20】彻底抛弃events文件维度做断点核对。监控流程的「抓取起点」直接从数据库events表取MAX(created_at)。脚本 ~/.hermes/scripts/events_db_checkpoint.py 实现三件事：①最新3条入库+近10天线图（默认）②按资产查看各asset最新入库时间（--by-asset）③校验某个时间之后有无新数据（--before "时间"），用在写库后自动验证。每个资产last入库可见，断档立刻发现。
§
【2026-06-20 达利欧AI泡沫警告】达利欧指出AI三大泡沫特征（估值高企/企业使用率不足20%/账面财富远超现金流），与美债30Y>5.19%+地缘动荡并列为合成风暴。警示2026-2028年动荡期。已归档：AI虚P-2pp/芯片虚P-1pp/恒科虚P-1pp。