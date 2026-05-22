---
name: wake-screen
title: 唤醒Ubuntu屏幕（Wayland/GNOME）
description: 当系统卡死后屏幕黑屏/锁屏，通过SSH/terminal远程唤醒屏幕。无需sudo，不依赖xset（Wayland下xset不可用）。
triggers:
  - 用户说「屏幕黑了」「屏幕不亮」「桌面黑了」「喊不亮」
  - 用户说「按电源键也没亮」
---

# 唤醒Ubuntu屏幕

## 适用场景

Hermes running on Ubuntu 24.04 Wayland + GNOME. 系统因hindsight叠罗汉/oomd误杀/etc卡死后屏幕黑屏，用户说"屏幕不亮了"。

## 根本原因

系统本身没死（terminal还能跑命令），但：
1. 自动锁屏了（logind LockedHint=yes）
2. 或屏幕因DPMS休眠了
3. 或gnome-shell冻结了

## 修复流程（三步走）

### 第1步：模拟用户活动 + 解锁

```bash
# 告诉gnome-screensaver"用户回来了"
gdbus call --session --dest org.gnome.ScreenSaver \
  --object-path /org/gnome/ScreenSaver \
  --method org.gnome.ScreenSaver.SimulateUserActivity

# 解锁当前session（找到对的session号）
loginctl unlock-session 2
# 或通配解锁
loginctl unlock-sessions
```

### 第2步：关掉自动休眠（防止再黑）

```bash
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
```

### 第3步：如果还不亮，发keyboard事件

```bash
# 模拟按键（需要安装xdotool）
sudo apt install -y xdotool 2>/dev/null && \
  DISPLAY=:0 xdotool key Shift_L 2>/dev/null || \
  echo "xdotool不可用，请用户手动按一下键"
```

## 踩坑记录

- ❌ `xset dpms force on` — 在Wayland下不可用，返回" unable to open display"
- ❌ `sudo vbetool dpms on` — vbetool通常未安装
- ❌ `export DISPLAY=:0` — terminal session的认证跟桌面session不同
- ✅ `gdbus call --session` — 这是Wayland/GNOME下唯一可靠的唤醒方式
- ✅ `loginctl unlock-session` — 直接解锁，不依赖GUI
- ✅ `gsettings` — 关休眠设置，防复发

## 前置条件

**必须先释放内存！** 屏幕黑屏通常伴随系统负荷极高（hindsight叠罗汉）。
如果用户说屏幕不亮，**先杀hindsight**，再唤醒屏幕，顺序不能反：

```bash
# 先杀叠罗汉的hindsight（释放内存）
pkill -9 -f "hindsight-api" 2>/dev/null
pkill -9 -f "hindsight_api.main" 2>/dev/null
sleep 3

# 再唤醒屏幕
gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SimulateUserActivity
loginctl unlock-sessions
```

原因：系统在swap满地的情况下，解锁屏幕命令可能因I/O阻塞而无法执行，必须先释放内存让系统喘口气。
