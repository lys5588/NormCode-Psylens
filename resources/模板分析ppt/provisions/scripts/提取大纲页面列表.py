#!/usr/bin/env python3
"""
提取大纲页面列表脚本

从对齐大纲中提取 sections 列表。

输入：{对齐大纲}
输出：[大纲页面列表] - sections 列表
"""

import json
from typing import Dict, List, Any


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> List[Dict]:
    """
    主函数 - 提取大纲页面列表
    
    Args:
        input_1: {对齐大纲}
        body: Agent body
    
    Returns:
        list: sections 列表
    """
    try:
        aligned_outline = flatten_input(input_1)
        
        if not isinstance(aligned_outline, dict):
            return []
        
        sections = aligned_outline.get("sections", [])
        
        if not isinstance(sections, list):
            return []
        
        return sections
        
    except Exception as e:
        return []


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_outline = {
        "total_slides": 6,
        "alignment_notes": "测试对齐",
        "sections": [
            {"slide_index": 0, "template_page": 0, "page_type": "title"},
            {"slide_index": 1, "template_page": 1, "page_type": "content"},
            {"slide_index": 2, "template_page": 3, "page_type": "content"}
        ]
    }
    
    result = main(input_1=test_outline)
    print(json.dumps(result, ensure_ascii=False, indent=2))

