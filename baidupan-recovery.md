# 百度网盘恢复指引

> 如果你看到这个文件，说明你正在通过 Git/本地 恢复。
> 完整的数据库和最新数据在 **百度网盘**。

## 百度网盘上有啥

百度网盘内 `hermes-investment-backup/` 目录包含：
- `investment.clean.db` — 最新完整数据库（SQLite）
- `investment.db` — 旧库（备用）
- `hermes-external-memory-full.tar.gz` — 整个 external_memory/ 目录打包
- `README.md` — 完整结构说明

## 怎么从百度网盘恢复

```bash
# 查看百度网盘文件
bypy list hermes-investment-backup/

# 下载整个备份目录
bypy downdir hermes-investment-backup/ ~/restore/

# 解压
cd ~/restore/hermes-investment-backup/
tar -xzf hermes-external-memory-full.tar.gz -C ~/.hermes/external_memory/
```

## 如遇问题

1. `bypy` 未安装：`pip install bypy`
2. 授权过期：`bypy info` → 按提示重新扫码
3. 恢复完成后，用 `sqlite3 ~/.hermes/external_memory/investment.clean.db "SELECT count(*) FROM events;"` 验证数据完整性
