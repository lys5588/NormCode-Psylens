#!/usr/bin/env python3
"""
加载页面分析脚本

从指定路径加载页面分析 JSON 文件。

输入：{输出目录}, {页面分析路径}
输出：{此页分析} - 页面分析数据
"""

import json
import re
from pathlib import Path
from typing import Dict, Any


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def _find_last_page_file(directory: Path) -> Path | None:
    """在目录中找到编号最大的 页面_XX.json 文件"""
    pattern = re.compile(r'^页面_(\d+)\.json$')
    best = None
    best_idx = -1
    for f in directory.iterdir():
        m = pattern.match(f.name)
        if m:
            idx = int(m.group(1))
            if idx > best_idx:
                best_idx = idx
                best = f
    return best


def main(input_1=None, input_2=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 加载页面分析
    
    使用 body.file_system.read() 进行文件操作（当可用时）。
    
    Args:
        input_1: {输出目录}
        input_2: {页面分析路径} - 相对路径
        body: Agent body
    
    Returns:
        dict: 页面分析数据
    """
    try:
        output_dir = flatten_input(input_1)
        relative_path = flatten_input(input_2)
        
        if not isinstance(output_dir, str):
            output_dir = str(output_dir) if output_dir else ""
        if not isinstance(relative_path, str):
            relative_path = str(relative_path) if relative_path else ""
        
        # 组合相对路径
        combined_path = str(Path(output_dir) / relative_path)
        
        # 使用 body.file_system.read() 加载（file_system 内部处理路径解析）
        if body and hasattr(body, 'file_system'):
            read_result = body.file_system.read(combined_path)
            
            if read_result.get('status') == 'success':
                content = read_result.get('content', '')
                if isinstance(content, (dict, list)):
                    return content
                if isinstance(content, str):
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {"content": content, "type": "text"}
                return content
            else:
                # 文件不存在 → 尝试回退到最后一个可用的页面分析文件
                resolved = None
                if hasattr(body.file_system, 'resolve_path'):
                    try:
                        resolved = Path(body.file_system.resolve_path(combined_path))
                    except Exception:
                        pass
                if resolved:
                    fallback = _find_last_page_file(resolved.parent)
                    if fallback and fallback.exists():
                        fb_relative = str(Path(relative_path).parent / fallback.name)
                        fb_result = body.file_system.read(str(Path(output_dir) / fb_relative))
                        if fb_result.get('status') == 'success':
                            content = fb_result.get('content', '')
                            if isinstance(content, (dict, list)):
                                return content
                            if isinstance(content, str):
                                try:
                                    return json.loads(content)
                                except json.JSONDecodeError:
                                    pass

                return {
                    "status": "error",
                    "error": read_result.get('message', '读取失败'),
                    "path": combined_path,
                    "index": 0,
                    "page_intent": "unknown",
                    "substitutable_elements": [],
                    "fixed_elements": []
                }
        else:
            # Fallback: 直接文件操作
            full_path = Path(combined_path)
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 回退到最后一个可用的页面分析文件
                fallback = _find_last_page_file(full_path.parent)
                if fallback and fallback.exists():
                    with open(fallback, 'r', encoding='utf-8') as f:
                        return json.load(f)

                return {
                    "status": "error",
                    "error": f"文件不存在: {full_path}",
                    "index": 0,
                    "page_intent": "unknown",
                    "substitutable_elements": [],
                    "fixed_elements": []
                }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"加载失败: {str(e)}",
            "index": 0,
            "page_intent": "unknown",
            "substitutable_elements": [],
            "fixed_elements": []
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        result = main(sys.argv[1], sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python 加载页面分析.py <输出目录> <相对路径>")

