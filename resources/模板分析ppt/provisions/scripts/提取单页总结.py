#!/usr/bin/env python3
"""
提取单页总结脚本

从页面分析结果中提取简化总结，用于生成简化概览。

输入：{页面分析}
输出：{单页总结} - 简化的页面信息
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
    主函数 - 提取单页总结
    
    Args:
        input_1: {页面分析} - 包含详细分析的字典
        body: Agent body
    
    Returns:
        dict: 简化总结
    """
    try:
        page_analysis = flatten_input(input_1)
        
        if not isinstance(page_analysis, dict):
            return {
                "index": 0,
                "page_type": "unknown",
                "purpose": "无法解析",
                "text_slots_count": 0,
                "suitable_for": [],
                "usage_notes": ""
            }
        
        # 提取基础信息
        index = page_analysis.get("index", 0)
        page_intent = page_analysis.get("page_intent", "")
        if isinstance(page_intent, dict):
            page_type = page_intent.get("type", "content")
            purpose = page_intent.get("primary_purpose", "内容展示")
        else:
            page_type = str(page_intent) if page_intent else "content"
            purpose = page_type
        
        # 提取可替换元素数量
        substitutable = page_analysis.get("substitutable_elements", [])
        text_slots_count = len(substitutable) if isinstance(substitutable, list) else 0
        
        # 提取适用场景
        best_for = page_analysis.get("best_for", [])
        if not isinstance(best_for, list):
            best_for = []
        
        # 提取使用说明
        usage_notes = page_analysis.get("usage_notes", "")
        
        # 构建简化总结
        summary = {
            "index": index,
            "page_type": page_type,
            "purpose": purpose,
            "text_slots_count": text_slots_count,
            "suitable_for": best_for,
            "usage_notes": usage_notes
        }
        
        return summary
        
    except Exception as e:
        return {
            "index": 0,
            "page_type": "error",
            "purpose": f"提取失败: {str(e)}",
            "text_slots_count": 0,
            "suitable_for": [],
            "usage_notes": ""
        }


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_analysis = {
        "index": 5,
        "page_intent": {
            "type": "三栏内容页",
            "primary_purpose": "展示三个并列的概念"
        },
        "best_for": ["展示三个核心特点", "流程步骤说明"],
        "substitutable_elements": [
            {"shape_index": 10, "role": "页面标题"},
            {"shape_index": 4, "role": "Block1标题"},
            {"shape_index": 7, "role": "Block1说明"},
            {"shape_index": 5, "role": "Block2标题"},
            {"shape_index": 8, "role": "Block2说明"},
            {"shape_index": 6, "role": "Block3标题"},
            {"shape_index": 9, "role": "Block3说明"}
        ],
        "usage_notes": "适合需要并列展示3个概念的场景"
    }
    
    result = main(input_1=test_analysis)
    print(json.dumps(result, ensure_ascii=False, indent=2))

