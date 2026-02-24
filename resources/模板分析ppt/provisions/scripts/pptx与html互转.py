#!/usr/bin/env python3
"""
PPTX 与 HTML 互转脚本

将 PPTX 转换为 HTML 中间格式，支持：
- 提取幻灯片内容（文本、图片、布局）
- 以 HTML 形式存储和操作幻灯片
- 从 HTML 重新生成 PPTX

这种方法可以绕过复杂的 PPTX 合并问题，
因为 HTML 操作（复制、重排、删除）比直接操作 PPTX 更简单可靠。

模块结构：
- pptx_extract.py  → PPTX 提取（形状、图片、表格、图表、组合形状等）
- pptx_html_gen.py → HTML 生成（预览用）
- pptx_rebuild.py  → PPTX 重建（从 JSON 数据恢复，支持 raw_xml 保障）

输入：{pptx路径}, {操作类型}
输出：{status, output_path, slides_count}
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# ---------- 模块加载 ----------
# 支持两种场景：
#   1) 直接运行/导入（__file__ 可用）
#   2) 动态执行（需要 sys.path 或 importlib）

def _setup_module_path():
    """确保同目录下的模块可导入"""
    try:
        module_dir = str(Path(__file__).parent)
    except NameError:
        module_dir = None

    if module_dir and module_dir not in sys.path:
        sys.path.insert(0, module_dir)

_setup_module_path()

from pptx_extract import (
    ensure_dependencies,
    extract_shape_info,
    extract_slide_to_dict,
    extract_presentation,
)
from pptx_html_gen import generate_html, escape_html
from pptx_rebuild import (
    add_shape_to_slide,
    rebuild_pptx,
    rebuild_from_json,
    manipulate_and_rebuild,
    build_from_template,
)


# ============================================================
# PPTX → HTML 转换
# ============================================================

def pptx_to_html(pptx_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    将 PPTX 转换为 HTML 格式

    Args:
        pptx_path: PPTX 文件路径
        output_dir: 输出目录（可选）

    Returns:
        dict: {status, html_path, json_path, slides_count}
    """
    pptx_path = Path(pptx_path)

    # 步骤1: 提取数据
    pptx_data = extract_presentation(str(pptx_path))
    if isinstance(pptx_data, dict) and pptx_data.get("status") == "error":
        return pptx_data

    # 步骤2: 生成 HTML
    try:
        html_content = generate_html(pptx_data)
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"生成 HTML 失败: {str(e)}\n{traceback.format_exc()}"
        }

    # 步骤3: 确定输出路径并保存
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = pptx_path.parent / "html_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = pptx_path.stem
    html_path = output_dir / f"{base_name}.html"
    json_path = output_dir / f"{base_name}.json"

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(pptx_data, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "html_path": str(html_path),
        "json_path": str(json_path),
        "slides_count": len(pptx_data.get("slides", [])),
        "source": str(pptx_path)
    }


# ============================================================
# HTML/JSON → PPTX 转换 (向后兼容)
# ============================================================

def html_to_pptx(
    json_path: str,
    output_path: str = None,
    slide_order: List[int] = None,
    template_path: str = None
) -> Dict[str, Any]:
    """
    从 JSON 数据重建 PPTX（向后兼容接口）

    Args:
        json_path: JSON 数据文件路径
        output_path: 输出 PPTX 路径
        slide_order: 幻灯片顺序列表
        template_path: 可选的模板路径
    """
    return rebuild_from_json(json_path, output_path, slide_order, template_path)


# ============================================================
# 幻灯片操作
# ============================================================

def manipulate_slides(
    json_path: str,
    operations: List[Dict],
    output_path: str = None
) -> Dict[str, Any]:
    """
    对幻灯片执行操作（复制、删除、重排）（向后兼容接口）
    """
    return manipulate_and_rebuild(json_path, operations, output_path)


# ============================================================
# 便捷函数
# ============================================================

