#!/usr/bin/env python3
"""
investment.clean.db V3

策略：events全保留不去重，board_raw全保留
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
print(f"events: {len(all_rows)}条，全部保留")

# 统计
ac = {}
for r in all_rows:
    rd = dict(zip(cols, r))
    a = rd.get('asset') or '(无)'
    ac[a] = ac.get(a, 0) + 1
for a, n in sorted(ac.items(), key=lambda x: -x[1]):
    print(f"  {a:12s}: {n}")

# events按asset+date统计重复情况
c.execute("""
    SELECT COALESCE(asset,'(无)'), COALESCE(date,''), COUNT(*), GROUP_CONCAT(source_ver,',')
    FROM events 
    WHERE date IS NOT NULL AND date != ''
    GROUP BY asset, date 
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
print("\n有日期重复TOP20:")
for r in c.fetchall():
    print(f"  {r[0]:12s} | {r[1]:12s} | {r[2]}条 | {r[3][:80]}")

# board_raw
bak = sqlite3.connect(BAK)
bc = bak.cursor()
bc.execute("SELECT * FROM board_raw")
raw_rows = bc.fetchall()
raw_cols = [d[0] for d in bc.description]
raw_cols_db = [c for c in raw_cols if c != 'id']
print(f"\nboard_raw: {len(raw_rows)}条，全部保留")

# 写入
out = sqlite3.connect(OUT)
oc = out.cursor()

c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='events'")
oc.execute(c.fetchone()[0])

placeholders = ','.join(['?'] * len(cols))
oc.execute("BEGIN TRANSACTION")
for r in all_rows:
    oc.execute(f"INSERT INTO events ({','.join(cols)}) VALUES ({placeholders})", r)
oc.execute("COMMIT")
print(f"events写入: {len(all_rows)}条")

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
print(f"✅ {OUT}")
