# 思想家档案索引（Thinkers Archive）— ★唯一主数据源★

> **监控脚本从此文件读取博主列表，不再读独立txt文件。**
> 改博主信息→改这里→监控脚本自动同步。

## 主表

| 博主 | 抖音 | B站 | 知乎 | 权重 | 建档 | 互锁仓位 |
|:----|:----|:----|:----|:----:|:----:|:---------|
| 付鹏的财经世界 | `MS4wLjABAAAAOtfT2LnLtcm4Z2_ahJZRxRV5HPJyLRlAo-lSV7P1wVW2v7J5w3-6T9HgU_bEVU60` | `space.bilibili.com/3546832705685582`（财经大咖录·常驻） | — | ⭐⭐⭐⭐⭐ | 05-19 | 芯片、恒生科技、黄金、债券 |
| 蒋宇飞商业 | `MS4wLjABAAAACny9yd6GiSgFyyTvE6jt44j0VxBKVVhe69GdklIZIL4` | — | — | ⭐⭐⭐⭐ | 05-20 | 芯片、有色、海外科技 |
| 宋鸿兵观天下 | `MS4wLjABAAAAzaye_V0qtP4d7m77UywUBRq7xB9CRiLaeGPfg79hLtQ` | `mid:390894226` | — | ⭐⭐⭐⭐⭐ | 05-19 | 黄金、芯片、银行、原油 |
| 岩松笔记 | `MS4wLjABAAAAKmBn1W1OtE3A2O79hh_R-HIAMHBX8iuTyoQhGMVVqg3nZMcZiJSfJp8qPCUuOnXc` | — | — | ⭐⭐⭐⭐ | 05-19 | 有色、稀有金属、黄金 |
| 无知半人 | 🔍待补充sec_uid | — | — | ⭐⭐⭐ | 05-22 | 银行、养殖 |
| 拿幸·AI启示录 | `MS4wLjABAAAAYiyWLrWJmy2JDr3EaQYGNOD9z2ZTCYIOgIXnckGDZYZmyAIMpnZtU99Wr6WpXdbN` | — | — | ⭐⭐⭐ | 05-22 | AI、芯片（待分析） |
| 生猪贸易~芳姐(山东) | `MS4wLjABAAAA84Px8FIb4E4UdQowhWdw_ZhHjXLQA_TeUJv7TygncxMxO-NGSfd5G--s0L66E36w` | — | — | ⭐⭐⭐ | 05-22 | 养殖（猪周期） |
| 猪猪女王 | `MS4wLjABAAAA9akoFc9rg5UbgoNGRED9mf4NI1X0doHdmglkhrN-SWo` | — | — | ⭐⭐⭐ | 05-22 | 养殖（猪周期） |
| 但斌 | `MS4wLjABAAAA4b19SkuGGVJCNpzGEiPdmvtIuI86lMLV415tjfA2KTw` | — | — | ⭐⭐⭐⭐ | 05-22 | 芯片（美银预警）、纳指 |
| 飞阅硬核财经 | `MS4wLjABAAAAGhkQZE8oAPGw2HoVyyCAAEK3niXCe_2GhrwmL_qePZTTuVdiMgNh21kNEXHcpTp_` | — | — | ⭐⭐⭐ | 05-22 | 个股分析（待分类） |
| 长坡厚雪 | `MS4wLjABAAAAHxYcDidnyJe_0c8b8fwU0725ODtyWYoiOsg8Q0TKUg0` | — | — | ⭐⭐⭐ | 05-22 | 价值投资（腾讯、泡泡玛特） |
| 闭眼看世界 | `MS4wLjABAAAAr_z1wGRb1oFflUusY0OYxeoJEs6msQoD16kBaSil9Ghl1ptC5mnKQ0PbPISvYdTR` | — | — | ⭐⭐⭐ | 05-22 | 地缘/国际（间接影响黄金） |
| 伊娃新营销 | `MS4wLjABAAAA6iF4GTOZwszOizo6WSZxfBUE_sR88Az5DkBVcDR4RJE` | — | — | ⭐⭐ | 05-22 | 养殖（猪周期，新营销视角） |
| 古都闲云 | — | — | `people/gududatong` | ⭐⭐⭐⭐ | 05-19 | 银行、芯片、债券 |
| 明珠是只猪（明珠十主） | — | — | `people/liu-bei-14-54` | ⭐⭐⭐ | 05-19 | 通用方法论 |
| 环中星鉴 | — | — | `people/lrc-8` | ⭐⭐⭐ | 05-21 | 黄金（独立投资人，INTJ） |
| 闻号说经济 | — | — | `people/wen-hao-roy` | ⭐⭐ | 05-21 | 宏微观（16年全球化企业+金融风控） |
| 华夏基金官方账号 | — | `mid:443551651` | — | ⭐⭐⭐⭐ | 05-22 | 芯片、黄金 |
| 芭蕉凉气多 | — | `video/BV16HoyBKEa8`（水果健康频道） | — | ⭐⭐ | 05-15 | 健康（不碰投资） |

> **标记说明：** 🔍待补充 = 等CDP连上或你提供后补。`—` = 该平台无账号。
> **格式：** 抖音列写`MS4w...`(sec_uid)，B站列写`mid:数字`，知乎列写`people/xxx`
> 监控脚本自动识别这三列的格式，不用额外配置。

## 脚本读取说明

监控脚本读此文件时：
1. 扫描每行的「抖音」「B站」「知乎」三列
2. 抖音列有 `MS4w...` → 加进抖音监控
3. B站列有 `mid:` 或 `space.bilibili.com/` → 加进B站监控
4. 知乎列有 `people/xxx` → 加进知乎监控
5. `🔍待补充` 或 `—` → 跳过不监控

## 权重规则

| 等级 | 含义 | 贝叶斯影响 |
|:----:|:----|:----------|
| ⭐⭐⭐⭐⭐ | 极高置信度（有产业实操/历史验证） | +3pp/条 |
| ⭐⭐⭐⭐ | 高置信度（长期跟踪，逻辑清晰） | +2pp/条 |
| ⭐⭐⭐ | 中等（观点有参考价值但需验证） | +1pp/条，上限-8pp |
| ⭐⭐ | 低（特定领域参考） | 不直接影响P值 |
