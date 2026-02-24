#!/usr/bin/env python3
"""
HTML 生成模块

从提取的 PPTX 数据字典生成可视化 HTML 页面。
HTML 用于预览和交互式操作（复制、删除、重排幻灯片），
不用于重建——重建使用 JSON 数据。
"""

import json
from typing import Dict


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_slide_html(slide: Dict, pptx_data: Dict) -> str:
    """生成单个幻灯片的 HTML"""

    shapes_html = []
    slide_width = pptx_data.get("slide_width", 9144000)
    slide_height = pptx_data.get("slide_height", 6858000)

    for shape in slide["shapes"]:
        left = shape.get("left", 0)
        top = shape.get("top", 0)
        width = shape.get("width", 0)
        height = shape.get("height", 0)

        # 避免除以零
        if slide_width <= 0 or slide_height <= 0:
            continue

        # 计算相对位置（百分比）
        left_pct = (left / slide_width) * 100
        top_pct = (top / slide_height) * 100
        width_pct = (width / slide_width) * 100
        height_pct = (height / slide_height) * 100

        shape_style = f"left:{left_pct:.1f}%;top:{top_pct:.1f}%;width:{width_pct:.1f}%;height:{height_pct:.1f}%"

        # 图片
        if "image_ref" in shape:
            img_data = pptx_data.get("images", {}).get(shape["image_ref"], {})
            if img_data:
                shapes_html.append(f'''
                <div class="shape shape-image" style="{shape_style}">
                    <img src="data:{img_data.get("type", "image/png")};base64,{img_data.get("data", "")}" alt="{escape_html(shape.get("name", "image"))}">
                </div>''')

        # 表格
        elif "table_data" in shape:
            table = shape["table_data"]
            rows = table.get("rows", 0)
            cols = table.get("columns", 0)
            cells = table.get("cells", [])

            table_html = '<table style="width:100%;height:100%;border-collapse:collapse;font-size:0.75rem;">'
            for r in range(rows):
                table_html += '<tr>'
                for c in range(cols):
                    cell_text = ""
                    for cell in cells:
                        if cell["row"] == r and cell["col"] == c:
                            cell_text = escape_html(cell["text"])
                            break
                    table_html += f'<td style="border:1px solid #ccc;padding:4px;">{cell_text}</td>'
                table_html += '</tr>'
            table_html += '</table>'

            shapes_html.append(f'''
            <div class="shape" style="{shape_style};overflow:auto;">
                {table_html}
            </div>''')

        # 文本
        elif "text_content" in shape and shape.get("full_text", "").strip():
            text_class = "body"
            placeholder_type = shape.get("placeholder_type", "")
            if placeholder_type in ("TITLE", "CENTER_TITLE"):
                text_class = "title"
            elif placeholder_type == "SUBTITLE":
                text_class = "subtitle"
            elif shape.get("placeholder_idx") == 0:
                text_class = "title"

            text_html = ""
            paragraphs = shape.get("text_content", [])
            has_bullets = len(paragraphs) > 1 and text_class == "body"

            if has_bullets:
                text_html = "<ul>"
                for para in paragraphs:
                    if para.get("text", "").strip():
                        text_html += f"<li>{escape_html(para['text'])}</li>"
                text_html += "</ul>"
            else:
                for para in paragraphs:
                    if para.get("text", "").strip():
                        text_html += f"<p>{escape_html(para['text'])}</p>"

            shapes_html.append(f'''
            <div class="shape shape-text {text_class}" style="{shape_style}">
                {text_html}
            </div>''')

        # 图表占位符
        elif shape.get("is_chart"):
            chart_type = shape.get("chart_type", "图表")
            shapes_html.append(f'''
            <div class="shape" style="{shape_style};background:rgba(100,126,234,0.1);border:2px dashed #667eea;display:flex;align-items:center;justify-content:center;">
                <span style="color:#667eea;font-size:0.85rem;">📊 {escape_html(str(chart_type))}</span>
            </div>''')

        # 组合形状
        elif "group_shapes" in shape:
            group_text = " | ".join(
                s.get("full_text", "").strip()
                for s in shape["group_shapes"]
                if s.get("full_text", "").strip()
            )
            display = escape_html(group_text[:100]) if group_text else "组合形状"
            shapes_html.append(f'''
            <div class="shape" style="{shape_style};background:rgba(200,200,200,0.15);border:1px dashed #999;">
                <div style="padding:5px;font-size:0.8rem;color:#666;">{display}</div>
            </div>''')

        # raw_xml shapes (auto-shapes, connectors, etc.) — show as placeholder
        elif "raw_xml" in shape and shape.get("name"):
            shapes_html.append(f'''
            <div class="shape" style="{shape_style};background:rgba(200,200,200,0.1);border:1px dotted #bbb;">
            </div>''')

    # 备注
    notes_html = ""
    if slide.get("notes", "").strip():
        notes_html = f'''
        <div class="slide-notes">
            <h4>📝 演讲者备注</h4>
            <p>{escape_html(slide["notes"])}</p>
        </div>'''

    return f'''
    <div class="slide" data-index="{slide["index"]}" data-original-index="{slide["index"]}">
        <div class="slide-header">
            <span class="slide-number">幻灯片 {slide["index"] + 1}</span>
            <span class="slide-layout">{escape_html(slide.get("layout_name", ""))}</span>
            <div class="slide-actions">
                <button onclick="duplicateSlide()">复制</button>
                <button class="delete" onclick="deleteSlide(this)">删除</button>
            </div>
        </div>
        <div class="slide-content">
            {"".join(shapes_html)}
        </div>
        {notes_html}
    </div>'''


