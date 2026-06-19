Deepseek 文件夹 — 项目1 Mini-Drop
==================================

用途
----

存放给 DeepSeek 看的结构化答复。用户与 DeepSeek 讨论 → DeepSeek 出提示词 → Cursor 执行 → **结果写入 answerN.txt**。

answer 编号约定
---------------

answer1.txt   项目是什么、材料在哪、初始要问 DeepSeek 的问题
answer2.txt   某次 Cursor 执行任务的结果（如：阿里云 Docker 安装）
answer3.txt   项目理解、待讨论问题、排期建议、给 DeepSeek 的下一步想法
answer4.txt+  随 DeepSeek 每轮对话递增（一提示词一 answer，或合并相关步骤）

文件内建议包含：执行结果 / 失败原因 / 待 DeepSeek 决策的问题 / 给 Cursor 的下一条任务草案

其他文件
--------

structure.txt         目录树（Cursor 维护）
course_resources.txt  官方链接
Internet1.txt         本地材料摘要

给 DeepSeek 时
--------------

附带 structure.txt + 最新 answerN.txt（需要上下文时可多附前几份）
