# Chrome CDP 启动指南

> **用途：** Hermes监控全流程需要Chrome CDP（9222端口）提取cookie和下载视频
> **最后更新：** 2026-05-30
> **状态：** ✅ systemd用户服务（最可靠方案）

---

## 为什么用systemd用户服务

| 方案 | 可靠性 | 原因 |
|:----|:----|:----|
| `systemd-run --user --pty` | ❌ 差 | terminal超时后被kill |
| `nohup/disown` | ❌ 差 | Hermes禁止shell级后台 |
| `terminal(background=true)` | ❌ 差 | 进程被Hermes跟踪，session结束就死 |
| **systemd用户服务** | ✅ 最稳 | 开机自启、崩溃自重启、独立生命周期 |

---

## 一键操作

```bash
# 启动/检查（一键脚本）
bash ~/桌面/系统工具/chrome-cdp-一键.sh

# 或者手动操作
# 启动
systemctl --user start google-chrome-cdp

# 重启（配置改了用这个）
systemctl --user restart google-chrome-cdp

# 检查状态
systemctl --user status google-chrome-cdp

# 验证9222端口
curl -s http://127.0.0.1:9222/json/version

# 停止
systemctl --user stop google-chrome-cdp

# 开机自启（已enable，不用手动开）
systemctl --user enable google-chrome-cdp
```

---

## 服务文件位置

`~/.config/systemd/user/google-chrome-cdp.service`

```ini
[Unit]
Description=Chrome CDP Debug Server (for Hermes)
After=graphical.target

[Service]
Type=simple
Environment=DISPLAY=:0
ExecStart=/usr/bin/google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  --no-sandbox \
  --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" \
  --window-size=1280,720 \
  --noheadless
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

---

## Cookie提取流程

```bash
# 1. 确认服务运行
bash ~/桌面/系统工具/chrome-cdp-一键.sh

# 2. 在Chrome里打开B站/知乎/抖音（确保登录态活跃）
#    Chrome窗口会在桌面显示，手动操作

# 3. 提取cookie
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com --output ~/桌面/凭证/bilibili_com_cookie_最新.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --output ~/桌面/凭证/zhihu_com_cookie_最新.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output ~/桌面/凭证/douyin_com_cookie_最新.txt

# 4. 同步到/tmp
cp ~/桌面/凭证/bilibili_com_cookie_最新.txt /tmp/bilibili_cookies.txt
cp ~/桌面/凭证/zhihu_com_cookie_最新.txt /tmp/zhihu_cookies.txt
cp ~/桌面/凭证/douyin_com_cookie_最新.txt /tmp/douyin_cookies.txt

# 5. 持久化Netscape格式
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com --output ~/.hermes/cookies/bilibili_netscape.txt --format netscape
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --output ~/.hermes/cookies/zhihu_netscape.txt --format netscape
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output ~/.hermes/cookies/douyin_netscape.txt --format netscape

# 6. 验证
wc -c /tmp/bilibili_cookies.txt /tmp/zhihu_cookies.txt /tmp/douyin_cookies.txt
# >1000字节 = 有效
```

---

## 常见问题

### Q: Chrome窗口打不开？
A: 检查`DISPLAY=:0`是否设置，检查Wayland兼容性。

### Q: 9222端口被占用？
A: `ss -tlnp | grep 9222`看谁占了，`systemctl --user restart google-chrome-cdp`重启服务。

### Q: Cookie提取超时？
A: 在Chrome里先打开目标网站（bilibili.com/zhihu.com/douyin.com），确保登录态活跃。

### Q: 服务挂了？
A: `systemctl --user status google-chrome-cdp`看状态，`restart`重启。服务设置了`Restart=on-failure`，崩溃会自动重启。

---

## 与监控流程的耦合

- **第〇步-己（Cookie检查）：** 先`bash ~/桌面/系统工具/chrome-cdp-一键.sh`确认服务运行，再提取cookie
- **第3.5步（抖音视频下载）：** 需要CDP Chrome有抖音登录态，才能下到完整音视频流
- **每次监控前：** 必须检查9222端口响应，不响应就`restart`