def generate_html(pptx_data: Dict) -> str:
    """
    从提取的数据生成完整的 HTML 文档。

    Args:
        pptx_data: 由 pptx_extract.extract_presentation() 返回的数据

    Returns:
        完整的 HTML 字符串
    """
    slides_html = []
    for slide in pptx_data.get("slides", []):
        slides_html.append(generate_slide_html(slide, pptx_data))

    slide_w = pptx_data.get("slide_width_inches", 10)
    slide_h = pptx_data.get("slide_height_inches", 7.5)
    source = pptx_data.get("source", "Presentation")
    n_slides = len(pptx_data.get("slides", []))

    # Embed JSON without image data to keep HTML smaller
    json_for_display = {k: v for k, v in pptx_data.items() if k != "images"}
    json_for_display["images"] = {k: {"type": v.get("type", "")} for k, v in pptx_data.get("images", {}).items()}

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(source)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .presentation-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .presentation-header {{
            text-align: center;
            color: #fff;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .presentation-header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .presentation-header .meta {{
            color: #8892b0;
            font-size: 0.9rem;
        }}
        .slide {{
            background: #fff;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
            transition: transform 0.3s ease;
        }}
        .slide:hover {{
            transform: translateY(-5px);
        }}
        .slide-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .slide-number {{
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .slide-layout {{
            font-size: 0.85rem;
            opacity: 0.9;
        }}
        .slide-content {{
            padding: 30px;
            min-height: 400px;
            position: relative;
            aspect-ratio: {slide_w}/{slide_h};
        }}
        .shape {{
            position: absolute;
            overflow: hidden;
        }}
        .shape-text {{
            padding: 10px;
        }}
        .shape-text.title {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #1a1a2e;
        }}
        .shape-text.subtitle {{
            font-size: 1.2rem;
            color: #555;
        }}
        .shape-text.body {{
            font-size: 1rem;
            color: #333;
            line-height: 1.6;
        }}
        .shape-text ul {{
            list-style: disc;
            margin-left: 25px;
        }}
        .shape-text li {{
            margin: 8px 0;
        }}
        .shape-image img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .slide-notes {{
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            padding: 20px 25px;
        }}
        .slide-notes h4 {{
            color: #6c757d;
            font-size: 0.85rem;
            margin-bottom: 10px;
        }}
        .slide-notes p {{
            color: #495057;
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        .controls button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .controls button:hover {{
            background: #5a6fd6;
            transform: scale(1.05);
        }}
        .slide-actions {{
            display: flex;
            gap: 8px;
        }}
        .slide-actions button {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 5px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background 0.2s;
        }}
        .slide-actions button:hover {{
            background: rgba(255,255,255,0.3);
        }}
        .slide-actions button.delete {{ background: rgba(255,77,77,0.5); }}
        .slide-actions button.delete:hover {{ background: rgba(255,77,77,0.7); }}
        .data-section {{
            background: #0d1117;
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
        }}
        .data-section h3 {{
            color: #58a6ff;
            margin-bottom: 15px;
        }}
        .data-section pre {{
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            color: #c9d1d9;
            font-size: 0.85rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        #json-data {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        <div class="presentation-header">
            <h1>{escape_html(source)}</h1>
            <p class="meta">共 {n_slides} 张幻灯片 | 尺寸: {slide_w:.1f}" × {slide_h:.1f}"</p>
        </div>

        <div id="slides-container">
            {"".join(slides_html)}
        </div>

        <div class="data-section">
            <h3>📋 结构化数据</h3>
            <button onclick="toggleData()" style="margin-bottom:15px;background:#238636;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">显示/隐藏 JSON</button>
            <pre id="json-data">{escape_html(json.dumps(json_for_display, ensure_ascii=False, indent=2))}</pre>
        </div>
    </div>

    <div class="controls">
        <button onclick="duplicateSlide()">📋 复制选中</button>
        <button onclick="moveUp()">⬆️ 上移</button>
        <button onclick="moveDown()">⬇️ 下移</button>
        <button onclick="exportOrder()">💾 导出顺序</button>
    </div>

    <script>
        let selectedSlide = null;

        document.querySelectorAll('.slide').forEach(slide => {{
            slide.addEventListener('click', function() {{
                document.querySelectorAll('.slide').forEach(s => s.style.outline = 'none');
                this.style.outline = '3px solid #667eea';
                selectedSlide = this;
            }});
        }});

        function toggleData() {{
            const el = document.getElementById('json-data');
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }}

        function duplicateSlide() {{
            if (!selectedSlide) {{ alert('请先选择一张幻灯片'); return; }}
            const clone = selectedSlide.cloneNode(true);
            clone.style.outline = 'none';
            selectedSlide.after(clone);
            updateSlideNumbers();
        }}

        function deleteSlide(btn) {{
            if (confirm('确定要删除这张幻灯片吗？')) {{
                btn.closest('.slide').remove();
                updateSlideNumbers();
            }}
        }}

        function moveUp() {{
            if (!selectedSlide || !selectedSlide.previousElementSibling) return;
            selectedSlide.parentNode.insertBefore(selectedSlide, selectedSlide.previousElementSibling);
            updateSlideNumbers();
        }}

        function moveDown() {{
            if (!selectedSlide || !selectedSlide.nextElementSibling) return;
            selectedSlide.parentNode.insertBefore(selectedSlide.nextElementSibling, selectedSlide);
            updateSlideNumbers();
        }}

        function updateSlideNumbers() {{
            document.querySelectorAll('.slide').forEach((slide, i) => {{
                slide.querySelector('.slide-number').textContent = '幻灯片 ' + (i + 1);
                slide.dataset.index = i;
            }});
        }}

        function exportOrder() {{
            const slides = document.querySelectorAll('.slide');
            const order = Array.from(slides).map(s => parseInt(s.dataset.originalIndex || s.dataset.index));
            const json = JSON.stringify({{
                "operation": "reorder",
                "original_count": {n_slides},
                "new_order": order,
                "new_count": slides.length
            }}, null, 2);

            const blob = new Blob([json], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'slide_order.json';
            a.click();
        }}
    </script>
</body>
</html>'''

    return html

