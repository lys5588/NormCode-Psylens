"""
Working Interpretation Builder

Builds working_interpretation structures for different sequence types.
"""

import re

from .utils import parse_axes, parse_axis_list
from .annotations import get_annotation_value, get_literal_annotation
from .concepts import extract_operator_marker, format_concept_name


def build_working_interpretation(inference: dict, sequence_type: str) -> dict:
    """Build working_interpretation based on sequence type
    
    WARNING: When a value concept receives bundled data (e.g., from a grouping operation),
    you may need to manually add 'value_selectors' with 'packed: true' to prevent the MVP
    step from unpacking the list/dict into multiple separate inputs.
    """
    func_concept = inference.get("function_concept", {})
    cti = inference.get("concept_to_infer", {})
    value_concepts = inference.get("value_concepts", [])
    other_concepts = inference.get("other_concepts", [])
    
    func_comments = func_concept.get("attached_comments", [])
    cti_flow_index = cti.get("flow_index", "")
    
    # Extract output axis from concept_to_infer's ref_axes annotation
    cti_comments = cti.get("attached_comments", [])
    cti_axes_str = get_annotation_value(cti_comments, "ref_axes")
    cti_axes = parse_axes(cti_axes_str) if cti_axes_str else None
    output_axis = cti_axes[0] if cti_axes and cti_axes[0] != "_none_axis" else None
    
    # Common fields
    wi = {
        "workspace": {},
        "flow_info": {"flow_index": cti_flow_index}
    }
    
    if sequence_type == "imperative":
        wi.update(_build_imperative_wi(inference, func_comments, value_concepts, output_axis))
    elif sequence_type == "judgement":
        wi.update(_build_judgement_wi(inference, func_concept, func_comments, value_concepts, output_axis))
    elif sequence_type == "assigning":
        wi.update(_build_assigning_wi(inference, func_concept, func_comments, cti))
    elif sequence_type == "grouping":
        wi.update(_build_grouping_wi(inference, func_concept, func_comments, value_concepts))
    elif sequence_type == "timing":
        wi.update(_build_timing_wi(func_concept))
    elif sequence_type == "looping":
        wi.update(_build_looping_wi(func_concept, other_concepts))
    
    return wi


def _build_imperative_wi(inference: dict, func_comments: list, value_concepts: list, output_axis: str | None) -> dict:
    """Build working interpretation for imperative sequence"""
    result = {}
    
    paradigm = get_annotation_value(func_comments, "norm_input")
    body_faculty = get_annotation_value(func_comments, "body_faculty")
    
    # Check for explicit value_order annotation first
    explicit_value_order = get_annotation_value(func_comments, "value_order")
    
    # Build value_order and value_selectors from value concepts
    value_order = {}
    value_selectors = {}
    
    if explicit_value_order:
        # Parse explicit value_order like [{all testing information}, {other concept}]
        inner = explicit_value_order.strip()
        if inner.startswith('[') and inner.endswith(']'):
            inner = inner[1:-1].strip()
        
        # Find concept patterns: {name}, [name], or <name>
        concept_patterns = re.findall(r'(\{[^}]+\}|\[[^\]]+\]|<[^>]+>)', inner)
        
        for i, pattern in enumerate(concept_patterns):
            value_order[pattern] = i + 1
    else:
        # Fall back to inferring from value concepts
        has_any_binding = any(re.search(r"<:\{(\d+)\}>", vc.get("nc_main", "")) for vc in value_concepts)
    
        for i, vc in enumerate(value_concepts):
            vc_name = vc.get("concept_name")
            if vc_name:
                nc_main = vc.get("nc_main", "")
                vc_comments = vc.get("attached_comments", [])
                binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
                formatted_name = format_concept_name(vc_name, vc.get("concept_type", "object"))
                
                if binding_match:
                    value_order[formatted_name] = int(binding_match.group(1))
                    
                    # Check for value_selector annotations
                    selector = _extract_value_selector(vc_comments)
                    if selector:
                        value_selectors[formatted_name] = selector
                        
                elif not has_any_binding:
                    value_order[formatted_name] = i + 1
    
    result["paradigm"] = paradigm
    result["body_faculty"] = body_faculty
    result["value_order"] = value_order
    if value_selectors:
        result["value_selectors"] = value_selectors
    if output_axis:
        result["output_axis"] = output_axis
    
    return result


