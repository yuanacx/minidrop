# Mini-Drop 演示视频录制脚本（≤15 分钟）

> 环境：ECS `http://47.113.102.23/` 或本地 `docker compose up -d --build`  
> 录制要求：端到端 perf 链路**不剪辑**；eBPF/CP 可口述 + 终端辅助演示

---

## 0. 录制前准备（5 分钟，不入镜）

```bash
# ECS 或本地
cd /opt/minidrop   # 本地: project1_MiniDrop
docker compose ps   # 6 容器 Up
curl -s http://127.0.0.1:8191/healthz
curl -s 'http://127.0.0.1:8191/api/v1/agents?target_ip=127.0.0.1'

# 启动 CPU hog（另开终端，记下 PID）
python3 -c "i=0
while True: i+=1" &
echo "CPU_HOG_PID=$!"
# 示例 PID 下文用 $CPU_HOG_PID 代替
```

确认首页 Agent 列表显示 **在线** 及 **最后心跳时间**。

---

## 1. 开场（0:00–1:00）

**口播要点：**

- 项目名：Mini-Drop 性能分析平台复刻
- 架构：Web → apiserver → drop_server → drop_agent → MinIO → analysis
- 一键启动：`docker compose up -d --build`

**画面：** 浏览器打开首页 + `docker compose ps`

---

## 2. Agent 在线（1:00–2:00）

**画面：** 首页 Agent 列表表格

**口播：**

- Agent 每 5s 心跳；30s 无心跳判离线
- 离线/恢复写入 `agent_audit` 审计表
- host 网络 Agent 上报内网 IP，server 对 127.0.0.1 查询做回退

**可选终端（不入镜也可）：**

```bash
curl -s 'http://127.0.0.1:8191/api/v1/agents?target_ip=127.0.0.1' | python3 -m json.tool
```

---

## 3. 新建 perf 采样（2:00–4:00）

**操作（全程录屏）：**

1. 点击「新建采样」
2. 目标 IP：`127.0.0.1`
3. PID：填 CPU hog 的 PID（**勿用 pid=1**）
4. 时长：10s，Hz：99，采集器：perf
5. 点击「开始采集」

**口播：** 任务经 apiserver 写入 PostgreSQL，状态 PENDING，再下发 drop_server 队列。

---

## 4. 状态轮转 PENDING→RUNNING→DONE（4:00–7:00）

**画面：** 任务详情页，展示状态与 history 折叠区

**口播对照 history：**

| 阶段 | 状态 | reason 示例 |
|------|------|-------------|
| 创建 | PENDING | created |
| 下发 | RUNNING | dispatched to agent |
| 上传 | UPLOADING | artifact uploaded |
| 完成 | DONE | collection complete |

等待约 15–20s 直至 DONE（不跳剪）。

---

## 5. 火焰图（7:00–10:00）

**操作：**

1. 点击「生成火焰图 / 分析」
2. 等待 analysis 完成
3. 火焰图 Tab：鼠标 **移动、点击放大**（SVG 交互）

**口播：** perf.data → perf script → FlameGraph → MinIO → nginx `/artifacts/` 反代

---

## 6. TopN 与归因 Tab（10:00–11:30）

**画面：** 切换 TopN Tab、归因/建议 Tab

**口播：** TopN 来自 collapsed stack；规则建议 + 可选 LLM 归因（无 Key 时规则降级）

---

## 7. 扩展能力说明（11:30–13:00）

**口播（诚实说明 MVP 边界）：**

| 能力 | 后端 | 前端 |
|------|------|------|
| py-spy | ✅ 采集器 | ⚠️ 无独立 Tab |
| bpftrace | ✅ 采集器 | ⚠️ 演示数据为主 |
| Continuous Profiling | ✅ Agent 每 60s 上传 `cp/` | ⚠️ 无 5 分钟时间轴 |

**终端展示 CP 数据（可选 30s）：**

```bash
docker compose exec minio mc alias set local http://127.0.0.1:9000 drop dropdrop 2>/dev/null || true
docker compose exec minio mc ls local/drop/cp/ 2>/dev/null | tail -5
```

---

## 8. eBPF 现场演示（13:00–14:00，可选）

**终端 + 口播：**

```bash
# 终端 1：IO 负载
dd if=/dev/zero of=/tmp/demo_io bs=1M count=512 oflag=direct

# 终端 2：bpftrace 采集（10s）
docker compose exec drop_agent bpftrace -e 'tracepoint:block:block_rq_issue { @[comm] = count(); }' &
sleep 10
```

**口播：** eBPF 采集器已实现；Web 完整可视化因工期未做完，现场以 CLI 输出说明。

---

## 9. 收尾：最得意的设计（14:00–15:00）

**推荐讲：**

1. **国内镜像 + ECS 部署**（pip 7min → 18s）
2. **任务队列 / Agent IP 回退**（127.0.0.1 vs 内网 IP）
3. **若重做：** drop 迁 gRPC、CP 时间轴 UI、单测进 CI

**结束画面：** GitHub 链接 + `docs/DESIGN.md`

---

## 检查清单

- [ ] perf 全链路一镜到底
- [ ] 未使用 pid=1 作为主演示
- [ ] Agent 在线可见
- [ ] 状态 history 有 reason
- [ ] 火焰图可交互
- [ ] 扩展能力说明诚实、不夸大
- [ ] 总时长 ≤ 15 分钟
