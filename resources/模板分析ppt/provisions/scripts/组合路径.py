#!/usr/bin/env python3
"""
组合路径脚本

将基础目录和相对路径组合成完整路径。

输入：{基础目录}, {相对路径}
输出：完整路径字符串
"""

from pathlib import Path
from typing import Dict, Any, Union


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, input_2=None, body=None, **kwargs) -> str:
    """
    主函数 - 组合路径
    
    Args:
        input_1: 基础目录
        input_2: 相对路径
        body: Agent body
    
    Returns:
        str: 组合后的完整路径
    """
    try:
        base_dir = flatten_input(input_1)
        relative_path = flatten_input(input_2)
        
        if not isinstance(base_dir, str):
            base_dir = str(base_dir) if base_dir else ""
        if not isinstance(relative_path, str):
            relative_path = str(relative_path) if relative_path else ""
        
        # 组合路径
        if base_dir and relative_path:
            combined = str(Path(base_dir) / relative_path)
        elif base_dir:
            combined = base_dir
        elif relative_path:
            combined = relative_path
        else:
            combined = ""
        
        return combined
        
    except Exception as e:
        return f"ERROR: {str(e)}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        result = main(sys.argv[1], sys.argv[2])
        print(result)
    else:
        print("用法: python 组合路径.py <基础目录> <相对路径>")

