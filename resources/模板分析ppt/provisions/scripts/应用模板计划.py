#!/usr/bin/env python3
"""
应用模板计划脚本

根据幻灯片索引计划从模板生成新的演示文稿。

例如：计划 [0, 5, 2, 2, 10] 表示：
- 第1张：使用模板的第0张幻灯片
- 第2张：使用模板的第5张幻灯片
- 第3张：使用模板的第2张幻灯片
- 第4张：使用模板的第2张幻灯片（重复）
- 第5张：使用模板的第10张幻灯片

支持：
- 幻灯片重复使用
- 幻灯片重新排序
- 跳过某些幻灯片
- 保留图片和文本内容

输入：{模板路径}, {计划列表}, {输出路径}
输出：{status, output_path, slides_count, plan_applied}
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import importlib.util


def _setup_module_path(body=None):
    """确保同目录下的模块可导入"""
    module_dir = None
    try:
        module_dir = str(Path(__file__).parent)
    except NameError:
        pass

    # 如果 __file__ 不可用（exec 模式），通过 body 定位脚本目录
    if module_dir is None and body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
        try:
            # 用一个已知存在的同目录模块来确定目录
            resolved = Path(body.file_system.resolve_path("provisions/scripts/pptx_rebuild.py"))
            if resolved.exists():
                module_dir = str(resolved.parent)
        except Exception:
            pass

    if module_dir and module_dir not in sys.path:
        sys.path.insert(0, module_dir)

_setup_module_path()


def _import_pptx_rebuild(body=None):
    """导入 pptx_rebuild 模块，支持多种回退方式"""
    # 1. 直接导入（sys.path 已配置时可用）
    try:
        import pptx_rebuild
        return pptx_rebuild
    except ImportError:
        pass

    # 2. 通过 body.file_system.resolve_path 定位并加载
    if body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
        try:
            resolved = Path(body.file_system.resolve_path("provisions/scripts/pptx_rebuild.py"))
            if resolved.exists():
                # 确保目录在 sys.path 中
                module_dir = str(resolved.parent)
                if module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
                # 通过 importlib 加载
                spec = importlib.util.spec_from_file_location("pptx_rebuild", str(resolved))
                pptx_rebuild = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pptx_rebuild)
                return pptx_rebuild
        except Exception:
            pass

    # 3. 尝试在常见相对路径查找
    for candidate in [
        Path("provisions/scripts/pptx_rebuild.py"),
        Path("pptx_rebuild.py"),
    ]:
        if candidate.exists():
            module_dir = str(candidate.parent.resolve())
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)
            spec = importlib.util.spec_from_file_location("pptx_rebuild", str(candidate.resolve()))
            pptx_rebuild = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pptx_rebuild)
            return pptx_rebuild

    raise ImportError("无法找到 pptx_rebuild 模块")


def load_html_module(body=None):
    """加载 HTML 转换模块（向后兼容）
    
    现在优先使用拆分后的模块，回退到整体模块。
    
    Args:
        body: Agent body（可选），用于通过 file_system.resolve_path 定位模块
    """
    # 优先尝试直接导入拆分后的模块
    try:
        import pptx_extract
        import pptx_rebuild
        # 构造一个兼容对象，暴露旧接口
        class _compat:
            ensure_dependencies = staticmethod(pptx_extract.ensure_dependencies)
            extract_slide_to_dict = staticmethod(pptx_extract.extract_slide_to_dict)
            add_shape_to_slide = staticmethod(pptx_rebuild.add_shape_to_slide)
        return _compat()
    except ImportError:
        pass

    # 回退：加载整体模块
    html_module_path = None
    
    try:
        current_dir = Path(__file__).parent
        candidate = current_dir / "pptx与html互转.py"
        if candidate.exists():
            html_module_path = candidate
    except NameError:
        pass

    if html_module_path is None and body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
        candidate = Path(body.file_system.resolve_path("provisions/scripts/pptx与html互转.py"))
        if candidate.exists():
            html_module_path = candidate
    
    if html_module_path is None or not html_module_path.exists():
        raise FileNotFoundError(f"HTML 转换模块不存在，尝试了多种路径")
    
    spec = importlib.util.spec_from_file_location("pptx_html", html_module_path)
    pptx_html = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pptx_html)
    return pptx_html


def apply_template_plan(
    template_path: str,
    plan: List[int],
    output_path: str = None,
    body=None
) -> Dict[str, Any]:
    """
    根据计划从模板生成新演示文稿
    
    Args:
        template_path: 模板 PPTX 路径
        plan: 幻灯片索引列表，如 [0, 5, 2, 2, 10]
        output_path: 输出路径（可选，默认在模板目录生成）
        body: Agent body（可选）
    
    Returns:
        dict: {status, output_path, slides_count, plan_applied}
    """
    result = {
        "status": "pending",
        "output_path": "",
        "slides_count": 0,
        "plan_applied": plan
    }
    
    # 验证输入
    if not template_path:
        result["status"] = "error"
        result["error"] = "未提供模板路径"
        return result
    
    if not plan or not isinstance(plan, list):
        result["status"] = "error"
        result["error"] = "计划必须是非空的索引列表"
        return result
    
    # 通过 file_system.resolve_path 解析路径
    if body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
        template_path = Path(body.file_system.resolve_path(str(template_path)))
    else:
        template_path = Path(template_path).resolve()
    
    if not template_path.exists():
        result["status"] = "error"
        result["error"] = f"模板文件不存在: {template_path}"
        return result
    
    # 确定输出路径（通过 file_system.resolve_path 解析）
    if output_path:
        if body and hasattr(body, 'file_system') and hasattr(body.file_system, 'resolve_path'):
            output_path = Path(body.file_system.resolve_path(str(output_path)))
        else:
            output_path = Path(output_path)
    else:
        output_path = template_path.parent / f"{template_path.stem}_plan_applied.pptx"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 确保模块路径已配置（exec 模式下需要 body）
        _setup_module_path(body)

        # 使用幻灯片级克隆（最可靠的方式）
        # 直接在 XML 和关系层面复制幻灯片，完美保留所有格式
        pptx_rebuild = _import_pptx_rebuild(body)

        # 预处理：索引越界时回退到最后一张幻灯片
        from pptx import Presentation as _Prs
        _tmp_prs = _Prs(str(template_path))
        _total = len(_tmp_prs.slides)
        if _total > 0:
            _last = _total - 1
            plan = [min(max(i, 0), _last) for i in plan]
        del _tmp_prs
        result["plan_applied"] = plan

        rebuild_result = pptx_rebuild.build_from_template(
            str(template_path), plan, str(output_path)
        )

        if rebuild_result["status"] != "success":
            result["status"] = "error"
            result["error"] = rebuild_result.get("error", "构建失败")
            return result

        result["status"] = "success"
        result["output_path"] = rebuild_result["output_path"]
        result["slides_count"] = rebuild_result["slides_count"]
        result["plan_applied"] = plan
        result["template_slides"] = rebuild_result.get("template_slides", 0)

        return result

    except Exception as e:
        import traceback
        result["status"] = "error"
        result["error"] = f"应用模板计划失败: {e}\n{traceback.format_exc()}"
        return result


def main(
    input_1=None,  # 模板路径
    input_2=None,  # 计划列表
    input_3=None,  # 输出路径（可选）
    body=None,
    **kwargs
) -> dict:
    """
    主函数
    
    Args:
        input_1: 模板 PPTX 路径
        input_2: 计划列表，如 [0, 5, 2, 2, 10]
        input_3: 输出路径（可选）
        body: Agent body
    
    Returns:
        dict: 处理结果
    """
    try:
        # 解析模板路径
        template_path = input_1
        if isinstance(template_path, list):
            template_path = template_path[0] if template_path else ""
        
        # 解析计划
        plan = input_2
        if isinstance(plan, str):
            plan = json.loads(plan)
        
        # 如果是 dict，提取 plan 键（兼容 {模板计划} 格式）
        if isinstance(plan, dict):
            plan = plan.get("plan", plan.get("result", {}).get("plan", []))
        
        # 处理嵌套列表
        if isinstance(plan, list) and len(plan) == 1 and isinstance(plan[0], list):
            plan = plan[0]
        
        # 确保计划是整数列表
        plan = [int(i) for i in plan]
        
        # 解析输出路径
        output_path = input_3
        if isinstance(output_path, list):
            output_path = output_path[0] if output_path else None
        
        return apply_template_plan(template_path, plan, output_path, body)
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"处理失败: {e}\n{traceback.format_exc()}"
        }


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    if len(sys.argv) >= 3:
        template = sys.argv[1]
        plan = json.loads(sys.argv[2])
        output = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = main(template, plan, output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("""
应用模板计划工具

用法:
    python 应用模板计划.py <模板文件> <计划JSON> [输出路径]

参数:
    模板文件: PPTX 模板路径
    计划JSON: 幻灯片索引列表，如 "[0, 5, 2, 2, 10]"
    输出路径: 可选，默认在模板目录生成 xxx_plan_applied.pptx

示例:
    python 应用模板计划.py template.pptx "[0, 5, 2, 2, 10]"
    python 应用模板计划.py template.pptx "[0, 0, 1, 2, 2, 3]" output.pptx

计划说明:
    [0, 5, 2, 2, 10] 表示：
    - 使用模板第 1 张幻灯片（索引 0）
    - 使用模板第 6 张幻灯片（索引 5）
    - 使用模板第 3 张幻灯片（索引 2）
    - 再次使用模板第 3 张幻灯片（重复）
    - 使用模板第 11 张幻灯片（索引 10）
""")