def convert_and_manipulate(
    pptx_path: str,
    operations: List[Dict] = None,
    output_path: str = None
) -> Dict[str, Any]:
    """
    一步完成：PPTX → HTML/JSON → 操作 → 新 PPTX

    Args:
        pptx_path: 输入 PPTX 路径
        operations: 操作列表（可选）
        output_path: 输出 PPTX 路径
    """
    # 步骤1：转换为 HTML/JSON
    convert_result = pptx_to_html(pptx_path)
    if convert_result["status"] != "success":
        return convert_result

    result = {
        "status": "success",
        "html_path": convert_result["html_path"],
        "json_path": convert_result["json_path"],
        "original_slides": convert_result["slides_count"]
    }

    # 步骤2：操作并重建
    if operations:
        rebuild_result = manipulate_and_rebuild(
            convert_result["json_path"],
            operations,
            output_path
        )
    else:
        rebuild_result = rebuild_from_json(
            convert_result["json_path"],
            output_path
        )

    if rebuild_result["status"] == "success":
        result["output_pptx"] = rebuild_result["output_path"]
        result["final_slides"] = rebuild_result["slides_count"]
        result["shapes_added"] = rebuild_result.get("shapes_added", 0)
        result["shapes_skipped"] = rebuild_result.get("shapes_skipped", 0)
    else:
        result["rebuild_error"] = rebuild_result.get("error")
        result["status"] = "partial"

    return result


# ============================================================
# 主函数
# ============================================================

def main(
    input_1=None,
    input_2=None,
    input_3=None,
    body=None,
    **kwargs
) -> dict:
    """
    主函数

    Args:
        input_1: PPTX 文件路径
        input_2: 操作类型或操作列表
            - "to_html": 仅转换为 HTML
            - "round_trip": 转换并重建（测试往返）
            - [{"action": "duplicate", "index": 0}, ...]: 操作列表
        input_3: 输出路径（可选）
    """
    try:
        # 解析输入
        pptx_path = input_1
        if isinstance(pptx_path, list):
            pptx_path = pptx_path[0] if pptx_path else ""

        operation = input_2
        if isinstance(operation, list) and len(operation) == 1 and isinstance(operation[0], str):
            operation = operation[0]

        output_path = input_3
        if isinstance(output_path, list):
            output_path = output_path[0] if output_path else None

        # 通过 file_system.resolve_path 解析相对路径
        if pptx_path and body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
            pptx_path = body.file_system.resolve_path(pptx_path)

        # 执行操作
        if operation == "to_html":
            return pptx_to_html(pptx_path)
        elif operation == "round_trip":
            return convert_and_manipulate(pptx_path, None, output_path)
        elif isinstance(operation, list):
            return convert_and_manipulate(pptx_path, operation, output_path)
        else:
            return pptx_to_html(pptx_path)

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"处理失败: {str(e)}\n{traceback.format_exc()}"
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pptx_file = sys.argv[1]
        operation = sys.argv[2] if len(sys.argv) > 2 else "to_html"
        output = sys.argv[3] if len(sys.argv) > 3 else None

        result = main(pptx_file, operation, output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("""
PPTX ↔ HTML 互转工具

用法:
    python pptx与html互转.py <pptx文件> [操作] [输出路径]

操作:
    to_html     - 将 PPTX 转换为 HTML（默认）
    round_trip  - 转换为 HTML 后重建 PPTX（测试往返）

示例:
    python pptx与html互转.py template.pptx to_html
    python pptx与html互转.py template.pptx round_trip output.pptx

编程接口:
    from pptx与html互转 import convert_and_manipulate

    # 复制第1张、删除第3张、重排
    result = convert_and_manipulate(
        "input.pptx",
        [
            {"action": "duplicate", "index": 0},
            {"action": "delete", "index": 2},
            {"action": "reorder", "order": [2, 0, 1, 0, 1]}
        ],
        "output.pptx"
    )
""")
