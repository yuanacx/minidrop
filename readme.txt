项目1：Mini-Drop 性能分析平台复刻
==================================

状态：开发中（3 天冲刺）

执行计划
--------

详见 PLAN.md（MVP 范围、技术栈、里程碑、风险、代码量）

快速开始（ECS / Linux）
-----------------------

```bash
cd project1_MiniDrop
make proto          # 生成 gRPC stub（需 protoc）
docker compose up -d postgres minio
make demo           # 一键演示（见 Makefile）
```

目录
----

PLAN.md / docker-compose.yml / Makefile
proto/ drop/ apiserver/ analysis/ web_frontend/
docs/ tests/ Deepseek/

协作
----

DeepSeek 讨论 → answerN.txt → Cursor 执行