def _build_judgement_wi(inference: dict, func_concept: dict, func_comments: list, value_concepts: list, output_axis: str | None) -> dict:
    """Build working interpretation for judgement sequence"""
    result = {}
    
    paradigm = get_annotation_value(func_comments, "norm_input")
    body_faculty = get_annotation_value(func_comments, "body_faculty")
    
    value_order = {}
    value_selectors = {}
    has_any_binding = any(re.search(r"<:\{(\d+)\}>", vc.get("nc_main", "")) for vc in value_concepts)
    
    for i, vc in enumerate(value_concepts):
        vc_name = vc.get("concept_name")
        if vc_name:
            nc_main = vc.get("nc_main", "")
            vc_comments = vc.get("attached_comments", [])
            binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
            formatted_name = format_concept_name(vc_name, vc.get("concept_type", "object"))
            
            if binding_match:
                value_order[formatted_name] = int(binding_match.group(1))
                selector = _extract_value_selector(vc_comments)
                if selector:
                    value_selectors[formatted_name] = selector
            elif not has_any_binding:
                value_order[formatted_name] = i + 1
    
    result["paradigm"] = paradigm
    result["body_faculty"] = body_faculty
    result["value_order"] = value_order
    if value_selectors:
        result["value_selectors"] = value_selectors
    
    # Extract assertion from function concept
    nc_main = func_concept.get("nc_main", "")
    if "<ALL True>" in nc_main:
        result["assertion_condition"] = {
            "quantifiers": {"axis": "all"},
            "condition": True
        }
    if output_axis:
        result["output_axis"] = output_axis
    
    return result


def _build_assigning_wi(inference: dict, func_concept: dict, func_comments: list, cti: dict) -> dict:
    """Build working interpretation for assigning sequence"""
    result = {}
    
    operator_type = func_concept.get("operator_type", "specification")
    nc_main = func_concept.get("nc_main", "")
    marker = extract_operator_marker(operator_type)
    
    if marker == "%":
        result["syntax"] = _build_abstraction_syntax(func_comments, cti)
    elif marker == ".":
        result["syntax"] = _build_specification_syntax(nc_main, func_comments, cti.get("flow_index", ""))
    elif marker == "+":
        result["syntax"] = _build_continuation_syntax(nc_main)
    else:
        result["syntax"] = _build_default_assigning_syntax(nc_main, marker)
    
    return result


def _build_grouping_wi(inference: dict, func_concept: dict, func_comments: list, value_concepts: list) -> dict:
    """Build working interpretation for grouping sequence"""
    result = {}
    nc_main = func_concept.get("nc_main", "")
    
    # Determine marker: &[{}] = in, &[#] = across
    if "&[{}]" in nc_main:
        marker = "in"
    elif "&[#]" in nc_main:
        marker = "across"
    else:
        marker = "in"
    
    # Extract create_axis from %+(...)
    create_axis_match = re.search(r"%\+\(([^)]+)\)", nc_main)
    create_axis = create_axis_match.group(1) if create_axis_match else None
    
    # Extract sources from %>[...]
    sources = _extract_grouping_sources(nc_main)
    
    # Build by_axes with priority order
    by_axes, by_axes_source = _extract_by_axes(nc_main, func_comments, value_concepts)
    
    result["syntax"] = {
        "marker": marker,
        "sources": sources,
        "create_axis": create_axis,
        "by_axes": by_axes,
        "by_axes_source": by_axes_source,
    }
    
    return result


