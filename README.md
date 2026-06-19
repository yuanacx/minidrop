# Mini-Drop

Mini-Drop 性能分析平台复刻（项目1）。

## 要求

- Linux（Ubuntu 22.04），Docker + Compose
- `perf_event_paranoid <= 1` 或容器 privileged
- 可选：`DEEPSEEK_API_KEY` 用于智能归因

## 快速开始

```bash
docker compose up -d --build
# Web: http://localhost  API: :8191
make test
bash tests/e2e/run_e2e.sh
```

## 目录

见 PLAN.md 与 docs/DESIGN.md
