#!/usr/bin/env python3
"""
构造页面内容路径脚本

根据大纲页面数据构造页面内容文件的保存路径。

输入：{当前大纲页面}
输出：相对路径字符串，如 "幻灯片/幻灯片_01_内容.json"
"""

import json
from typing import Dict, Any


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> str:
    """
    主函数 - 构造页面内容路径
    
    Args:
        input_1: {当前大纲页面}
        body: Agent body
    
    Returns:
        str: 页面内容文件的相对路径
    """
    try:
        outline_page = flatten_input(input_1)
        
        if not isinstance(outline_page, dict):
            return "幻灯片/幻灯片_01_内容.json"
        
        # 尝试从不同的键获取索引（优先使用 slide_index）
        index = outline_page.get("slide_index")
        if index is None:
            index = outline_page.get("index")
        if index is None:
            index = outline_page.get("page_index", 0)
        
        # 格式化索引为两位数（slide_index 从0开始，显示时+1）
        display_index = int(index) + 1
        index_str = f"{display_index:02d}"
        
        # 返回相对路径
        return f"幻灯片/幻灯片_{index_str}_内容.json"
        
    except Exception as e:
        return "幻灯片/幻灯片_01_内容.json"


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_outline_page = {"slide_index": 0, "template_page": 0, "page_type": "title"}
    result = main(input_1=test_outline_page)
    print(result)  # 应输出: 幻灯片/幻灯片_01_内容.json
    
    test_outline_page_2 = {"slide_index": 5, "template_page": 3, "page_type": "content"}
    result = main(input_1=test_outline_page_2)
    print(result)  # 应输出: 幻灯片/幻灯片_06_内容.json