def _build_timing_wi(func_concept: dict) -> dict:
    """Build working interpretation for timing sequence"""
    result = {}
    nc_main = func_concept.get("nc_main", "")
    
    if "@:!" in nc_main:
        marker = "if!"
    elif "@:'" in nc_main:
        marker = "if"
    elif "@." in nc_main:
        marker = "after"
    else:
        marker = "if"
    
    condition_match = re.search(r"@[:'!\.]+\s*\(<?([^>)]+)>?\)", nc_main)
    condition = condition_match.group(1) if condition_match else None
    
    # For @:' and @:! (if/if!), the condition is a proposition - wrap in <>
    # For @. (after/completion check), preserve the concept name as-is
    if condition:
        if marker == "after":
            # Completion check: preserve concept name with its original brackets
            # The condition might be {concept}, [concept], or <concept>
            formatted_condition = condition
            if not (condition.startswith("{") or condition.startswith("[") or condition.startswith("<")):
                formatted_condition = f"{{{condition}}}"
        else:
            # If/If! check: condition is a proposition
            formatted_condition = f"<{condition}>"
    else:
        formatted_condition = None
    
    result["syntax"] = {
        "marker": marker,
        "condition": formatted_condition,
    }
    result["blackboard"] = None
    
    return result


def _build_looping_wi(func_concept: dict, other_concepts: list) -> dict:
    """Build working interpretation for looping sequence"""
    result = {}
    nc_main = func_concept.get("nc_main", "")
    func_comments = func_concept.get("attached_comments", [])
    
    base_match = re.search(r"%>\(\[?([^\])\]]+)\]?\)", nc_main)
    result_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
    context_match = re.search(r"%:\(\{([^}]+)\}\)", nc_main)  # Extracts context concept name
    carry_match = re.search(r"%\^\(\{([^}]+)\}\)", nc_main)
    index_match = re.search(r"%@\((\d+)\)", nc_main)
    
    current_element = None
    current_element_source = None
    carry_element = None
    carry_element_source = None
    context_concept_axis = None  # Axis from context concept's %{ref_axes}
    
    for oc in other_concepts:
        if oc.get("inference_marker") == "<*":
            oc_nc_main = oc.get("nc_main", "")
            oc_name = oc.get("concept_name")
            oc_comments = oc.get("attached_comments", [])
            
            source_match = re.search(r"<\$\(([^)]+)\)\*(-?\d+)?", oc_nc_main)
            
            if source_match:
                source_concept = source_match.group(1)
                offset = source_match.group(2)
                
                if offset and int(offset) < 0:
                    carry_element = oc_name
                    carry_element_source = source_concept
                else:
                    current_element = oc_name
                    current_element_source = source_concept
                    # Extract axis from context concept's %{ref_axes} annotation
                    ref_axes_str = get_annotation_value(oc_comments, "ref_axes")
                    if ref_axes_str:
                        axes = parse_axes(ref_axes_str)
                        if axes and len(axes) > 0 and axes[0] != "_none_axis":
                            context_concept_axis = axes[0]
            else:
                current_element = oc_name
    
    # Determine group_base with priority:
    # 1. Explicit %{group_base} annotation on the looping function
    # 2. Context concept's axis from %{ref_axes}
    # 3. Fallback to context concept name (legacy behavior)
    explicit_group_base = get_annotation_value(func_comments, "group_base")
    if explicit_group_base:
        group_base = explicit_group_base
    elif context_concept_axis:
        group_base = context_concept_axis
    elif context_match:
        group_base = context_match.group(1)  # Legacy: use concept name
    else:
        group_base = None
    
    result["syntax"] = {
        "marker": "every",
        "loop_index": int(index_match.group(1)) if index_match else 1,
        "LoopBaseConcept": f"[{base_match.group(1)}]" if base_match else None,
        "CurrentLoopBaseConcept": f"{{{current_element}}}" if current_element else None,
        "CurrentLoopBaseSource": current_element_source,
        "group_base": group_base,
        "ConceptToInfer": [f"{{{result_match.group(1)}}}"] if result_match else [],
    }
    
    if carry_element:
        result["syntax"]["CarryStateConcept"] = f"{{{carry_element}}}"
        result["syntax"]["CarryStateSource"] = carry_element_source
    
    return result


