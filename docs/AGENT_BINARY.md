# drop_agent 独立二进制

## 构建

### Linux（ECS / Ubuntu 22.04，推荐）

```bash
cd drop
bash build_agent.sh
# 产物: drop/dist/drop_agent  (~18MB ELF x86_64)
```

### Windows（本地开发验证）

```powershell
cd drop
python -m pip install pyinstaller -r requirements.txt
python -m PyInstaller --clean --noconfirm drop_agent.spec
# 产物: drop/dist/drop_agent.exe  (~12MB)
```

> **注意**：Windows 生成的 `.exe` 无法在 Linux ECS 上运行；生产部署必须在 Linux 上构建。

## 运行

```bash
export DROP_SERVER=http://127.0.0.1:50051
export APISERVER=http://127.0.0.1:8191
export AGENT_ID=agent-1
export MINIO_ENDPOINT=127.0.0.1:9000
export MINIO_ROOT_USER=drop
export MINIO_ROOT_PASSWORD=dropdrop
export MINIO_BUCKET=drop
# 需要 root/capabilities 以使用 perf
sudo ./dist/drop_agent
```

CLI：`--help` / `--version`

## 依赖说明

PyInstaller 仅打包 **Python 代码**（requests、minio、collectors）。以下工具需在宿主机 PATH 中单独安装：

| 工具 | 用途 |
|------|------|
| `perf` | perf 采集 + CP |
| `py-spy` | py-spy 采集器（可选） |
| `bpftrace` | eBPF 采集器（可选） |

Docker 方式仍推荐用于一键 demo；独立二进制满足群聊「Agent standalone executable」要求。

## ECS 验证（2026-06-20）

- 构建：`/opt/minidrop/drop/dist/drop_agent` 18MB ELF
- 安装：`/opt/minidrop/bin/drop_agent`
- `drop_agent --version` → `drop_agent 0.1.0`
- 12s 心跳测试 → `list_agents` 返回 online + last_seen
