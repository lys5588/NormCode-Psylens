#!/usr/bin/env python3
"""
映射 slot 到 shape_index 脚本

将 LLM 生成的 slot-based 内容转换为 shape_index-based 内容。
这是一个确定性脚本，不会出错。

输入：
  - {页面文本内容}: slot-based 内容 {slide_index, replacements: [{slot, text}]}
  - {可更改元素映射}: 映射表 {mapping: {"1": 10, "2": 11, ...}}

输出：{映射页面文本内容}: shape_index-based 内容
"""

import json
from typing import Dict, Any, List


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, input_2=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 将 slot 映射回 shape_index
    
    Args:
        input_1: {页面文本内容} - slot-based 内容
        input_2: {可更改元素映射} - 映射表
        body: Agent body
    
    Returns:
        dict: shape_index-based 内容
    """
    try:
        content = flatten_input(input_1)
        mapping_data = flatten_input(input_2)
        
        # 提取映射表
        if isinstance(mapping_data, dict):
            mapping = mapping_data.get("mapping", mapping_data)
        else:
            mapping = {}
        
        if not isinstance(content, dict):
            return {
                "slide_index": 0,
                "replacements": [],
                "error": "无法解析页面内容"
            }
        
        # 提取 slide_index
        slide_index = content.get("slide_index", 0)
        
        # 提取并转换 replacements
        slot_replacements = content.get("replacements", [])
        shape_replacements = []
        mapping_log = []
        
        for item in slot_replacements:
            slot = item.get("slot")
            text = item.get("text", "")
            
            if slot is None:
                # 如果已经是 shape_index 格式，直接使用
                if "shape_index" in item:
                    shape_replacements.append({
                        "shape_index": item["shape_index"],
                        "text": text
                    })
                    mapping_log.append({
                        "input": f"shape_index {item['shape_index']}",
                        "output": f"shape_index {item['shape_index']}",
                        "note": "已是 shape_index 格式，直接使用"
                    })
                continue
            
            # 查找映射
            slot_key = str(slot)
            shape_index = mapping.get(slot_key)
            
            if shape_index is not None:
                shape_replacements.append({
                    "shape_index": shape_index,
                    "text": text
                })
                mapping_log.append({
                    "input": f"slot {slot}",
                    "output": f"shape_index {shape_index}",
                    "text_preview": text[:30] + "..." if len(text) > 30 else text
                })
            else:
                # 映射不存在，记录警告
                mapping_log.append({
                    "input": f"slot {slot}",
                    "output": "未找到映射",
                    "warning": f"slot {slot} 在映射表中不存在"
                })
        
        return {
            "slide_index": slide_index,
            "replacements": shape_replacements,
            "_mapping_log": mapping_log
        }
        
    except Exception as e:
        return {
            "slide_index": 0,
            "replacements": [],
            "error": f"映射失败: {str(e)}"
        }


if __name__ == "__main__":
    # 测试用例
    test_content = {
        "slide_index": 0,
        "replacements": [
            {"slot": 1, "text": "序言智理科技公司介绍"},
            {"slot": 2, "text": "NormCode规范化推理框架"},
            {"slot": 3, "text": "让AI推理透明可控，共建可信人工智能未来"}
        ]
    }
    
    test_mapping = {
        "mapping": {
            "1": 10,
            "2": 11,
            "3": 9
        }
    }
    
    result = main(input_1=test_content, input_2=test_mapping)
    print("映射结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 验证结果
    print("\n验证：")
    for r in result["replacements"]:
        print(f"  shape_index {r['shape_index']}: {r['text'][:20]}...")
    
    # 验证 slot 已被替换
    result_str = json.dumps(result["replacements"])
    if '"slot"' in result_str:
        print("\n❌ 错误：输出中仍包含 slot！")
    else:
        print("\n✅ 成功：所有 slot 已转换为 shape_index")