# Helper functions

def _extract_value_selector(vc_comments: list) -> dict | None:
    """Extract value selector annotations from comments"""
    selector = {}
    source_concept = get_annotation_value(vc_comments, "selector_source")
    select_key = get_annotation_value(vc_comments, "selector_key")
    select_index = get_annotation_value(vc_comments, "selector_index")
    is_packed = get_annotation_value(vc_comments, "selector_packed")
    should_unpack = get_annotation_value(vc_comments, "selector_unpack")
    
    if source_concept:
        selector["source_concept"] = source_concept
    if select_key:
        selector["key"] = select_key
    if select_index:
        selector["index"] = int(select_index)
    if is_packed and is_packed.lower() == "true":
        selector["packed"] = True
    if should_unpack and should_unpack.lower() == "true":
        selector["unpack"] = True
    
    return selector if selector else None


def _build_abstraction_syntax(func_comments: list, cti: dict) -> dict:
    """Build syntax for abstraction ($%) operator"""
    _, face_value = get_literal_annotation(func_comments, "%")
    
    cti_comments = cti.get("attached_comments", [])
    axes_str = get_annotation_value(cti_comments, "ref_axes")
    axis_names = parse_axes(axes_str) if axes_str else None
    
    return {
        "marker": "%",
        "face_value": face_value,
        "axis_names": axis_names,
    }


def _build_specification_syntax(nc_main: str, func_comments: list, flow_index: str) -> dict:
    """Build syntax for specification ($.) operator"""
    assign_source = None
    
    # Priority 1: Check for %{assign_sources} annotation
    assign_sources_str = get_annotation_value(func_comments, "assign_sources")
    if assign_sources_str:
        assign_source = _parse_assign_sources(assign_sources_str)
    
    # Priority 2: Check for inline %<[...] pattern
    if assign_source is None:
        inline_sources_match = re.search(r"%<\[([^\]]+)\]", nc_main)
        if inline_sources_match:
            assign_source = _parse_sources_text(inline_sources_match.group(1))
    
    # Priority 3: Extract single source from %>(...)
    if assign_source is None:
        assign_source = _extract_single_source(nc_main)
        
        if assign_source is None:
            import logging
            logging.warning(f"Specification operator '.' at {flow_index} has no source in %>(...).")
    
    return {
        "marker": ".",
        "assign_source": assign_source,
    }


def _build_continuation_syntax(nc_main: str) -> dict:
    """Build syntax for continuation ($+) operator"""
    assign_source = None
    assign_destination = None
    by_axes = None
    
    dest_match = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
    if dest_match:
        assign_destination = f"[{dest_match.group(1)}]"
    
    source_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
    if source_match:
        assign_source = f"{{{source_match.group(1)}}}"
    
    axis_match = re.search(r"%:\(([^)]+)\)", nc_main)
    if axis_match:
        by_axes = axis_match.group(1)
    
    return {
        "marker": "+",
        "assign_source": assign_source,
        "assign_destination": assign_destination,
        "by_axes": by_axes,
    }


def _build_default_assigning_syntax(nc_main: str, marker: str) -> dict:
    """Build syntax for other assigning operators"""
    assign_source = _extract_single_source(nc_main)
    
    return {
        "marker": marker,
        "assign_source": assign_source,
    }


def _extract_grouping_sources(nc_main: str) -> list:
    """Extract sources from %>[...] in grouping operation"""
    sources = []
    sources_section_match = re.search(r"%>\[(.+)\]", nc_main)
    if sources_section_match:
        sources = _parse_sources_text(sources_section_match.group(1))
        if isinstance(sources, str):
            sources = [sources]
    return sources


