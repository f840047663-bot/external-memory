# Cookie检查

## 输入
- 无（模块内部读取cookie文件）

## 输出（返回值）
| 字段 | 类型 | 说明 |
|:----|:----|:----|
| 抖音 | ✅/❌ | cookie是否有效 |
| B站 | ✅/❌ | cookie是否有效 |
| 知乎 | ✅/❌ | cookie是否有效 |
| 详情 | 字符串 | 每个cookie文件大小 |

## 执行步骤

### Step 1：检查文件大小
```bash
ls -la ~/.hermes/cookies/*_netscape.txt
```

### Step 2：判断有效性
| 文件大小 | 状态 |
|:--------|:-----|
| >1000字节 | ✅ 有效 |
| 500-1000字节 | ⚠️ 可疑，建议刷新 |
| <500字节 | ❌ 过期，必须刷新 |

### Step 3：同步到桌面凭证（如果Hermes目录有更新）
```bash
cp ~/.hermes/cookies/bilibili_netscape.txt ~/桌面/凭证/bilibili_com_cookie_最新.txt
cp ~/.hermes/cookies/douyin_netscape.txt ~/桌面/凭证/douyin_com_cookie_最新.txt
cp ~/.hermes/cookies/zhihu_netscape.txt ~/桌面/凭证/zhihu_com_cookie_最新.txt
```

## 返回值示例
```
{
  "抖音": "✅",
  "B站": "✅", 
  "知乎": "❌",
  "详情": "抖音:6604B, B站:1482B, 知乎:480B"
}
```

## 失败处理
- 文件不存在 → 返回❌，提示需要提取
- 文件大小不足 → 返回❌，提示需要刷新
