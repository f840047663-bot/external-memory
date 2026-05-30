# Cookie提取

## 输入
| 参数 | 类型 | 说明 |
|:----|:----|:----|
| 平台 | 字符串 | "抖音" / "B站" / "知乎" |

## 输出（返回值）
| 字段 | 类型 | 说明 |
|:----|:----|:----|
| 状态 | ✅/❌ | 提取是否成功 |
| 文件大小 | 数字 | 保存的cookie文件大小（字节） |
| 失败原因 | 字符串 | 如果❌，返回原因 |

## 执行步骤

### Step 1：用CDP打开目标网站
```python
# 用Hermes browser_cdp工具
browser_cdp(
    method="Target.createTarget",
    params={"url": "https://目标网站.com"}
)
```

| 平台 | URL |
|:----|:----|
| 抖音 | https://www.douyin.com |
| B站 | https://www.bilibili.com |
| 知乎 | https://www.zhihu.com |

### Step 2：等用户登录
- **停顿**，提示用户："请在Chrome窗口登录{平台}"
- 用户登录完成后，继续Step 3

### Step 3：提取Cookie
```python
# 用Hermes browser_cdp工具
browser_cdp(
    method="Network.getAllCookies",
    params={},
    target_id={目标标签页ID}
)
```

### Step 4：过滤并保存
```python
# 过滤目标域名的cookie
# 保存Netscape格式到 ~/.hermes/cookies/{平台}_netscape.txt
# 同步到 ~/桌面/凭证/{平台}_cookie_最新.txt
```

## 返回值示例
```
{
  "状态": "✅",
  "平台": "B站",
  "文件大小": 1482
}
```

## 失败处理
| 故障 | 解决 |
|:----|:-----|
| 用户没登录 | 等待，不超时 |
| Cookie为空 | 提示用户检查登录状态 |
| CDP连接失败 | 调用[通用/启动CDP]重新连接 |
