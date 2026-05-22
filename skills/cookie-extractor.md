---
name: cookie-extractor
description: 通用 — 从本地 Chrome 提取登录 cookie 用于 curl/API 访问任何需要登录态的平台。用 yt-dlp，不杀用户 Chrome。被 WAF 拦截时用 waf-bypass 技能配合
---

# Cookie Extractor（通用，不挑平台）

> ⚠️ **本机 Chrome v147+，唯一可用方案是 CDP（local-chrome-cdp-bridge）。**
> yt-dlp / F12手动 等旧方案全部失效，不要试，直接走 CDP。

## 一句话

**任何需要登录态 cookie 的场景 → 直接跑 CDP 提取脚本。** 通用，不挑网站（抖音/知乎/B站/微博都行）。

## 核心命令

```bash
# 通用格式：--domain=网站域名
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --test

# 输出到桌面（推荐，方便下次直接用）
python3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output ~/桌面/ --netscape
```

## 前置条件

- Chrome 9222 端口正在监听（用户正常浏览时即有）或 系统已有桌面cookie文件
- Chrome 已登录目标网站（首次需要用户手动登录一次，后续CDP自动持会话）

## 完整流程（5步，自己执行不等人）

```
1. 检查桌面已有cookie → ls ~/桌面/*cookie* 2>/dev/null
   → 有有效文件 → 直接用（跳到第5步）

2. 没有/过期了 → 跑CDP提取
   → python3 ~/.hermes/scripts/cdp-get-cookies.py --domain <网站> --test
   → 脚本自动连接Chrome 9222端口，提取cookie，保存到桌面

3. 验证有效性 → curl测试调目标站API
   → curl -H "Cookie: $(cat ~/桌面/<domain>_cookie_最新.txt)" <API_URL>

4. 把cookie复制到标准位置供监控脚本使用
   → cp ~/桌面/<domain>_cookie_最新.txt /tmp/<domain>_cookies.txt

5. 干活（调API/读帖/监控等，用对应技能）
```

## 铁律

1. **绝对不要叫用户手动F12取cookie** — CDP自动方案已验证可行，不需要也不应该让用户碰
2. **不要杀用户Chrome** — 重大事故历史，杀了也重启不了（Wayland依赖）
3. **CDP是唯一方案** — yt-dlp已废（v11加密不可破解），别试
4. **先检查桌面已有cookie文件** — 桌面 `~/桌面/*cookie*.txt` 可能还有效，先 `ls` 再看
5. **cookie约7-30天过期** — 过期重跑CDP即可，用户登录态保持就不需要再手动登录

## 输出

- 桌面：`~/桌面/{domain}_cookie_最新.txt`（raw header格式，用户可见）
- 临时：`/tmp/{domain}_cookies.txt`（脚本用）
- 格式：`key=value; key=value; ...`

## 配套脚本

| 脚本 | 用途 | 适用Chrome版本 |
|:----|:-----|:------------|
| `~/.hermes/scripts/cdp-get-cookies.py` | **通用CDP提取（唯一推荐）** — --domain参数，--test验证，--output输出 | v147+ ✅ |
| `~/.hermes/skills/devops/cookie-extractor/scripts/get_cookie.py` | 旧版yt-dlp方案 | < v147 ⚠️ |

## 参考

- `local-chrome-cdp-bridge` 技能 — CDP全自动启动+提取流程（含Chrome重启方法）
- `00-网站内容抓取总纲.md` — 三件套积木架构（cookie→waf→平台读帖）
- `waf-bypass` 技能 — 被WAF拦住时用手机UA绕过