def _extract_by_axes(nc_main: str, func_comments: list, value_concepts: list) -> tuple[list, str]:
    """
    Extract by_axes for grouping operation.
    Priority: D (per-concept) > C (functional) > B (inline) > fallback
    """
    by_axes = None
    by_axes_source = None
    
    # Option D: Per-concept annotation
    per_concept_axes = []
    all_have_annotation = True
    for vc in value_concepts:
        vc_comments = vc.get("attached_comments", [])
        collapse_axes = get_annotation_value(vc_comments, "collapse_in_grouping")
        if collapse_axes:
            parsed = parse_axis_list(collapse_axes)
            if parsed and isinstance(parsed[0], list):
                per_concept_axes.append(parsed[0])
            else:
                per_concept_axes.append(parsed)
        else:
            all_have_annotation = False
            per_concept_axes.append(None)
    
    if all_have_annotation and per_concept_axes:
        by_axes = per_concept_axes
        by_axes_source = "option_d_per_concept"
    
    # Option C: Functional annotation
    if by_axes is None:
        by_axes_annotation = get_annotation_value(func_comments, "by_axes")
        if by_axes_annotation:
            parsed = parse_axis_list(by_axes_annotation)
            if parsed:
                if isinstance(parsed[0], list):
                    by_axes = parsed
                else:
                    by_axes = [parsed for _ in value_concepts]
                by_axes_source = "option_c_functional"
    
    # Option B: Inline modifier
    if by_axes is None:
        inline_match = re.search(r"%-\[(.+?)\](?=\s|%|\||$)", nc_main)
        if inline_match:
            inline_text = f"[{inline_match.group(1)}]"
            parsed = parse_axis_list(inline_text)
            if parsed:
                if isinstance(parsed[0], list):
                    by_axes = parsed
                else:
                    by_axes = [parsed for _ in value_concepts]
                by_axes_source = "option_b_inline"
    
    # Fallback
    if by_axes is None:
        by_axes = []
        for vc in value_concepts:
            vc_comments = vc.get("attached_comments", [])
            axes_str = get_annotation_value(vc_comments, "ref_axes")
            if axes_str:
                by_axes.append(parse_axes(axes_str))
            else:
                by_axes.append(["_none_axis"])
        by_axes_source = "fallback_ref_axes"
    
    # Ensure length matches
    if len(by_axes) < len(value_concepts):
        by_axes.extend([["_none_axis"]] * (len(value_concepts) - len(by_axes)))
    elif len(by_axes) > len(value_concepts):
        by_axes = by_axes[:len(value_concepts)]
    
    return by_axes, by_axes_source


def _parse_assign_sources(assign_sources_str: str) -> str | list:
    """Parse assign_sources annotation value"""
    import ast
    try:
        sources_list = ast.literal_eval(assign_sources_str)
        if isinstance(sources_list, list):
            formatted_sources = []
            for src in sources_list:
                src_str = str(src).strip()
                if src_str.startswith("{") or src_str.startswith("[") or src_str.startswith("<"):
                    formatted_sources.append(src_str)
                else:
                    formatted_sources.append(f"{{{src_str}}}")
            return formatted_sources if len(formatted_sources) > 1 else formatted_sources[0]
    except (ValueError, SyntaxError):
        pass
    
    return _parse_sources_text(assign_sources_str.strip("[]"))


def _parse_sources_text(sources_text: str) -> str | list:
    """Parse sources text with bracket tracking"""
    sources = []
    current = ""
    depth = 0
    for char in sources_text:
        if char in "{[<":
            depth += 1
            current += char
        elif char in "}]>":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            if current.strip():
                sources.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        sources.append(current.strip())
    
    return sources if len(sources) > 1 else (sources[0] if sources else None)


def _extract_single_source(nc_main: str) -> str | None:
    """Extract single source from %>(...) patterns"""
    # Try object pattern %>({...})
    source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
    if source_match:
        return f"{{{source_match.group(1)}}}"
    
    # Try relation/list pattern %>([...])
    source_match_list = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
    if source_match_list:
        return f"[{source_match_list.group(1)}]"
    
    # Try proposition pattern %>(<...>)
    source_match_prop = re.search(r"%>\(<([^>]+)>\)", nc_main)
    if source_match_prop:
        return f"<{source_match_prop.group(1)}>"
    
    return None

