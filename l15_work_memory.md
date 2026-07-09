# L1.5 工作记忆（不可清理）
> 物理外挂L2，平级同层。保存当前活跃任务的关键进度、状态、变量。
> 更新日期：2026-07-09 12:05

---

## 当前主任务：任泽平抖音视频转录+归档

### 状态：第2条已完成，继续第3~5条

### 已完成进度
| # | 视频 | aweme_id | 文件 | 转录 | 归档 |
|---|------|----------|------|------|------|
| 1 | 空头将被逼翻多，AI科技业绩炸裂 | 7660460742059035955 | ✅ 29.2MB | ✅ 891字逐字稿 | ⏳ |
| 2 | 对市场争议的看法，千金难买牛回头 | 7660085720370973971 | ✅ 31.4MB | ✅ ~1200字逐字稿 | ⏳ |
| 3 | AI是我们这一代人最重要的机会 | 7660051721091140918 | ✅ 6.1MB | ✅ 200字 | ✅ ID=5099 |
| 4 | 下半年美联储放水，科技牛音乐继续 | 7659709791081729330 | ✅ 21MB | ✅ 600字 | ✅ ID=5100 |
| 5 | 在硅谷，我看到ai改变世界 | 7659660829557525787 | ✅ 24MB | ✅ 500字 | ✅ ID=5101 |

### 技术记录
- **容器**: videocaptioner (Up healthy), 镜像: ghcr.io/weifeng2333/videocaptioner:latest
- **Volume权限**: 损坏！~/.hermes/videocaptioner/videos/ 不能直接cp
- **视频入容器方法**: 下载到/tmp/ → `docker cp /tmp/xxx.mp4 videocaptioner:/app/videos/`
- **转录方法**: `docker exec videocaptioner python3 -c "...BcutASR..."` → video2audio + BcutASR.run()
- **转录结果**: 容器内 /app/output/xxx.srt + 即时全文输出
- **视频地址**: api.amemv.com/aweme/v1/play/?video_id=... (play_addr url_list[-1])
- **sec_uid**: MS4wLjABAAAA2Cp4dE8SUB9QqjXOpcm_7SblIW0UwgyqZD68lT4tVEgliq0l3i6qzajzsPADzarv

### 待归档
- 第1条逐字稿 + 核心观点摘要 → events文件 + 数据库
- 第2条逐字稿 + 核心观点摘要 → events文件 + 数据库

### 下几步计划
1. 下载第3~5条视频（并行下载提升效率）
2. 第3条转录
3. 第4条转录（可并行，但容器CPU4G内存限制，建议串行）
4. 第5条转录
5. 三条逐字稿全部归档到events + 数据库
6. 联合分析任泽平近期核心观点

---

## 其他活跃任务
- 知乎16:00 cron (10cb8ee72d02): 正常运行中
- 徐小范/美刀哥监控: 正常

---

## 关键变量
- HOME: /home/fw
- DB: ~/.hermes/external_memory/investment.clean.db
- INDEX.md: ~/.hermes/external_memory/thinkers/INDEX.md
- Events: ~/.hermes/external_memory/events/
