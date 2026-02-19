"""
NormCode Parser

Parses .pf.ncd files to .nci.json format.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .concepts import detect_concept_type


def calculate_depth(line: str) -> int:
    """Calculate indentation depth (4 spaces = 1 level)."""
    stripped = line.lstrip()
    spaces = len(line) - len(stripped)
    return spaces // 4


def assign_flow_indices(lines: List[str]) -> List[Dict[str, Any]]:
    """Parse lines and assign flow indices based on structure."""
    parsed_lines = []
    indices = []  # Stack of counters for each depth
    
    for raw_line in lines:
        if not raw_line.strip():
            continue
            
        depth = calculate_depth(raw_line)
        content = raw_line.strip()
        
        is_concept = False
        main_part = content
        inline_comment = None
        explicit_flow_index = None
        
        # Check for NCN annotation line
        is_ncn_annotation = content.startswith('|?{natural language}:') or content.startswith('|?{')
        
        # Split inline comments/metadata
        if '|' in content and not is_ncn_annotation:
            parts = content.split('|', 1)
            main_part = parts[0].strip()
            inline_comment = parts[1].strip()
            
            if inline_comment:
                flow_match = re.search(r'\?{flow_index}:\s*([\d.]+)', inline_comment)
                if flow_match:
                    explicit_flow_index = flow_match.group(1)
        
        # Concept prefixes
        concept_prefixes = [':<:', ':>:', '<=', '<-', '<*', '$%', '$.', '*.',  '$+', '&[', '@:', '@:!', '::']
        for prefix in concept_prefixes:
            if main_part.startswith(prefix):
                is_concept = True
                break
        
        flow_index = None
        
        if is_concept:
            if explicit_flow_index:
                flow_index = explicit_flow_index
                parts = [int(p) for p in explicit_flow_index.split('.')]
                indices = parts[:]
            else:
                while len(indices) <= depth:
                    indices.append(0)
                indices = indices[:depth+1]
                indices[depth] += 1
                flow_index = ".".join(map(str, indices))
        else:
            if parsed_lines:
                for prev in reversed(parsed_lines):
                    if prev['type'] == 'main' and prev['flow_index']:
                        flow_index = prev['flow_index']
                        break
        
        concept_info = detect_concept_type(main_part) if is_concept else {}
        
        # Handle pipe-only lines
        if not is_concept and not main_part and inline_comment:
            parsed_lines.append({
                "raw_line": raw_line,
                "content": f"| {inline_comment}",
                "depth": depth,
                "flow_index": flow_index,
                "type": "comment"
            })
        else:
            if is_concept or main_part:
                line_entry = {
                    "raw_line": raw_line,
                    "content": main_part,
                    "depth": depth,
                    "flow_index": flow_index,
                    "type": "main" if is_concept else "comment"
                }
                if is_concept and concept_info:
                    line_entry["inference_marker"] = concept_info.get("inference_marker")
                    line_entry["concept_type"] = concept_info.get("concept_type")
                    line_entry["operator_type"] = concept_info.get("operator_type")
                    line_entry["concept_name"] = concept_info.get("concept_name")
                    if concept_info.get("warnings"):
                        line_entry["warnings"] = concept_info["warnings"]
                parsed_lines.append(line_entry)
            
            if inline_comment:
                parsed_lines.append({
                    "raw_line": "",
                    "content": inline_comment,
                    "depth": depth,
                    "flow_index": flow_index,
                    "type": "inline_comment"
                })
    
    return parsed_lines


def parse_ncdn(ncdn_content: str) -> Dict[str, Any]:
    """Parse .ncdn/.pf.ncd format to structured JSON."""
    lines = ncdn_content.splitlines()
    parsed_ncd = assign_flow_indices(lines)
    
    merged_lines = []
    i = 0
    
    while i < len(parsed_ncd):
        line = parsed_ncd[i]
        
        merged_item = {
            "flow_index": line['flow_index'],
            "type": line['type'],
            "depth": line['depth']
        }
        
        if line['type'] == 'main':
            merged_item['nc_main'] = line['content']
            
            for key in ['inference_marker', 'concept_type', 'operator_type', 'concept_name', 'warnings']:
                if key in line:
                    merged_item[key] = line[key]
            
            # Look ahead for NCN annotation
            lookahead = i + 1
            if lookahead < len(parsed_ncd) and parsed_ncd[lookahead]['type'] == 'inline_comment':
                lookahead += 1
            
            if lookahead < len(parsed_ncd):
                next_line = parsed_ncd[lookahead]
                next_content = next_line['content']
                
                if next_content.startswith('|?{natural language}:') or next_content.startswith('|?{'):
                    if '|?{natural language}:' in next_content:
                        ncn_content = next_content.split('|?{natural language}:', 1)[1].strip()
                    else:
                        ncn_content = next_content.split(':', 1)[1].strip() if ':' in next_content else ''
                    merged_item['ncn_content'] = ncn_content
                    
        elif line['type'] == 'inline_comment':
            merged_item['nc_comment'] = line['content']
        elif line['type'] == 'comment':
            if line['content'].startswith('|?{natural language}:') or line['content'].startswith('|?{'):
                i += 1
                continue
            merged_item['nc_comment'] = line['content']
        
        merged_lines.append(merged_item)
        i += 1
    
    return {"lines": merged_lines}


def to_nci(nc_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert nc.json structure to nci.json format."""
    lines = nc_json.get('lines', [])
    if not lines:
        return []
    
    # Group lines by flow_index
    concepts_by_index: Dict[str, Dict] = {}
    
    for line in lines:
        fi = line.get('flow_index')
        if not fi:
            continue
            
        if fi not in concepts_by_index:
            concepts_by_index[fi] = {"main": None, "comments": []}
            
        if line['type'] == 'main':
            concepts_by_index[fi]['main'] = line
        else:
            concepts_by_index[fi]['comments'].append(line)
    
    # Build parent-child relationships
    parent_stack = []
    children_map = {}
    
    for line in lines:
        if line['type'] != 'main':
            continue
            
        depth = line.get('depth', 0)
        fi = line.get('flow_index')
        if not fi:
            continue
        
        parent_fi = None
        while parent_stack:
            last_fi, last_depth = parent_stack[-1]
            if last_depth < depth:
                parent_fi = last_fi
                break
            else:
                parent_stack.pop()
        
        if parent_fi:
            if parent_fi not in children_map:
                children_map[parent_fi] = []
            children_map[parent_fi].append(fi)
        
        parent_stack.append((fi, depth))
    
    def get_concept_obj(fi):
        c = concepts_by_index.get(fi)
        if not c:
            return None
        obj = c['main'].copy() if c['main'] else {"flow_index": fi, "type": "virtual", "depth": -1}
        obj['attached_comments'] = c['comments']
        return obj
    
    # Build NCI groups
    nci_groups = []
    
    def index_sort_key(fi):
        try:
            return [int(x) for x in fi.split('.')]
        except:
            return []
    
    all_parents = sorted(children_map.keys(), key=index_sort_key)
    
    for parent_fi in all_parents:
        children_fis = children_map[parent_fi]
        
        function_child_fi = None
        value_child_fis = []
        other_child_fis = []
        
        has_function = False
        
        for child_fi in children_fis:
            child_main = concepts_by_index[child_fi]['main']
            if not child_main:
                continue
            content = child_main.get('nc_main', '').strip()
            
            if content.startswith('<='):
                if function_child_fi is None:
                    function_child_fi = child_fi
                    has_function = True
                else:
                    other_child_fis.append(child_fi)
            elif content.startswith('<-'):
                value_child_fis.append(child_fi)
            else:
                other_child_fis.append(child_fi)
        
        if has_function:
            group = {
                "concept_to_infer": get_concept_obj(parent_fi),
                "function_concept": get_concept_obj(function_child_fi),
                "value_concepts": [get_concept_obj(f) for f in value_child_fis],
                "other_concepts": [get_concept_obj(f) for f in other_child_fis]
            }
            nci_groups.append(group)
    
    return nci_groups


def parse_pf_ncd_to_nci(pf_ncd_path: str) -> str:
    """
    Parse a .pf.ncd file and convert to NCI JSON.
    
    Args:
        pf_ncd_path: Path to the .pf.ncd file
        
    Returns:
        Path to the output .nci.json file
    """
    pf_ncd_path = Path(pf_ncd_path)
    
    if not pf_ncd_path.exists():
        raise FileNotFoundError(f"File not found: {pf_ncd_path}")
    
    content = pf_ncd_path.read_text(encoding='utf-8')
    parsed = parse_ncdn(content)
    nci_data = to_nci(parsed)
    
    # Determine output path
    if pf_ncd_path.name.endswith('.pf.ncd'):
        output_path = pf_ncd_path.parent / (pf_ncd_path.stem.replace('.pf', '.pf.nci') + '.json')
    else:
        output_path = pf_ncd_path.with_suffix('.nci.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nci_data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Parsed {len(parsed['lines'])} lines")
    print(f"[OK] Generated {len(nci_data)} inference groups")
    print(f"[OK] Output: {output_path}")
    
    return str(output_path)

