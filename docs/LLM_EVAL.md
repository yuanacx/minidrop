# 智能归因评测报告（Mini-Drop）

## 方法

- 输入：analysis 产出的 TopN JSON + 任务元数据
- LLM：DeepSeek Chat + tools `get_hotspot_detail` / `compare_baseline`
- 约束：LLM 不得直接编造 samples，须通过 tool 返回 verified 字段

## 样例

无 `DEEPSEEK_API_KEY` 时降级为规则归因（Top3 热点列表）。

## 可验证性

tool 返回 `verified: true` 且 samples 与 top.json 一致即为可核对结论。

## 局限

未接腾讯混元；baseline 为静态比例，非历史库。
