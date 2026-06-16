#!/usr/bin/env python3
"""
investment.clean.db V2

核心策略：
1. events: 有日期(304条)按asset+date去重，无日期(1982条)全部保留
2. board_raw: 从备份9754条全部保留，不合并
3. 添加source_ver能做版本标记
"""

import sqlite3, os

DB = '/home/fw/.hermes/external_memory/investment.db'
BAK = '/home/fw/.hermes/external_memory/investment.db.bak.0616'
OUT = '/home/fw/.hermes/external_memory/investment.clean.db'

VER_ORDER = {'0606': 0, '0607': 1, '0612': 2, '0614': 3}

db = sqlite3.connect(DB)
c = db.cursor()

c.execute("SELECT * FROM events ORDER BY id")
all_rows = c.fetchall()
cols = [d[0] for d in c.description]

print(f"原始events: {len(all_rows)}条")

# 分类
has_date = []
no_date = []
for r in all_rows:
    rd = dict(zip(cols, r))
    if rd.get('date') and rd.get('date').strip():
        has_date.append(r)
    else:
        no_date.append(r)

print(f"  有日期(事件): {len(has_date)}条")
print(f"  无日期(板子结构): {len(no_date)}条")

# 有日期 → 按(asset, date)去重，保留最新source_ver
date_dedup = {}
for r in has_date:
    rd = dict(zip(cols, r))
    key = (rd.get('asset') or '', rd['date'])
    if key not in date_dedup:
        date_dedup[key] = r
    else:
        ex = dict(zip(cols, date_dedup[key]))
        if VER_ORDER.get(rd['source_ver'], -1) > VER_ORDER.get(ex['source_ver'], -1):
            date_dedup[key] = r

dedup_has_date = list(date_dedup.values())
print(f"  事件去重后: {len(dedup_has_date)}条 (去掉{len(has_date)-len(dedup_has_date)}条)")

# 无日期 → 全部保留
merged = dedup_has_date + no_date
print(f"  合并后: {len(merged)}条")

# 统计资产分布
ac = {}
for r in merged:
    rd = dict(zip(cols, r))
    a = rd.get('asset') or '(无)'
    ac[a] = ac.get(a, 0) + 1
print("  资产分布:")
for a, n in sorted(ac.items(), key=lambda x: -x[1]):
    print(f"    {a:12s}: {n}")

# board_raw → 从备份全部保留
bak = sqlite3.connect(BAK)
bc = bak.cursor()
bc.execute("SELECT * FROM board_raw")
raw_rows = bc.fetchall()
raw_cols = [d[0] for d in bc.description]
raw_cols_db = [c for c in raw_cols if c != 'id']
print(f"\nboard_raw: {len(raw_rows)}条(全部保留)")

# 写入新库
if os.path.exists(OUT):
    os.remove(OUT)
out = sqlite3.connect(OUT)
oc = out.cursor()

# events表
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='events'")
oc.execute(c.fetchone()[0])

placeholders = ','.join(['?'] * len(cols))
oc.execute("BEGIN TRANSACTION")
for r in merged:
    oc.execute(f"INSERT INTO events ({','.join(cols)}) VALUES ({placeholders})", r)
oc.execute("COMMIT")
print(f"  events写入: {len(merged)}条")

# board_raw表
oc.execute("""
    CREATE TABLE IF NOT EXISTS board_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_ver TEXT,
        sheet_name TEXT,
        row INTEGER,
        col INTEGER,
        value TEXT,
        comment TEXT
    )
""")
rw_ph = ','.join(['?'] * len(raw_cols_db))
oc.execute("BEGIN TRANSACTION")
for r in raw_rows:
    rd = dict(zip(raw_cols, r))
    vals = [rd.get(c) for c in raw_cols_db]
    oc.execute(f"INSERT INTO board_raw ({','.join(raw_cols_db)}) VALUES ({rw_ph})", vals)
oc.execute("COMMIT")
print(f"  board_raw写入: {len(raw_rows)}条")

# 索引
oc.execute("CREATE INDEX IF NOT EXISTS idx_events_asset ON events(asset)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_board_raw_sheet ON board_raw(sheet_name, row, col)")

out.commit()

# 验证
oc.execute("SELECT COUNT(*) FROM events")
print(f"\n最终events: {oc.fetchone()[0]}条")
oc.execute("SELECT COUNT(*) FROM board_raw")
print(f"最终board_raw: {oc.fetchone()[0]}条")

db.close()
bak.close()
out.close()
print(f"\n✅ → {OUT}")
