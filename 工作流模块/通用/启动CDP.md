# 启动CDP

## 输入
- 无

## 输出（返回值）
| 字段 | 类型 | 说明 |
|:----|:----|:----|
| 状态 | ✅/❌ | Chrome CDP是否启动成功 |
| 端口 | 数字 | 实际监听端口（应=9222） |
| 失败原因 | 字符串 | 如果❌，返回原因 |

## 执行步骤

### Step 1：检查Chrome是否运行
```bash
curl -s http://127.0.0.1:9222/json/version
```
- 有返回 → ✅ 跳Step 3
- 无返回 → ❌ 跳Step 2

### Step 2：启动Chrome
```bash
# 方式1：systemd服务
systemctl --user enable --now chrome-cdp.service

# 方式2：手动启动（如果systemd失败）
/opt/google/chrome/chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  --no-sandbox \
  --window-size=1280,720 \
  --noheadless
```
- 启动后sleep 3秒 → 跳Step 3

### Step 3：验证并更新配置
```bash
# 验证端口
curl -s http://127.0.0.1:9222/json/version

# 更新Hermes配置（关键！Chrome每次重启ID都变）
bash ~/系统工具/更新Chrome-CDP-ID.sh
```

## 返回值示例
```
{
  "状态": "✅",
  "端口": 9222,
  "browser_id": "5abbdff3-bdfb-4bf0-a566-08fe9b0c67fa"
}
```

## 失败处理
| 故障 | 解决 |
|:----|:-----|
| 端口被占用 | `pkill -9 -f chrome` → 重启动 |
| OOM被杀 | `bash ~/桌面/脚本/内存急救.sh` → 重启动 |
| 窗口不显示 | 检查DISPLAY/WAYLAND_DISPLAY环境变量 |
| 配置404 | 运行`更新Chrome-CDP-ID.sh` |
