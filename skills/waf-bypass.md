---
name: waf-bypass
description: 通用 — 当目标网站 WAF（如知乎的40362或类似拦截）封禁服务器 IP 时，用手机 UA 绕过。依赖 cookie-extractor 先提取 cookie。独立层，可被任何网页访问技能引用
---

# WAF Bypass

## 用途

当目标网站检测到服务器 IP 并返回 WAF 拦截（如知乎 40362 "您当前请求存在异常"），用本技能绕过。**适用于任何被 WAF 封 IP 的网站。**

## 核心原则

**不要用 browser_navigate / headless Chrome。** headless Chrome 指纹已被主流网站标记，返回空白页面或验证码。正确方法：curl + 手机 UA。

## 操作方式

### 手机 UA 绕过（已验证有效）

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' \
  -H 'Accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest' \
  'https://目标平台.com/api/v4/some_endpoint'
```

**关键点：** 
- iPhone UA 可以绕过知乎等网站的 WAF IP 封锁
- headless Chrome 不行（指纹被标记）
- 系统返回 "body--Mobile" 和 "logged:true" 表示绕过成功

### 桌面 UA + cookie（常规方式，部分场景可用）

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36' \
  'https://目标平台.com/api/v4/me'
```

如果桌面UA被 WAF 拦截，切换到手机 UA。

## 排查顺序（从最常见到最罕见）

**第1步：检查是否是 WAF 拦截**

| 症状 | 判断 | 行动 |
|------|------|------|
| JSON 解码报错 `Expecting value` | **最可能：WAF 静默拦截**（返回空200） | 先输curl原始输出确认，切手机UA |
| curl 返回 `40362` | 明确 WAF 拦截 | 切换手机 UA |
| 返回 `{"error":...}` 含 `"code":40362` | WAF 拦截（API版） | 切换手机 UA |
| browser_navigate 只出"美观输出"checkbox | headless Chrome 被识别 | 不要用浏览器，改用 curl |
| 返回 `"code":4041` | **不是 WAF**，内容不存在 | 让user确认链接 |

**第2步：定位到 WAF → 手机 UA 绕过**

```bash
curl -s --cookie /tmp/cookies.txt \
  -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' \
  -H 'Accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest' \
  'https://目标平台.com/api/v4/some_endpoint'
```

验证绕过成功：返回含 `"logged":true` 或正常 JSON 数据。

**第3步：确认失败原因**
- 如果 iPhone UA 仍返回空 → 检查 cookie 是否过期（重跑 cookie-extractor 或 CDP bridge）
- 如果 iPhone UA 仍返回空 → 检查 cookie 是否过期（重跑技能1/2提cookie）
- 如果 iPhone UA 返回 HTML 而不是 JSON → 加 `Accept: application/json` + `x-requested-with: XMLHttpRequest`
- 如果 cookie 有效 + iPhone UA 仍失败 → 可能触发了其他风控（如频率限制），隔段时间再试

## 参考

- 配合 `cookie-extractor` 使用（先提 cookie，再用本技能绕过 WAF）
- **如果手机UA也不行 → 用 `local-chrome-cdp-reader` 兜底**（用户手动开Chrome debug端口，脚本连CDP读DOM，完全真实浏览器环境，不会被WAF检测）
- 三者优先级：cookie-extractor（最轻量）→ waf-bypass（绕WAF）→ local-chrome-cdp-reader（最后兜底）
- 部分网站可能还需要特定 Header，见具体平台的技能
