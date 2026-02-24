#!/usr/bin/env python3
"""
提取页面列表脚本

从模板原始数据中提取页面列表。

输入：{模板原始数据}
输出：[页面列表] - 每个页面的数据
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
    主函数 - 提取页面列表
    
    Args:
        input_1: {模板原始数据}
        body: Agent body
    
    Returns:
        list: 页面列表
    """
    try:
        raw_data = flatten_input(input_1)
        
        if not isinstance(raw_data, dict):
            return []
        
        pages = raw_data.get("pages", [])
        
        if not isinstance(pages, list):
            return []
        
        return pages
        
    except Exception as e:
        return []


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_data = {
        "status": "success",
        "pages": [
            {"index": 0, "layout_name": "Title"},
            {"index": 1, "layout_name": "Content"},
            {"index": 2, "layout_name": "Content"}
        ]
    }
    
    result = main(input_1=test_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

