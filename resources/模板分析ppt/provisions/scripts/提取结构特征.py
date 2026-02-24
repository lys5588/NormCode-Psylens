#!/usr/bin/env python3
"""
提取结构特征脚本

从已提取的页面数据中识别客观结构特征（不做意图判断）。
这是一个简单的规则脚本，输出供后续 LLM 理解意图时使用。

输入：{当前页面} - 单页的 shapes 数据
输出：{结构特征} - 客观结构信息
"""

import json
import re
from typing import Dict, List, Any, Optional


def is_numbering_text(text: str) -> bool:
    """判断文本是否为编号格式"""
    text = text.strip()
    # 匹配常见编号格式: 01, 02, 03, 1, 2, 3, 一, 二, 三, A, B, C, etc.
    patterns = [
        r'^0?[1-9]$',           # 01, 02, 1, 2
        r'^[一二三四五六七八九十]+$',  # 中文数字
        r'^[A-Za-z]$',           # 单字母
        r'^[①②③④⑤⑥⑦⑧⑨⑩]$',  # 圆圈数字
        r'^STEP\s*\d+$',         # STEP 1, STEP 2
        r'^Part\s*\d+$',         # Part 1, Part 2
    ]
    for pattern in patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def extract_structure_features(page_data: Dict, body=None) -> Dict:
    """
    从页面数据中提取结构特征
    
    Args:
        page_data: 单页的原始数据（包含 shapes 列表）
        body: Agent body (可选)
    
    Returns:
        结构特征字典
    """
    shapes = page_data.get("shapes", [])
    
    # 统计各类元素
    text_shapes = []
    image_shapes = []
    table_shapes = []
    other_shapes = []
    
    numbering_texts = []
    large_background = False
    
    for shape in shapes:
        element_type = shape.get("element_type", "other")
        
        if element_type == "text":
            text_content = shape.get("text_content", "").strip()
            text_shapes.append({
                "shape_index": shape.get("shape_index"),
                "text": text_content,
                "font_size": None,  # 尝试获取字体大小
                "position": shape.get("position", {})
            })
            
            # 提取字体大小
            text_frame = shape.get("text_frame", {})
            if text_frame:
                paragraphs = text_frame.get("paragraphs", [])
                for para in paragraphs:
                    font = para.get("font", {})
                    if "size_pt" in font:
                        text_shapes[-1]["font_size"] = font["size_pt"]
                        break
            
            # 检查是否为编号
            if is_numbering_text(text_content):
                numbering_texts.append(text_content)
        
        elif element_type == "picture":
            coverage = shape.get("coverage_ratio", 0)
            image_shapes.append({
                "shape_index": shape.get("shape_index"),
                "coverage_ratio": coverage
            })
            # 判断是否为大背景图
            if coverage and coverage >= 0.7:
                large_background = True
        
        elif element_type == "table":
            table_shapes.append({
                "shape_index": shape.get("shape_index"),
                "rows": shape.get("table_info", {}).get("rows", 0),
                "columns": shape.get("table_info", {}).get("columns", 0)
            })
        
        else:
            other_shapes.append({
                "shape_index": shape.get("shape_index"),
                "type": element_type
            })
    
    # 构建结构特征
    result = {
        "page_index": page_data.get("index", 0),
        "layout_name": page_data.get("layout_name", "Unknown"),
        
        # 数量统计
        "text_count": len(text_shapes),
        "image_count": len(image_shapes),
        "table_count": len(table_shapes),
        "total_shapes": len(shapes),
        
        # 编号检测
        "has_numbering": len(numbering_texts) > 0,
        "numbering_texts": numbering_texts,
        
        # 背景检测
        "has_large_background": large_background,
        
        # 文本形状详情（供 LLM 分析）
        "text_shapes": text_shapes,
        
        # 图片形状简要
        "image_shapes": image_shapes,
        
        # 表格存在
        "has_table": len(table_shapes) > 0,
        "table_info": table_shapes[0] if table_shapes else None
    }
    
    # 尝试猜测布局模式（简单规则，不做意图判断）
    if result["text_count"] == 0:
        result["layout_hint"] = "pure_visual"
    elif result["text_count"] <= 2 and not result["has_numbering"]:
        result["layout_hint"] = "title_style"
    elif len(numbering_texts) >= 3:
        result["layout_hint"] = "multi_block_numbered"
    elif result["text_count"] >= 4:
        result["layout_hint"] = "multi_text"
    else:
        result["layout_hint"] = "standard"
    
    return result


def flatten_input(data):
    """展平嵌套的输入"""
    if isinstance(data, list):
        while isinstance(data, list) and len(data) > 0:
            data = data[0]
    return data


def main(input_1=None, body=None, **kwargs) -> Dict:
    """
    主函数 - 提取结构特征
    
    Args:
        input_1: {当前页面} - 单页数据
        body: Agent body
    
    Returns:
        dict: 结构特征
    """
    try:
        page_data = flatten_input(input_1)
        
        if not isinstance(page_data, dict):
            return {
                "status": "error",
                "error": f"输入必须是字典类型，收到: {type(page_data)}"
            }
        
        return extract_structure_features(page_data, body)
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"提取结构特征失败: {str(e)}",
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    import sys
    
    # 测试用例
    test_page = {
        "index": 5,
        "layout_name": "Content Slide",
        "shapes": [
            {"shape_index": 0, "element_type": "picture", "coverage_ratio": 1.0},
            {"shape_index": 1, "element_type": "text", "text_content": "01"},
            {"shape_index": 2, "element_type": "text", "text_content": "02"},
            {"shape_index": 3, "element_type": "text", "text_content": "03"},
            {"shape_index": 4, "element_type": "text", "text_content": "CASE TITLE", 
             "text_frame": {"paragraphs": [{"text": "CASE TITLE", "font": {"size_pt": 24}}]}},
            {"shape_index": 5, "element_type": "text", "text_content": "First point description"},
            {"shape_index": 6, "element_type": "text", "text_content": "Second point description"},
            {"shape_index": 7, "element_type": "text", "text_content": "Third point description"},
        ]
    }
    
    result = main(input_1=test_page)
    print(json.dumps(result, ensure_ascii=False, indent=2))

