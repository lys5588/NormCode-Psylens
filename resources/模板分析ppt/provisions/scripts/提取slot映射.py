#!/usr/bin/env python3
"""
提取 slot 映射脚本

从页面分析中提取 slot 到 shape_index 的映射。
这个映射在最后一步用于将 LLM 生成的 slot-based 内容转回 shape_index。

输入：{此页分析} - 包含 substitutable_elements 的完整分析
输出：{可更改元素映射} - slot 到 shape_index 的映射表
"""

import json
from typing import Dict, Any


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 提取 slot 到 shape_index 的映射
    
    Args:
        input_1: {此页分析} - 包含 substitutable_elements 的完整分析
        body: Agent body
    
    Returns:
        dict: 映射表 {"1": 10, "2": 11, "3": 9, ...}
    """
    try:
        page_analysis = flatten_input(input_1)
        
        if not isinstance(page_analysis, dict):
            return {
                "mapping": {},
                "error": "无法解析页面分析"
            }
        
        # 提取可替换元素
        substitutable = page_analysis.get("substitutable_elements", [])
        
        # 构建映射表
        mapping = {}
        slot_details = []  # 额外记录详情，方便调试
        
        for i, elem in enumerate(substitutable):
            slot_num = i + 1  # slot 从 1 开始
            shape_index = elem.get("shape_index")
            
            if shape_index is not None:
                # 使用字符串作为 key，方便 JSON 序列化
                mapping[str(slot_num)] = shape_index
                
                slot_details.append({
                    "slot": slot_num,
                    "shape_index": shape_index,
                    "role": elem.get("role", "")
                })
        
        return {
            "mapping": mapping,
            "details": slot_details,
            "total_slots": len(mapping)
        }
        
    except Exception as e:
        return {
            "mapping": {},
            "error": f"提取映射失败: {str(e)}"
        }


if __name__ == "__main__":
    # 测试用例
    test_analysis = {
        "index": 0,
        "page_intent": "标题页",
        "substitutable_elements": [
            {
                "shape_index": 10,
                "role": "页面标题",
                "current_text": "EDUCATIONAL TALK"
            },
            {
                "shape_index": 11,
                "role": "副标题",
                "current_text": "Creative Showcase"
            },
            {
                "shape_index": 9,
                "role": "说明文字",
                "current_text": "Academic Perspectives..."
            }
        ]
    }
    
    result = main(input_1=test_analysis)
    print("映射结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 验证映射
    print("\n验证映射：")
    for slot, shape_idx in result["mapping"].items():
        print(f"  slot {slot} → shape_index {shape_idx}")

