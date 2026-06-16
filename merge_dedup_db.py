#!/usr/bin/env python3
"""
合并去重 investment.db → investment.clean.db

策略：
events表：
  1. 有日期（真实事件）：按(asset, date, source_ver)去重，同一个asset+date保留最新版本（0614 > 0612 > 0607 > 0606）
  2. 有asset无日期（看板结构行）：按(asset, content)去重，保留最新版本
  3. 无asset无日期：按content去重保留唯一

board_raw表：
  从备份investment.db.bak.0616取全部9754条，按(sheet_name, row, col, source_ver)去重，保留最新版本
"""

import sqlite3
import os

DB_PATH = '/home/fw/.hermes/external_memory/investment.db'
BAK_PATH = '/home/fw/.hermes/external_memory/investment.db.bak.0616'
OUT_PATH = '/home/fw/.hermes/external_memory/investment.clean.db'

VER_ORDER = {'0606': 0, '0607': 1, '0612': 2, '0614': 3}

# ---------- events 去重 ----------
print("=== events去重 ===")
db = sqlite3.connect(DB_PATH)
c = db.cursor()

# 全量events
c.execute("SELECT * FROM events ORDER BY id")
all_rows = c.fetchall()
cols = [d[0] for d in c.description]
print(f"  原始events: {len(all_rows)}条")

# 分三类处理
has_date = []    # 有asset有date
has_asset = []   # 有asset无date
no_asset = []    # 无asset

for r in all_rows:
    row_dict = dict(zip(cols, r))
    asset = row_dict.get('asset')
    date = row_dict.get('date')
    if asset and date:
        has_date.append(r)
    elif asset:
        has_asset.append(r)
    else:
        no_asset.append(r)

print(f"  有资产有日期: {len(has_date)}条")
print(f"  有资产无日期: {len(has_asset)}条")
print(f"  无资产:       {len(no_asset)}条")

# 有asset+date：按(asset, date)去重，保留source_ver最大的
date_dedup = {}
for r in has_date:
    rd = dict(zip(cols, r))
    key = (rd['asset'], rd['date'])
    if key not in date_dedup:
        date_dedup[key] = r
    else:
        existing = dict(zip(cols, date_dedup[key]))
        if VER_ORDER.get(rd['source_ver'], -1) > VER_ORDER.get(existing['source_ver'], -1):
            date_dedup[key] = r

# 有asset无日期：按(asset, content)去重，保留source_ver最大的
asset_dedup = {}
for r in has_asset:
    rd = dict(zip(cols, r))
    key = (rd['asset'], rd['content'])
    if key not in asset_dedup:
        asset_dedup[key] = r
    else:
        existing = dict(zip(cols, asset_dedup[key]))
        if VER_ORDER.get(rd['source_ver'], -1) > VER_ORDER.get(existing['source_ver'], -1):
            asset_dedup[key] = r

# 无asset：按content去重
no_asset_dedup = {}
for r in no_asset:
    rd = dict(zip(cols, r))
    key = rd['content']
    if key not in no_asset_dedup:
        no_asset_dedup[key] = r
    else:
        existing = dict(zip(cols, no_asset_dedup[key]))
        if VER_ORDER.get(rd['source_ver'], -1) > VER_ORDER.get(existing['source_ver'], -1):
            no_asset_dedup[key] = r

merged_events = list(date_dedup.values()) + list(asset_dedup.values()) + list(no_asset_dedup.values())
print(f"  events去重后: {len(merged_events)}条 (去掉了{len(all_rows) - len(merged_events)}条重复)")

# 统计去重后各资产数量
asset_counts = {}
for r in merged_events:
    rd = dict(zip(cols, r))
    a = rd.get('asset') or '(无)'
    asset_counts[a] = asset_counts.get(a, 0) + 1
print("  去重后资产分布:")
for a, n in sorted(asset_counts.items(), key=lambda x: -x[1]):
    print(f"    {a:12s}: {n}")

# ---------- board_raw 去重 ----------
print("\n=== board_raw去重 ===")
bak = sqlite3.connect(BAK_PATH)
bc = bak.cursor()
bc.execute("SELECT * FROM board_raw")
raw_rows = bc.fetchall()
raw_cols = [d[0] for d in bc.description]
print(f"  备份board_raw: {len(raw_rows)}条")

# 按(sheet_name, row, col)去重，保留source_ver最大的
raw_dedup = {}
for r in raw_rows:
    rd = dict(zip(raw_cols, r))
    key = (rd['sheet_name'], rd['row'], rd['col'])
    if key not in raw_dedup:
        raw_dedup[key] = r
    else:
        existing = dict(zip(raw_cols, raw_dedup[key]))
        if VER_ORDER.get(rd['source_ver'], -1) > VER_ORDER.get(existing['source_ver'], -1):
            raw_dedup[key] = r

merged_raw = list(raw_dedup.values())
print(f"  board_raw去重后: {len(merged_raw)}条 (去掉了{len(raw_rows) - len(merged_raw)}条重复)")

# ---------- 写入新库 ----------
print("\n=== 写入新库 ===")
if os.path.exists(OUT_PATH):
    os.remove(OUT_PATH)
out = sqlite3.connect(OUT_PATH)
oc = out.cursor()

# 创建events表
# 从原库获取events表结构
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='events'")
create_sql = c.fetchone()[0]
oc.execute(create_sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS'))

# 批量插入events
placeholders = ','.join(['?'] * len(cols))
oc.execute("BEGIN TRANSACTION")
for r in merged_events:
    oc.execute(f"INSERT INTO events ({','.join(cols)}) VALUES ({placeholders})", r)
oc.execute("COMMIT")
print(f"  events写入: {len(merged_events)}条")

# 创建board_raw表
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

raw_cols_db = [c for c in raw_cols if c != 'id']
raw_placeholders = ','.join(['?'] * len(raw_cols_db))
oc.execute("BEGIN TRANSACTION")
for r in merged_raw:
    rd = dict(zip(raw_cols, r))
    vals = [rd.get(c) for c in raw_cols_db]
    oc.execute(f"INSERT INTO board_raw ({','.join(raw_cols_db)}) VALUES ({raw_placeholders})", vals)
oc.execute("COMMIT")
print(f"  board_raw写入: {len(merged_raw)}条")

# 索引
oc.execute("CREATE INDEX IF NOT EXISTS idx_events_asset ON events(asset)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
oc.execute("CREATE INDEX IF NOT EXISTS idx_board_raw_sheet ON board_raw(sheet_name, row, col)")

out.commit()

# 验证
oc.execute("SELECT COUNT(*) FROM events")
print(f"\n  最终events: {oc.fetchone()[0]}条")
oc.execute("SELECT COUNT(*) FROM board_raw")
print(f"  最终board_raw: {oc.fetchone()[0]}条")

# 资产分布
oc.execute("SELECT COALESCE(asset,'(无)'), COUNT(*) FROM events GROUP BY asset ORDER BY COUNT(*) DESC")
print("  最终资产分布:")
for r in oc.fetchall():
    print(f"    {r[0]:12s}: {r[1]}")

db.close()
bak.close()
out.close()
print("\n✅ 完成! → investment.clean.db")
