#!/usr/bin/env python3
"""
提取路径脚本

从结果字典中提取路径字段。

输入：{结果字典}
输出：路径字符串
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
    主函数 - 提取路径
    
    Args:
        input_1: {结果字典} - 包含 output_path 或 path 字段
        body: Agent body
    
    Returns:
        str: 提取的路径
    """
    try:
        result = flatten_input(input_1)
        
        if not isinstance(result, dict):
            return ""
        
        # 尝试不同的路径键
        path = result.get("output_path")
        if not path:
            path = result.get("path")
        if not path:
            path = result.get("location")
        if not path:
            path = result.get("file_path")
        if not path:
            path = ""
        
        return str(path)
        
    except Exception as e:
        return ""


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_result = {
        "status": "success",
        "output_path": "/path/to/output.pptx",
        "slides_count": 6
    }
    
    result = main(input_1=test_result)
    print(result)

