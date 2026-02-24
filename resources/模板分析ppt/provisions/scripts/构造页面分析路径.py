#!/usr/bin/env python3
"""
构造页面分析路径脚本

根据页面数据构造页面分析文件的保存路径。

输入：{当前页面} 或 {当前大纲页面}
输出：相对路径字符串，如 "页面分析/页面_05.json"
"""

import json
from typing import Dict, Any, Union


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> str:
    """
    主函数 - 构造页面分析路径
    
    Args:
        input_1: {当前页面} 或 {当前大纲页面}
        body: Agent body
    
    Returns:
        str: 页面分析文件的相对路径
    """
    try:
        page_data = flatten_input(input_1)
        
        if not isinstance(page_data, dict):
            return "页面分析/页面_00.json"
        
        # 尝试从不同的键获取索引
        # 优先使用 template_page，因为页面分析是针对模板页的
        index = page_data.get("template_page")
        if index is None:
            index = page_data.get("index")
        if index is None:
            index = page_data.get("slide_index")
        if index is None:
            index = page_data.get("page_index", 0)
        
        # 格式化索引为两位数
        index_str = f"{int(index):02d}"
        
        # 返回相对路径
        return f"页面分析/页面_{index_str}.json"
        
    except Exception as e:
        return "页面分析/页面_00.json"


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_page = {"index": 5, "layout_name": "Content"}
    result = main(input_1=test_page)
    print(f"Test 1 (index=5): {result}")  # 期望: 页面分析/页面_05.json
    
    # 关键测试：当 slide_index 和 template_page 不同时，应使用 template_page
    test_outline_page = {"slide_index": 2, "template_page": 3}
    result = main(input_1=test_outline_page)
    print(f"Test 2 (slide_index=2, template_page=3): {result}")  # 期望: 页面分析/页面_03.json