1. **需要 Chrome 正在运行** — yt-dlp 需要访问 Chrome 的加密 cookie 存储
2. **cookie 会过期** — z_c0 等关键 cookie 有效期有限，失效了重跑 Step 1
3. **输出是 Netscape 格式** — curl 的 `--cookie` 直接认
4. **不要杀用户 Chrome** — 重大事故
5. **`[*]` 在 shell 中会被 glob 展开** — URL 必须用单引号包裹，不能用双引号
6. **如果被 WAF 拦截** — 不要继续硬碰硬，加载 `waf-bypass` 技能
7. **⚠️ Chrome v147+ 自动升级会静默摧毁本技能** — v11 cookie 加密导致 yt-dlp 无法提取关键 cookie。用户说"昨天可以今天不行"时，查 Chrome 版本。`google-chrome --version` 如果 ≥147，直接切到 `local-chrome-cdp-bridge`，不要反复试 yt-dlp。
8. **yt-dlp 输出 `Extracted 44 cookies from chrome (185 could not be decrypted)` 是危险信号** — 44 个非登录 cookie 看似提取成功，但关键的 z_c0/sessionid 等属于那 185 个无法解密的。**不要被"Extracted"字眼骗了，必须验证是否能调通目标站点的登录 API。**
9. **Chrome v147 加密密钥在 GNOME Keyring 中，不在 Local State 文件** — 老版在 `~/.config/google-chrome/Local State` → `os_crypt.encrypted_key`。v147 改用 `os_crypt.portal` 元数据 + GNOME Keyring 中 `org.freedesktop.portal.Secret` schema 下的 `Application key for com.google.Chrome`。直接读 Local State 会报 `KeyError: 'encrypted_key'`。详见 `references/chrome-v147-cookie-encryption.md`。
10. **⚠️ 桌面脚本优先检查** — 碰到cookie问题，**第一步**必须是 `ls /home/fw/桌面/*cookie* /home/fw/桌面/*提取*.desktop 2>/dev/null`。如果桌面上有现成的 `提取知乎Cookie.desktop` 或 `zhihu_cookie.txt`，**直接用，不要自己写新的提取逻辑**。用户会因此发火。
11. **用户要求模块化解耦（铁律）** — 提取cookie → 保存文件 → 用cookie调API → 解析结果，每一步拆成独立脚本存在 `.hermes/scripts/` 或技能目录下。不要把所有逻辑写在一个大文件里。忘记桌面脚本=用户发火。
12. **Chrome v147+ 的 v11 加密目前不可破解（2026-05-18 结论）** — portal key 拿到了也解密不了。不要尝试任何 Python 解密方案，直接走 F12 手动或 CDP。

## 手动兜底（当所有自动方法失败时）

告诉用户在 Chrome 中按 F12 → Console → 粘贴下面代码，把结果发给我：

```javascript
console.log(document.cookie)
```

拿到 cookie 字符串后，直接用 curl 调目标站点 API。

## 参考

- `waf-bypass` 技能 — 当 cookie 成功但被 WAF 拦截时用手机 UA 绕过
- `local-chrome-cdp-bridge` 技能 — 当 cookie 提取失败或 WAF 封 IP 时的兜底方案
- **三件套原则：** cookie-extractor → waf-bypass → CDP bridge。任意网站被抓，按这个顺序试。失败立即切下一方案，不要在同一方案上反复试。
- `references/chrome-v147-cookie-encryption.md` — Chrome v147 新加密格式详解

## 输出

文件：`/tmp/cookies.txt`（Netscape cookie 格式）

## 配套脚本

| 路径 | 用途 | Chrome版本 |
|------|------|-----------|
| `/home/fw/.hermes/scripts/get_zhihu_cookie.py` | **旧版** — 仅zhihu，仅读 `encrypted_key`，Chrome v147 上会报错。已弃用。 | v10 可用，v147+ 不可用 |
| `/home/fw/.hermes/skills/devops/cookie-extractor/scripts/get_cookie.py` | **通用版v1** — `--domain` 参数指定目标站，支持 Chrome v10/v11 检测 + GNOME Keyring 回退。v11 会告知不可解。 | v10 可用，v147+ 报告v11后失败 |
| `/home/fw/.hermes/scripts/cdp-get-cookies.py` | **CDP通用版 (v147+ 唯一方案)** — 通过Chrome调试端口WebSocket提取，无需解密。**2026-05-19验证通过。** | v147+ 唯一可用方案 |

**使用方式（通用版）：**\n```bash\n# Chrome < v147\npython3 ~/.hermes/skills/devops/cookie-extractor/scripts/get_cookie.py --domain zhihu.com\npython3 ~/.hermes/skills/devops/cookie-extractor/scripts/get_cookie.py --domain zhihu.com --output ~/桌面/\n\n# Chrome v147+（唯一方案，全自动）\npython3 ~/.hermes/scripts/cdp-get-cookies.py --domain zhihu.com --test\npython3 ~/.hermes/scripts/cdp-get-cookies.py --domain douyin.com --output ~/桌面/ --netscape\n```
