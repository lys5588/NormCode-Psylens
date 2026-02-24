#!/usr/bin/env python3
"""
加载JSON脚本

通用的 JSON 加载脚本，用于加载工作流中保存的中间产物。
使用 body.file_system 进行文件操作（当可用时）。

支持的加载场景：
- 模板原始数据 ← {输出目录}/模板原始数据.json
- 页面分析 ← {输出目录}/页面分析/{index}.json
- 简化概览 ← {输出目录}/简化概览.json
- 模板计划 ← {输出目录}/中间产物/模板计划.json
- 对齐大纲 ← {输出目录}/中间产物/对齐大纲.json

输入：{加载路径} 或 {输出目录} + {文件名}
输出：加载的 JSON 数据，或 {"status": "error", ...}
"""

import json
from pathlib import Path
from typing import Dict, Any, Union, Optional


def load_with_body(relative_path: str, body) -> Union[Dict, Any]:
    """
    使用 body.file_system 加载数据
    
    Args:
        relative_path: 相对加载路径
        body: Agent body with file_system
    
    Returns:
        加载的数据或错误信息
    """
    try:
        # 使用 file_system 读取
        read_result = body.file_system.read(relative_path)
        
        if read_result.get('status') == 'success':
            content = read_result.get('content', '')
            
            # 如果内容已经是 dict/list，直接返回
            if isinstance(content, (dict, list)):
                return content
            
            # 如果是字符串，尝试解析 JSON
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 不是 JSON，返回原始字符串
                    return {"content": content, "type": "text"}
            
            return content
        else:
            return {
                "status": "error",
                "error": read_result.get('message', '读取失败'),
                "path": relative_path
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"加载失败: {str(e)}",
            "path": relative_path
        }


def load_direct(full_path: str) -> Union[Dict, Any]:
    """
    直接从文件系统加载（fallback 方法）
    
    Args:
        full_path: 完整文件路径
    
    Returns:
        加载的数据或错误信息
    """
    try:
        path = Path(full_path)
        
        if not path.exists():
            return {
                "status": "error",
                "error": f"文件不存在: {path}",
                "path": str(path)
            }
        
        # 读取并解析 JSON
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 不是 JSON，返回原始字符串
            return {"content": content, "type": "text"}
            
    except Exception as e:
        return {
            "status": "error",
            "error": f"加载失败: {str(e)}",
            "path": full_path
        }


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) == 1:
            data = data[0]
    return data


def main(input_1=None, input_2=None, body=None, **kwargs) -> Union[Dict, Any]:
    """
    主函数 - 加载 JSON 数据
    
    支持两种调用方式：
    
    方式1：指定完整相对路径
        input_1: {加载路径} - 相对路径，如 "中间产物/模板计划.json"
    
    方式2：指定输出目录和文件名
        input_1: {输出目录} - 输出目录路径
        input_2: {文件名} - 文件名（如 "模板计划.json"）或索引（如 0）
    
    Args:
        input_1: 加载路径或输出目录
        input_2: 文件名或索引（可选）
        body: Agent body with file_system
    
    Returns:
        加载的数据，或 {"status": "error", ...}
    """
    try:
        # 解析输入
        path_or_dir = flatten_input(input_1)
        filename_or_index = flatten_input(input_2)
        
        # 确定加载路径
        if isinstance(path_or_dir, str):
            if path_or_dir.endswith('.json'):
                # 方式1：完整相对路径
                relative_path = path_or_dir
            elif filename_or_index is not None:
                # 方式2：输出目录 + 文件名/索引
                output_dir = path_or_dir
                
                if isinstance(filename_or_index, str):
                    if filename_or_index.endswith('.json'):
                        filename = filename_or_index
                    else:
                        filename = f"{filename_or_index}.json"
                elif isinstance(filename_or_index, int):
                    filename = f"{filename_or_index}.json"
                else:
                    filename = str(filename_or_index)
                
                relative_path = f"{output_dir}/{filename}"
            else:
                return {
                    "status": "error",
                    "error": "需要指定文件名或完整路径",
                    "input_1": str(path_or_dir)
                }
        else:
            return {
                "status": "error",
                "error": "无效的加载路径",
                "input_1": str(path_or_dir)
            }
        
        # 规范化路径
        relative_path = str(Path(relative_path))
        
        # 加载数据
        if body and hasattr(body, 'file_system'):
            return load_with_body(relative_path, body)
        else:
            # Fallback: 直接文件操作
            return load_direct(relative_path)
            
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"加载失败: {str(e)}",
            "traceback": traceback.format_exc()
        }


# 便捷函数：为特定场景提供简化接口

def load_template_raw_data(output_dir: str, body=None) -> Union[Dict, Any]:
    """加载模板原始数据"""
    return main(f"{output_dir}/模板原始数据.json", body=body)


def load_page_analysis(output_dir: str, index: int, body=None) -> Union[Dict, Any]:
    """加载单页分析"""
    return main(f"{output_dir}/页面分析/{index}.json", body=body)


def load_simplified_overview(output_dir: str, body=None) -> Union[Dict, Any]:
    """加载简化概览"""
    return main(f"{output_dir}/简化概览.json", body=body)


def load_template_plan(output_dir: str, body=None) -> Union[Dict, Any]:
    """加载模板计划"""
    return main(f"{output_dir}/中间产物/模板计划.json", body=body)


def load_aligned_outline(output_dir: str, body=None) -> Union[Dict, Any]:
    """加载对齐大纲"""
    return main(f"{output_dir}/中间产物/对齐大纲.json", body=body)


def load_all_page_analyses(output_dir: str, total_pages: int, body=None) -> list:
    """
    加载所有页面分析
    
    Args:
        output_dir: 输出目录
        total_pages: 总页数
        body: Agent body
    
    Returns:
        所有页面分析的列表
    """
    analyses = []
    for i in range(total_pages):
        analysis = load_page_analysis(output_dir, i, body)
        if isinstance(analysis, dict) and analysis.get('status') == 'error':
            # 记录错误但继续
            analyses.append({"index": i, "error": analysis.get('error')})
        else:
            analyses.append(analysis)
    return analyses


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 2:
        load_path = sys.argv[1]
        result = main(input_1=load_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(json.dumps({
            "error": "用法: python 加载JSON.py <path.json>"
        }, ensure_ascii=False))

