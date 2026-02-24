#!/usr/bin/env python3
"""
保存JSON脚本

通用的 JSON 保存脚本，用于保存工作流中的各种中间产物。
使用 body.file_system 进行文件操作（当可用时）。

支持的保存场景：
- 模板原始数据 → {输出目录}/模板原始数据.json
- 页面分析 → {输出目录}/页面分析/{index}.json
- 简化概览 → {输出目录}/简化概览.json
- 模板计划 → {输出目录}/中间产物/模板计划.json
- 对齐大纲 → {输出目录}/中间产物/对齐大纲.json

输入：{数据}, {保存路径} 或 {输出目录} + {文件名}
输出：{"status": "success", "path": "..."}
"""

import json
from pathlib import Path
from typing import Dict, Any, Union


def save_with_body(data: Any, relative_path: str, body) -> Dict:
    """
    使用 body.file_system 保存数据
    
    Args:
        data: 要保存的数据（dict, list, 或其他可序列化对象）
        relative_path: 相对保存路径
        body: Agent body with file_system
    
    Returns:
        保存结果 dict
    """
    try:
        # 确保数据可序列化
        if isinstance(data, (dict, list)):
            content = data
        else:
            content = {"value": data}
        
        # 使用 file_system 保存
        save_result = body.file_system.save(
            content=content,
            location=relative_path
        )
        
        if save_result.get('status') == 'success':
            return {
                "status": "success",
                "path": save_result.get('location', relative_path),
                "message": f"已保存到 {relative_path}"
            }
        else:
            return {
                "status": "error",
                "error": save_result.get('message', '保存失败'),
                "path": relative_path
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"保存失败: {str(e)}",
            "path": relative_path
        }


def save_direct(data: Any, full_path: str) -> Dict:
    """
    直接保存到文件系统（fallback 方法）
    
    Args:
        data: 要保存的数据
        full_path: 完整文件路径
    
    Returns:
        保存结果 dict
    """
    try:
        path = Path(full_path)
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 确保数据可序列化
        if isinstance(data, (dict, list)):
            content = data
        else:
            content = {"value": data}
        
        # 保存 JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False, default=str)
        
        return {
            "status": "success",
            "path": str(path),
            "message": f"已保存到 {path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"保存失败: {str(e)}",
            "path": full_path
        }


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) == 1:
            data = data[0]
    return data


def main(input_1=None, input_2=None, input_3=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 保存 JSON 数据
    
    支持三种调用方式：
    
    方式1：指定完整相对路径（.json 结尾）
        input_1: {数据} - 要保存的数据
        input_2: {保存路径} - 相对路径，如 "中间产物/模板计划.json"
    
    方式2：指定输出目录 + 相对路径（推荐，支持动态构造）
        input_1: {数据} - 要保存的数据
        input_2: {输出目录} - 基础输出目录，如 "productions/"
        input_3: {相对路径} - 目录下的相对路径，如 "页面分析/0.json"
        最终路径：{输出目录}/{相对路径}
    
    方式3：指定输出目录 + 自动从数据推断文件名
        input_1: {数据} - 要保存的数据（需包含 index 字段）
        input_2: {输出目录} - 输出目录路径
        最终路径：{输出目录}/{data.index}.json
    
    Args:
        input_1: 要保存的数据
        input_2: 保存路径或输出目录
        input_3: 相对路径（可选）
        body: Agent body with file_system
    
    Returns:
        dict: {"status": "success/error", "path": "...", ...}
    """
    try:
        # 解析输入
        data = flatten_input(input_1)
        path_or_dir = flatten_input(input_2)
        relative_sub_path = flatten_input(input_3)
        
        # 确定保存路径
        if isinstance(path_or_dir, str):
            if path_or_dir.endswith('.json'):
                # 方式1：完整相对路径
                relative_path = path_or_dir
            elif isinstance(relative_sub_path, str):
                # 方式2：输出目录 + 相对路径
                output_dir = path_or_dir.rstrip('/').rstrip('\\')
                sub_path = relative_sub_path.lstrip('/').lstrip('\\')
                relative_path = f"{output_dir}/{sub_path}"
            elif isinstance(relative_sub_path, int):
                # 索引模式（如页面分析，input_3 是整数索引）
                output_dir = path_or_dir.rstrip('/').rstrip('\\')
                relative_path = f"{output_dir}/{relative_sub_path}.json"
            elif isinstance(data, dict) and 'index' in data:
                # 方式3：从数据中获取索引
                output_dir = path_or_dir.rstrip('/').rstrip('\\')
                relative_path = f"{output_dir}/{data['index']}.json"
            else:
                # 默认：输出目录 + output.json
                output_dir = path_or_dir.rstrip('/').rstrip('\\')
                relative_path = f"{output_dir}/output.json"
        else:
            return {
                "status": "error",
                "error": "无效的保存路径",
                "input_2": str(path_or_dir)
            }
        
        # 规范化路径（处理可能的 // 等）
        relative_path = str(Path(relative_path))
        
        # 保存数据
        if body and hasattr(body, 'file_system'):
            return save_with_body(data, relative_path, body)
        else:
            # Fallback: 直接文件操作
            # 需要从某处获取基础路径，这里假设相对于当前工作目录
            return save_direct(data, relative_path)
            
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"保存失败: {str(e)}",
            "traceback": traceback.format_exc()
        }


# 便捷函数：为特定场景提供简化接口

def save_template_raw_data(data: Dict, output_dir: str, body=None) -> Dict:
    """保存模板原始数据"""
    return main(data, f"{output_dir}/模板原始数据.json", body=body)


def save_page_analysis(data: Dict, output_dir: str, index: int, body=None) -> Dict:
    """保存单页分析"""
    return main(data, f"{output_dir}/页面分析/{index}.json", body=body)


def save_simplified_overview(data: Any, output_dir: str, body=None) -> Dict:
    """保存简化概览"""
    return main(data, f"{output_dir}/简化概览.json", body=body)


def save_template_plan(data: Dict, output_dir: str, body=None) -> Dict:
    """保存模板计划"""
    return main(data, f"{output_dir}/中间产物/模板计划.json", body=body)


def save_aligned_outline(data: Dict, output_dir: str, body=None) -> Dict:
    """保存对齐大纲"""
    return main(data, f"{output_dir}/中间产物/对齐大纲.json", body=body)


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_data = {
        "index": 0,
        "page_type": "title",
        "purpose": "标题页",
        "text_slots_count": 2
    }
    
    if len(sys.argv) >= 2:
        output_path = sys.argv[1]
        result = main(input_1=test_data, input_2=output_path)
    else:
        result = main(input_1=test_data, input_2="test_output.json")
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

