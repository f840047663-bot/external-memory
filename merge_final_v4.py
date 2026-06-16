#!/usr/bin/env python3
"""
investment.clean.db FINAL

只保留有资产+有日期的事件，全部保留不去重，批注(comment)完整保留。
"""
import sqlite3, os

DB = '/home/fw/.hermes/external_memory/investment.db'
BAK = '/home/fw/.hermes/external_memory/investment.db.bak.0616'
OUT = '/home/fw/.hermes/external_memory/investment.clean.db'

db = sqlite3.connect(DB)
c = db.cursor()

c.execute("SELECT * FROM events ORDER BY id")
all_rows = c.fetchall()
cols = [d[0] for d in c.description]

# 有资产+有日期 = 真实事件
good = []
bad = []
for r in all_rows:
    rd = dict(zip(cols, r))
    if rd.get('asset') and rd.get('date') and rd['date'].strip():
        good.append(r)
    else:
        bad.append(r)

print(f"原始events: {len(all_rows)}条")
print(f"真实事件(有asset+有date): {len(good)}条")
print(f"丢弃(无asset或无date): {len(bad)}条")

# 资产分布
ac = {}
for r in good:
    rd = dict(zip(cols, r))
    a = rd['asset']
    ac[a] = ac.get(a, 0) + 1
for a, n in sorted(ac.items(), key=lambda x: -x[1]):
    print(f"  {a:12s}: {n}")

# 有comment的事件数
cc = 0
for r in good:
    rd = dict(zip(cols, r))
    if rd.get('comment') and rd['comment'].strip():
        cc += 1
print(f"有批注的事件: {cc}/{len(good)}条")

# board_raw仅保留有来源标记的(至少有个事件关联)
bak = sqlite3.connect(BAK)
bc = bak.cursor()
bc.execute("SELECT * FROM board_raw")
raw_rows = bc.fetchall()
raw_cols = [d[0] for d in bc.description]
raw_cols_db = [c for c in raw_cols if c != 'id']
print(f"\nboard_raw: {len(raw_rows)}条，全部保留")

# 写入
if os.path.exists(OUT):
    os.remove(OUT)
out = sqlite3.connect(OUT)
oc = out.cursor()

c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='events'")
oc.execute(c.fetchone()[0])

placeholders = ','.join(['?'] * len(cols))
oc.execute("BEGIN TRANSACTION")
for r in good:
    oc.execute(f"INSERT INTO events ({','.join(cols)}) VALUES ({placeholders})", r)
oc.execute("COMMIT")
print(f"events写入: {len(good)}条")

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
print(f"board_raw写入: {len(raw_rows)}条")

oc.execute("CREATE INDEX IF NOT EXISTS idx_events_asset ON events(asset)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_board_raw_sheet ON board_raw(sheet_name, row, col)")
out.commit()

oc.execute("SELECT COUNT(*) FROM events")
print(f"\n最终events: {oc.fetchone()[0]}条")
oc.execute("SELECT COUNT(*) FROM board_raw")
print(f"最终board_raw: {oc.fetchone()[0]}条")

bak.close()
db.close()
out.close()
print(f"\n✅ {OUT}")

# 打印样例验证
print("\n=== 抽样验证（前3条）===")
out2 = sqlite3.connect(OUT)
oc2 = out2.cursor()
oc2.execute("SELECT asset, date, p_value, substr(content,1,100), substr(COALESCE(comment,''),1,80) FROM events LIMIT 3")
for r in oc2.fetchall():
    print(f"  {r[0]:6s} | {r[1]:12s} | {r[2]:12s} | {r[3]} | {r[4]}")
out2.close()
