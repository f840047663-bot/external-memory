#!/bin/bash
# L1+L2 备份到百度网盘 /Hermes备份/
# 不压缩，直接打包（无gzip，老机器快）
set -e

DATE=$(date '+%Y%m%d_%H%M%S')
TMPDIR="/tmp/hermes-bak-$DATE"
REMOTE_DIR="/Hermes备份/$DATE"
LOG="/tmp/hermes-baidu-backup.log"

echo "[$(date '+%H:%M')] 开始备份 L1+L2" > "$LOG"

# 停 hindsight（防PG文件锁）
kill -9 $(pgrep -f hindsight) 2>/dev/null || true
sleep 2

# 打包（无压缩，纯打包更快）
mkdir -p "$TMPDIR"
tar cf "$TMPDIR/backup.tar" \
  -C ~/.hermes memories/MEMORY.md memories/USER.md \
  -C ~ .pg0 2>&1 >> "$LOG"
echo "[$(date '+%H:%M')] 打包完成 ($(du -h $TMPDIR/backup.tar | cut -f1))" >> "$LOG"

# 分卷（每卷20MB）
cd "$TMPDIR"
split -b 20M -d -a 2 backup.tar part_
echo "[$(date '+%H:%M')] 分卷完成" >> "$LOG"

# 逐个上传
for f in part_*; do
    echo "[$(date '+%H:%M')] 上传 $f" >> "$LOG"
    bypy upload "$f" "$REMOTE_DIR/" -t 120 >> "$LOG" 2>&1
done

# 合并脚本
printf 'cat part_* > backup.tar\ntar xf backup.tar\necho "恢复完成，backup.tar 已解压"\n' > 合并.sh
bypy upload 合并.sh "$REMOTE_DIR/" -t 120 >> "$LOG" 2>&1

rm -rf "$TMPDIR"
echo "[$(date '+%H:%M')] ✅ 备份完成: $REMOTE_DIR" >> "$LOG"
