# CDP通用Cookie提取器

> 技能备份 — 任何AI读此文件即可重建此技能
> 对应Hermes技能：`cdp-cookie-extractor`

## 一句话

从用户Chrome提取指定网站的登录cookie → 存文件 → 供后续API调用。
**不绑定任何特定网站。** 所有技能（B站/抖音/知乎等）统一调用本模块获取cookie。

---

## 使用方式

```bash
# 通用：提取任意网站cookie
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain <域名> --output /tmp/cookies.txt

# 例子
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain bilibili.com --output /tmp/bili_cookies.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output /tmp/douyin_cookies.txt
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --output /tmp/zhihu_cookies.txt
```

## 前置条件

- Chrome调试端口9222已就绪（桌面脚本 `~/桌面/启动Chrome调试模式.sh`）
- Chrome内有对应网站的登录态（用户日常使用时会自动保持）

## 核心脚本路径

`~/.hermes/scripts/cdp-get-cookies.py` — 通用脚本，`--domain` 支持任何网站，`--test` 自动验证

## 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 主文件 | 指定的 `--output` 路径 | Cookie文件（Header格式） |
| 桌面备份 | `~/桌面/{域名}_cookie_最新.txt` | 人工备用 |
| stdout | 关键cookie名字 | 用于确认是否成功 |

## 测试cookie是否有效

```bash
# B站
curl -s -H "Cookie: $(cat /tmp/bili_cookies.txt)" \
  "https://api.bilibili.com/x/web-interface/nav" | grep -c '"isLogin":true'

# 抖音
curl -s -H "Cookie: $(cat /tmp/douyin_cookies.txt)" \
  "https://www.douyin.com/aweme/v1/web/aweme/post/" | grep -c '"status_code":0'

# 知乎
curl -s -H "Cookie: $(cat /tmp/zhihu_cookies.txt)" \
  "https://www.zhihu.com/api/v4/me" | grep -c '"name"'
```

## 在整个系统中的位置

```
⚠️ 注意：本技能是以下所有管线/技能的前置依赖
所有需要登录态的工作流（B站、抖音、知乎等）必须先调用本模块拿cookie。

┌──────────────────────────┐
│   CDP通用Cookie提取器     │  ← 通用底座
│   (任意网站cookie)       │
└────────┬─────────────────┘
         │
    ┌────┼────┬──────────┐
    │    │    │          │
    ▼    ▼    ▼          ▼
  B站  抖音  知乎   未来任何需要
  管线  监控  阅读  登录态的网站
```

## cookie有效期

| 网站 | 预估有效期 | 过期特征 |
|------|-----------|---------|
| B站 | 7-30天 | API返回 `code:-799` 或 `isLogin:false` |
| 抖音 | 7-30天 | API返回验证码/空数据 |
| 知乎 | 30天+ | API返回登录页面内容 |

**过期后重新执行本脚本即可。**

## 注意事项

1. **Chrome不能被杀掉** — 用户在用Chrome时，不要为了拿cookie重启Chrome
2. **用crontab启动Chrome调试实例** — 不干扰用户正在用的Chrome
3. **CDP端口只能连一个实例** — 不要同时跑多个Chrome调试实例
4. **cookie格式是HTTP Header格式**（`key=value; key=value`），不是Netscape格式
5. **本模块不负责具体业务** — 只管拿cookie，不管怎么用
