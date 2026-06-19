#!/usr/bin/env python3
"""DeepSeek smart attribution with fixed tool schema."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_hotspot_detail",
            "description": "Get sample count for a hotspot function name",
            "parameters": {
                "type": "object",
                "properties": {"function_name": {"type": "string"}},
                "required": ["function_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_baseline",
            "description": "Compare function samples vs baseline ratio",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string"},
                    "baseline_ratio": {"type": "number"},
                },
                "required": ["function_name", "baseline_ratio"],
            },
        },
    },
]


def tool_get_hotspot_detail(topn: List[Dict], function_name: str) -> Dict[str, Any]:
    for item in topn:
        if item.get("function") == function_name:
            return {"function": function_name, "samples": item.get("samples", 0), "verified": True}
    return {"function": function_name, "samples": 0, "verified": True}


def tool_compare_baseline(topn: List[Dict], function_name: str, baseline_ratio: float) -> Dict[str, Any]:
    total = sum(x.get("samples", 0) for x in topn) or 1
    hit = next((x for x in topn if x.get("function") == function_name), {"samples": 0})
    ratio = hit.get("samples", 0) / total
    return {
        "function": function_name,
        "current_ratio": round(ratio, 4),
        "baseline_ratio": baseline_ratio,
        "regression": ratio > baseline_ratio * 1.2,
        "verified": True,
    }


def run_tools(name: str, args: Dict, topn: List[Dict]) -> Dict:
    if name == "get_hotspot_detail":
        return tool_get_hotspot_detail(topn, args.get("function_name", ""))
    if name == "compare_baseline":
        return tool_compare_baseline(
            topn, args.get("function_name", ""), float(args.get("baseline_ratio", 0.1))
        )
    return {"error": "unknown tool"}


def attribute(topn: List[Dict], metadata: Dict) -> Dict:
    """Call DeepSeek with tools; fallback to rule summary without API key."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        top = topn[:3] if topn else []
        return {
            "conclusion": "规则归因（无 API Key）",
            "hotspots": top,
            "verified": True,
            "source": "rules_fallback",
        }

    messages = [
        {
            "role": "system",
            "content": "你是性能分析助手。只能使用提供的 tools 获取事实，不得编造数据。",
        },
        {
            "role": "user",
            "content": json.dumps({"topn": topn[:10], "metadata": metadata}, ensure_ascii=False),
        },
    ]
    url = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "messages": messages, "tools": TOOLS},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choice = data["choices"][0]["message"]
    if choice.get("tool_calls"):
        tc = choice["tool_calls"][0]
        fn = tc["function"]["name"]
        args = json.loads(tc["function"].get("arguments") or "{}")
        result = run_tools(fn, args, topn)
        return {"conclusion": f"工具 {fn} 结果", "tool_result": result, "verified": True}
    return {"conclusion": choice.get("content", ""), "verified": False}


if __name__ == "__main__":
    demo = [{"function": "main", "samples": 100}, {"function": "foo", "samples": 40}]
    print(json.dumps(attribute(demo, {"task_id": "demo"}), ensure_ascii=False, indent=2))
