#!/usr/bin/env python3
"""
简化页面分析脚本

将页面分析转换为简化的 slot 格式，隐藏 shape_index 复杂性。
LLM 只需要看 slot 1, 2, 3... 而不是具体的 shape_index。

输入：{此页分析} - 包含 substitutable_elements 的完整分析
输出：{分析简化版本} - 用 slot 编号代替 shape_index
"""

import json
from typing import Dict, Any, List


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 简化页面分析
    
    Args:
        input_1: {此页分析} - 包含 substitutable_elements 的完整分析
        body: Agent body
    
    Returns:
        dict: 简化版本，用 slot 代替 shape_index
    """
    try:
        page_analysis = flatten_input(input_1)
        
        if not isinstance(page_analysis, dict):
            return {
                "page_intent": "unknown",
                "slots": [],
                "error": "无法解析页面分析"
            }
        
        # 提取基础信息
        page_intent = page_analysis.get("page_intent", "")
        narrative_structure = page_analysis.get("narrative_structure", "")
        usage_notes = page_analysis.get("usage_notes", "")
        
        # 提取可替换元素并转换为 slot 格式
        substitutable = page_analysis.get("substitutable_elements", [])
        slots = []
        
        for i, elem in enumerate(substitutable):
            slot_num = i + 1  # slot 从 1 开始
            
            # 提取约束条件
            constraints = elem.get("constraints", {})
            max_chars = constraints.get("max_chars", 100)
            
            slot = {
                "slot": slot_num,
                "role": elem.get("role", f"元素{slot_num}"),
                "intent": elem.get("intent", ""),
                "content_type": elem.get("content_type", "文本"),
                "max_chars": max_chars,
                "current_text": elem.get("current_text", "")
            }
            
            # 如果有 block 归属，也保留
            if "belongs_to_block" in elem:
                slot["belongs_to_block"] = elem["belongs_to_block"]
            
            slots.append(slot)
        
        # 构建简化版本
        simplified = {
            "page_intent": page_intent,
            "narrative_structure": narrative_structure,
            "slots": slots,
            "usage_notes": usage_notes,
            "total_slots": len(slots)
        }
        
        return simplified
        
    except Exception as e:
        return {
            "page_intent": "error",
            "slots": [],
            "error": f"简化失败: {str(e)}"
        }


if __name__ == "__main__":
    # 测试用例
    test_analysis = {
        "index": 0,
        "page_intent": "标题页",
        "narrative_structure": "引言式结构",
        "substitutable_elements": [
            {
                "shape_index": 10,
                "role": "页面标题",
                "intent": "概括整页主题",
                "content_type": "短语",
                "constraints": {"max_chars": 25},
                "current_text": "EDUCATIONAL TALK"
            },
            {
                "shape_index": 11,
                "role": "副标题",
                "intent": "补充说明页面主题",
                "content_type": "句子",
                "constraints": {"max_chars": 30},
                "current_text": "Creative Showcase"
            },
            {
                "shape_index": 9,
                "role": "说明文字",
                "intent": "传达核心议题与学术深度",
                "content_type": "1-2句话",
                "constraints": {"max_chars": 100},
                "current_text": "Academic Perspectives on\nEmerging Challenges and Solutions"
            }
        ],
        "usage_notes": "适合需要快速建立专业感与创意氛围的场景"
    }
    
    result = main(input_1=test_analysis)
    print("简化结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 验证 shape_index 已被隐藏
    result_str = json.dumps(result)
    if "shape_index" in result_str:
        print("\n❌ 错误：输出中仍包含 shape_index！")
    else:
        print("\n✅ 成功：shape_index 已被隐藏，只有 slot 编号")

