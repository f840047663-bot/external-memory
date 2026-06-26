#!/usr/bin/env python3
"""Insert all events into investment.clean.db events table."""
import sqlite3
from datetime import datetime

DB_PATH = "/home/fw/.hermes/external_memory/investment.clean.db"
EVENTS_DIR = "/home/fw/.hermes/external_memory/events/"

# Define all events to insert (id, date, asset, p_value, comment, source_file)
# max_id = 2891, so we start from 2892

events = [
    # === 闭眼看世界 (3条有摘要) ===
    {
        "date": "2026-06-25",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:闭眼看世界】立陶宛总理鲁吉尼埃内因对华关系错误策略导致经济崩溃而辞职。中方要求先纠正错误。",
        "source_file": "2026-06-25-闭眼看世界-立陶宛总理辞职.md",
    },
    {
        "date": "2026-06-25",
        "asset": "具体资产名/半导体设备国产替代",
        "p_value": "实P+2pp",
        "comment": "【信源:闭眼看世界】日本五大芯片设备商对华销售额暴跌-12%，国产替代核心环节突破40%，市场转移不可逆。",
        "source_file": "2026-06-25-闭眼看世界-日本半导体出口暴跌.md",
    },
    {
        "date": "2026-06-25",
        "asset": "宏观/稀土供应链",
        "p_value": "0pp",
        "comment": "【信源:闭眼看世界】两名日本人因走私稀土磁体被刑拘。中国采取刑事拘留+有奖举报打击走私，稀土供应链博弈升级。",
        "source_file": "2026-06-25-闭眼看世界-日本人走私稀土被抓.md",
    },
    # === 拿幸·AI启示录 (5条有摘要) ===
    {
        "date": "2026-06-24",
        "asset": "中观/AI大模型",
        "p_value": "实P+2pp",
        "comment": "【信源:拿幸·AI启示录】豆包2.1 Pro 18小时完成芯片RTL设计1303行代码，多评测超越GPT/Claude，日均180万亿Token，MaaS市占49.5%。",
        "source_file": "2026-06-24-拿幸·AI启示录-豆包2.1Pro芯片RTL设计.md",
    },
    {
        "date": "2026-06-25",
        "asset": "中观/AI Agent应用",
        "p_value": "0pp",
        "comment": "【信源:拿幸·AI启示录】Anthropic推出Claude Tag——集成Slack的AI同事。AI Agent战争从模型打到办公桌，内部65%代码由AI生成。",
        "source_file": "2026-06-25-拿幸·AI启示录-Claude Tag完整解读.md",
    },
    {
        "date": "2026-06-25",
        "asset": "中观/AI芯片",
        "p_value": "0pp",
        "comment": "【信源:拿幸·AI启示录】OpenAI发布首款自研推理ASIC芯片Jalapeño，9个月极速流片，推理成本腰斩。AI造芯飞轮成型。",
        "source_file": "2026-06-25-拿幸·AI启示录-OpenAI自研芯片Jalapeño.md",
    },
    {
        "date": "2026-06-25",
        "asset": "中观/AI人才竞争",
        "p_value": "0pp",
        "comment": "【信源:拿幸·AI启示录】谷歌AI核心人才集体跳槽Anthropic（估值9650亿）。谷歌面临人才/算力/资本/产品/共识五重复合挑战。",
        "source_file": "2026-06-25-拿幸·AI启示录-谷歌人才跳槽Anthropic.md",
    },
    {
        "date": "2026-06-26",
        "asset": "中观/AI企业应用",
        "p_value": "0pp",
        "comment": "【信源:拿幸·AI启示录】李开复：中美AI下半场在企业内部落地而非模型智商。企业本体+数据闭环运营是护城河。",
        "source_file": "2026-06-26-拿幸·AI启示录-李开复预判中美AI.md",
    },
    # === 晨钟暮鼓自由人生 (4条有摘要) ===
    {
        "date": "2026-06-13",
        "asset": "具体资产名/贵州茅台",
        "p_value": "虚P-1pp",
        "comment": "【信源:晨钟暮鼓自由人生】茅台处于第四阶段下行确认，可能是第五阶段底部恐慌前夜。核心不确定性：周期性调整or估值中枢下移？",
        "source_file": "2026-06-13-晨钟暮鼓自由人生-茅台周期阶段分析.md",
    },
    {
        "date": "2026-06-14",
        "asset": "具体资产名/腾讯控股",
        "p_value": "实P+1pp",
        "comment": "【信源:晨钟暮鼓自由人生】腾讯未来五年营收增速9%-13%，利润增速10%-15%。驱动力：云服务、微短剧、AI技术。",
        "source_file": "2026-06-14-晨钟暮鼓自由人生-腾讯增长分析.md",
    },
    {
        "date": "2026-06-18",
        "asset": "具体资产名/富信科技",
        "p_value": "虚P+1pp",
        "comment": "【信源:晨钟暮鼓自由人生】富信科技为国产Micro TEC唯一供应商，受益于出口管制+AI光模块需求。全球缺口2250万片（2026），PE 355倍估值极高。",
        "source_file": "2026-06-18-晨钟暮鼓自由人生-富信科技Micro TEC研究.md",
    },
    {
        "date": "2026-06-22",
        "asset": "具体资产名/贵州茅台",
        "p_value": "虚P-0.5pp",
        "comment": "【信源:晨钟暮鼓自由人生】茅台6次大跌反转复盘。当前与2014年相似但更难，直销占比突破50%。乐观20%/中性55%/悲观25%，建议极小仓位观察。",
        "source_file": "2026-06-22-晨钟暮鼓自由人生-茅台6次大跌反转复盘.md",
    },
    # === 岩松笔记 (5条有摘要) ===
    {
        "date": "2026-06-11",
        "asset": "具体资产名/国电南瑞",
        "p_value": "虚P-1pp",
        "comment": "【信源:岩松笔记】国电南瑞增速约10%，难以保持25%以上高增长。客户为国家电网和头部发电企业，应收账款风险较低。",
        "source_file": "2026-06-11-岩松笔记-国电南瑞增长放缓.md",
    },
    {
        "date": "2026-06-16",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:岩松笔记】五步看懂上市公司：利润→估值→行业→产品→实控人。方法论类内容。",
        "source_file": "2026-06-16-岩松笔记-五步看懂上市公司.md",
    },
    {
        "date": "2026-06-19",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:岩松笔记】长线价值投资vs短线热点炒作是两套体系，普通人难以兼顾。建议专注一种体系。",
        "source_file": "2026-06-19-岩松笔记-长线vs短线选择.md",
    },
    {
        "date": "2026-06-22",
        "asset": "具体资产名/券商板块",
        "p_value": "0pp",
        "comment": "【信源:岩松笔记】券商分化：中信/东财利润以固收为主，国信证券属传统周期性券商。慢牛受益需甄别。",
        "source_file": "2026-06-22-岩松笔记-慢牛券商受益分析.md",
    },
    {
        "date": "2026-06-22",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:岩松笔记】价值投机思路：量化筛选优质个股+技术分析波段操作，不追高/不买估值透支/设止盈止损。",
        "source_file": "2026-06-22-岩松笔记-价值投机思路.md",
    },
    # === 大鹅确定性 (3条有摘要) ===
    {
        "date": "2026-06-22",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:大鹅确定性】美国脑洞型产品创新，投资者想要上涨收益也想有高租金回报。",
        "source_file": "2026-06-22-大鹅确定性-美国脑洞型产品.md",
    },
    {
        "date": "2026-06-24",
        "asset": "中观/科技股",
        "p_value": "虚P+1pp",
        "comment": "【信源:大鹅确定性】不论加息与否，释放流动性是必要的。利好科技股/光模块/半导体。",
        "source_file": "2026-06-24-大鹅确定性-美联储释放流动性必要.md",
    },
    {
        "date": "2026-06-25",
        "asset": "具体资产名/存储芯片",
        "p_value": "实P+2pp",
        "comment": "【信源:大鹅确定性】美光财报超预期（营收414亿，EPS 25+，毛利率85%），下季指引500亿。科技浪潮比房产周期更大。",
        "source_file": "2026-06-25-大鹅确定性-美光财报超预期科技海啸.md",
    },
    # === 熊哥有干货 (2条有摘要) ===
    {
        "date": "2026-06-24",
        "asset": "具体资产名/黄金",
        "p_value": "0pp",
        "comment": "【信源:熊哥有干货】黄金是全球风向标。美债收益率升高理论上压制黄金但实际走势相反。区分信用危机型vs加息预期型。",
        "source_file": "2026-06-24-熊哥有干货-黄金美债逻辑.md",
    },
    {
        "date": "2026-06-25",
        "asset": "具体资产名/黄金",
        "p_value": "0pp",
        "comment": "【信源:熊哥有干货】黄金变了——黄金定价逻辑正在发生变化。",
        "source_file": "2026-06-25-熊哥有干货-黄金变了.md",
    },
    # === 但斌 (1条有摘要) ===
    {
        "date": "2026-06-26",
        "asset": "宏观",
        "p_value": "0pp",
        "comment": "【信源:但斌】91岁张钹院士：保持好奇心和求知欲。中年后好奇心下降是大脑衰退和生活失去动力的原因。",
        "source_file": "2026-06-26-但斌-张钹院士保持好奇心.md",
    },
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get max_id
cur.execute("SELECT MAX(id) FROM events")
max_id = cur.fetchone()[0] or 0
print(f"Current max_id: {max_id}")

# Insert all events
inserted = 0
for i, ev in enumerate(events):
    new_id = max_id + 1 + i
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO events (id, source_ver, sheet, asset, category, row_num, col_num, date, p_value, content, comment, created_at, md5, author, channel, tags, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id,       # id
        None,         # source_ver
        None,         # sheet
        ev["asset"],  # asset
        None,         # category
        None,         # row_num
        None,         # col_num
        ev["date"],   # date
        ev["p_value"],# p_value
        None,         # content
        ev["comment"],# comment
        now,          # created_at
        None,         # md5
        None,         # author
        None,         # channel
        None,         # tags
        ev["source_file"], # source_file
    ))
    print(f"  INSERT id={new_id}: {ev['date']} {ev['source_file']} asset={ev['asset']} p={ev['p_value']}")
    inserted += 1

conn.commit()
conn.close()
print(f"\nDone! Inserted {inserted} events. IDs: {max_id+1} → {max_id+inserted}")
