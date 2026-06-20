# Mini-Drop 3 天执行计划

> 落地版：与 Cursor Plan 一致。官方材料见 `INITIAL/Mini-Drop+题目.md`、`INITIAL/drop系统复刻指南.md`。

## 前提与目标对齐

| 项 | 决策 |
|----|------|
| 周期 | **3 天全力冲刺**，尽量贴近官方完整要求 |
| 开发机 | Windows 10 → 同步阿里云 `47.113.102.23` |
| drop | **Python 简化版** + `grpcio` + subprocess `perf record` |
| 存储 | **MinIO** 替代 COS |
| 加分项 | **智能归因**（DeepSeek API + tool schema） |

**诚实评估**：官方 14 天 × 4 人排期；3 天采用「最小合规实现 + 文档说明取舍」。

---

## 1. MVP / 扩展 / 加分 范围

### 1.1 基础能力 6 条 — 全部必做

| # | 策略 | 验收 |
|---|------|------|
| 1 | POST /tasks + gRPC CreateTask + agent 拉任务 | 前端/ curl 可建任务 |
| 2 | perf → MinIO → NotifyResult → analysis | MinIO 有 perf.data |
| 3 | perf script → flamegraph → SVG + TopN | Web iframe 可见 |
| 4 | PENDING→RUNNING→UPLOADING→DONE/FAILED + history.reason | 每次迁移落库 |
| 5 | 5s 心跳，30s 离线，agent_audit | Agent 列表 online/offline |
| 6 | 结构化日志；单测集中在 analysis/状态机；3 E2E | make test |

apiserver MVP **8 个核心 API**（非指南 12 个全做）。

### 1.2 扩展能力 — 全部必做（简化）

| 扩展 | 方案 |
|------|------|
| Continuous Profiling | agent 每 60s 采 10s perf → MinIO `cp/{unix}.data`；Web 时间轴选 5 分钟窗口 |
| eBPF | **bpftrace** biolatency → JSON → ECharts Tab |
| 用户态 | **py-spy** → 独立 SVG Tab |

### 1.3 加分项

- **智能归因**：DeepSeek + tools `get_hotspot_detail` / `compare_baseline`
- **自然语言采集**：不做（写入设计文档「若有 7 天」）

---

## 2. 开发顺序与代码量

| 阶段 | 工时 | 产出 | 代码量 |
|------|------|------|--------|
| proto | 4h | `proto/` | ~200 行 |
| infra | 4h | docker-compose, Makefile | ~150 行 |
| analysis | 6h | 火焰图/TopN/规则 | ~400–600 行 |
| drop Python | 10h | server + agent + 采集器 | ~900–1400 行 |
| apiserver Go | 10h | Gin + GORM + gRPC | ~1800–2800 行 |
| web_frontend | 8h | React + TDesign | ~1800–2500 行 |
| 归因/测试/文档 | 8h | docs, tests | ~800 行 |

**合计约 6,000–8,500 行**（官方 Drop 5 万+ 行）。

---

## 3. 技术栈

| 模块 | 选型 | 说明 |
|------|------|------|
| drop | Python + grpcio + subprocess | privileged + pid:host |
| apiserver | Go + Gin + GORM + PostgreSQL | 8 API；dev cookie 鉴权 |
| analysis | Python + flamegraph.pl + minio | Dockerfile 装 perf/perl |
| web | React + TDesign + axios | 火焰图 iframe SVG |
| LLM | DeepSeek API | 替代混元 |

Go 降级预案：Day2 18:00 不通则 apiserver 临时 FastAPI（文档记录）。

---

## 4. 三天里程碑

### Day 1
- docker compose up postgres minio
- analysis 对 perf.data 出 SVG
- proto 编译通过

### Day 2
- curl 建任务 → agent 采集 → MinIO → DONE
- 状态机 + 心跳 + audit

### Day 3
- Web 全链路 + py-spy/bpftrace/CP + 归因 + make test + 设计文档

---

## 5. 风险与缓解

见 Plan 原文 §5（3 天排期、Go 不熟、perf/eBPF 权限、CORS、单测 50%、Windows 无 perf）。

---

## 6. 目录结构

```
project1_MiniDrop/
├── PLAN.md
├── docker-compose.yml
├── Makefile
├── proto/
├── drop/
├── apiserver/
├── analysis/
├── web_frontend/
├── docs/
├── tests/
└── Deepseek/
```

---

## 7. 当前进度

| 项 | 状态 |
|----|------|
| PLAN.md | ✅ |
| Day1 infra + analysis + proto | ✅ 已创建 |
| Day2 drop + apiserver | ✅ 已创建 |
| Day3 web + ext + tests + docs | ✅ 骨架已创建；ECS 联调 ✅ |
| P0 演示脚本 | ✅ `docs/DEMO_VIDEO.md` |
| P1 单测 + 审计 + 30s 离线 | ✅ |
| P2 py-spy / eBPF / CP Tab | ✅ |
| **P3 Agent 独立二进制** | ✅ PyInstaller `drop/dist/drop_agent`（Linux 18MB）；ECS 心跳验证通过；见 `docs/AGENT_BINARY.md` |
