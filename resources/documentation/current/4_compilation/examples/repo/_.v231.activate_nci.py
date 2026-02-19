"""
Activation Script: Transform .pf.nci.json → concept_repo.json + inference_repo.json

This script implements Phase 4 (Activation) of the NormCode compilation pipeline.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def parse_comment_value(comment: str, key: str) -> str | None:
    """Extract value from a comment like '| %{key}: value'"""
    pattern = rf"\|\s*%{{\s*{re.escape(key)}\s*}}:\s*(.+)"
    match = re.search(pattern, comment)
    if match:
        return match.group(1).strip()
    return None


def parse_inline_comment(comment: str) -> dict:
    """Parse inline comment like '?{flow_index}: 1.1 | ?{sequence}: imperative'"""
    result = {}
    parts = comment.split("|")
    for part in parts:
        match = re.search(r"\?\{(\w+)\}:\s*(.+)", part.strip())
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def extract_concept_type_marker(concept_type: str) -> str:
    """Map concept_type to NormCode marker"""
    mapping = {
        "object": "{}",
        "proposition": "<>",
        "relation": "[]",
    }
    return mapping.get(concept_type, "{}")


def extract_operator_marker(operator_type: str) -> str:
    """Map operator_type to assigning marker"""
    mapping = {
        "specification": ".",
        "identity": "=",
        "abstraction": "%",
        "continuation": "+",
        "derelation": "-",
        "timing_conditional": "if",
        "timing_conditional_negated": "if!",
        "timing_after": "after",
    }
    return mapping.get(operator_type, "")


def get_annotation_value(attached_comments: list, key: str) -> str | None:
    """Extract annotation value from attached comments"""
    for comment in attached_comments:
        if comment.get("type") == "comment":
            nc_comment = comment.get("nc_comment", "")
            value = parse_comment_value(nc_comment, key)
            if value:
                return value
    return None


def get_literal_annotation(attached_comments: list, marker: str = None) -> tuple[str | None, any]:
    """
    Extract literal value from %{literal<$% name>}: value annotations.
    
    Args:
        attached_comments: List of comment objects
        marker: Optional marker to match (e.g., "$%")
    
    Returns:
        Tuple of (concept_name, wrapped_value) or (None, None) if not found
        The value is wrapped in literal notation like %(value)
    """
    import ast
    
    for comment in attached_comments:
        nc_comment = comment.get("nc_comment", "")
        # Pattern: | %{literal<$% name>}: value
        pattern = r"\|\s*%\{literal<\$([%=.+-])\s*([^>]+)>\}:\s*(.+)"
        match = re.search(pattern, nc_comment)
        if match:
            found_marker = match.group(1)
            concept_name = match.group(2).strip()
            value_str = match.group(3).strip()
            
            # If marker specified, check it matches
            if marker and found_marker != marker:
                continue
            
            # Parse the value and wrap each element in literal notation
            try:
                parsed_value = ast.literal_eval(value_str)
                # Wrap in literal notation
                if isinstance(parsed_value, list):
                    # Wrap each element: [1, 2] -> [%(1), %(2)]
                    wrapped_value = [f"%({item})" for item in parsed_value]
                else:
                    # Single value: 1 -> %(1)
                    wrapped_value = f"%({parsed_value})"
            except (ValueError, SyntaxError):
                # If parsing fails, wrap the string as-is
                wrapped_value = f"%({value_str})"
            
            return concept_name, wrapped_value
    
    return None, None


def get_sequence_type(attached_comments: list) -> str | None:
    """Extract sequence type from inline comments"""
    for comment in attached_comments:
        if comment.get("type") == "inline_comment":
            parsed = parse_inline_comment(comment.get("nc_comment", ""))
            if "sequence" in parsed:
                return parsed["sequence"]
    return None


def extract_literal_value(concept_name: str) -> str | None:
    """Extract literal value from concept names like 'phase_name: "phase_1"' or 'field_name: "operations"'"""
    # Pattern: key: "value" or key: 'value'
    match = re.search(r':\s*["\']([^"\']+)["\']', concept_name)
    if match:
        return match.group(1)
    return None


def is_literal_concept(concept_name: str) -> bool:
    """Check if concept name represents a literal value like 'phase_name: "phase_1"'"""
    return extract_literal_value(concept_name) is not None


def is_ground_concept(concept_data: dict, attached_comments: list) -> bool:
    """Determine if a concept is a ground concept"""
    # Check for /: Ground: comment
    for comment in attached_comments:
        nc_comment = comment.get("nc_comment", "")
        if "/: Ground:" in nc_comment:
            return True
    
    # Check for file_location annotation
    if get_annotation_value(attached_comments, "file_location"):
        return True
    
    # Check for perceptual_sign element type
    element_type = get_annotation_value(attached_comments, "ref_element")
    if element_type == "perceptual_sign":
        return True
    
    # Check for literal concepts like {phase_name: "phase_1"}
    concept_name = concept_data.get("concept_name", "")
    if is_literal_concept(concept_name):
        return True
    
    return False


def extract_file_location(attached_comments: list) -> str | None:
    """Extract file_location from annotations"""
    return get_annotation_value(attached_comments, "file_location")


def parse_axes(axes_str: str) -> list:
    """Parse axes string like '[_none_axis]' or '[date, signal]'"""
    if not axes_str:
        return ["_none_axis"]
    # Remove brackets and split
    axes_str = axes_str.strip("[]")
    axes = [a.strip() for a in axes_str.split(",")]
    return axes if axes else ["_none_axis"]


def concept_name_to_id(concept_name: str) -> str:
    """Convert concept name to ID"""
    # Remove special characters and normalize
    clean = re.sub(r"[{}[\]<>]", "", concept_name)
    clean = clean.strip().lower()
    clean = re.sub(r"\s+", "-", clean)
    clean = re.sub(r"[^a-z0-9-]", "", clean)
    return f"c-{clean}"


def format_concept_name(name: str, concept_type: str) -> str:
    """Format concept name with proper markers"""
    if concept_type == "object":
        return f"{{{name}}}"
    elif concept_type == "proposition":
        return f"<{name}>"
    elif concept_type == "relation":
        return f"[{name}]"
    return f"{{{name}}}"


def build_concept_repo(nci_data: list) -> list:
    """Build concept repository from NCI data"""
    concepts = {}  # concept_name -> concept_data
    function_concepts = {}  # function_concept nc_main -> function_concept_data
    
    # First pass: collect all concepts and their flow indices
    for inference in nci_data:
        # Process concept_to_infer
        cti = inference.get("concept_to_infer", {})
        if cti and cti.get("concept_name"):
            name = cti["concept_name"]
            concept_type = cti.get("concept_type", "object")
            attached_comments = cti.get("attached_comments", [])
            flow_index = cti.get("flow_index")
            
            if name not in concepts:
                concepts[name] = {
                    "concept_name": name,
                    "concept_type": concept_type,
                    "flow_indices": [],
                    "attached_comments": attached_comments,
                    "is_final": cti.get("inference_marker") == ":<:",
                }
            if flow_index:
                concepts[name]["flow_indices"].append(flow_index)
            # Merge comments if they have more annotations
            if len(attached_comments) > len(concepts[name].get("attached_comments", [])):
                concepts[name]["attached_comments"] = attached_comments
        
        # Process function_concept (NEW: add function concepts to repo)
        func = inference.get("function_concept", {})
        if func and func.get("nc_main"):
            nc_main = func["nc_main"]
            concept_type = func.get("concept_type", "operator")
            operator_type = func.get("operator_type")
            attached_comments = func.get("attached_comments", [])
            flow_index = func.get("flow_index")
            
            if nc_main not in function_concepts:
                function_concepts[nc_main] = {
                    "nc_main": nc_main,
                    "concept_type": concept_type,
                    "operator_type": operator_type,
                    "flow_indices": [],
                    "attached_comments": attached_comments,
                    "is_functional": True,
                }
            if flow_index:
                function_concepts[nc_main]["flow_indices"].append(flow_index)
        
        # Process value_concepts
        for vc in inference.get("value_concepts", []):
            if vc.get("concept_name"):
                name = vc["concept_name"]
                concept_type = vc.get("concept_type", "object")
                attached_comments = vc.get("attached_comments", [])
                flow_index = vc.get("flow_index")
                
                if name not in concepts:
                    concepts[name] = {
                        "concept_name": name,
                        "concept_type": concept_type,
                        "flow_indices": [],
                        "attached_comments": attached_comments,
                        "is_final": False,
                    }
                if flow_index:
                    concepts[name]["flow_indices"].append(flow_index)
        
        # Process other_concepts (context concepts)
        for oc in inference.get("other_concepts", []):
            if oc.get("concept_name"):
                name = oc["concept_name"]
                concept_type = oc.get("concept_type", "object")
                attached_comments = oc.get("attached_comments", [])
                flow_index = oc.get("flow_index")
                
                if name not in concepts:
                    concepts[name] = {
                        "concept_name": name,
                        "concept_type": concept_type,
                        "flow_indices": [],
                        "attached_comments": attached_comments,
                        "is_final": False,
                    }
                if flow_index:
                    concepts[name]["flow_indices"].append(flow_index)
    
    # Second pass: build concept repo entries for VALUE concepts
    concept_repo = []
    for name, data in concepts.items():
        attached_comments = data.get("attached_comments", [])
        concept_type = data.get("concept_type", "object")
        
        # Extract annotations
        axes_str = get_annotation_value(attached_comments, "ref_axes")
        element_type = get_annotation_value(attached_comments, "ref_element")
        shape_str = get_annotation_value(attached_comments, "ref_shape")
        file_location = extract_file_location(attached_comments)
        is_invariant_str = get_annotation_value(attached_comments, "is_invariant")
        
        is_ground = is_ground_concept(data, attached_comments)
        is_invariant = is_invariant_str and is_invariant_str.lower() == "true"
        
        # Build reference_data for ground concepts
        reference_data = None
        if is_ground:
            if file_location:
                reference_data = [f"%{{file_location}}({file_location})"]
            elif is_literal_concept(name):
                # Extract literal value from concept name like 'phase_name: "phase_1"'
                literal_value = extract_literal_value(name)
                if literal_value:
                    reference_data = [literal_value]
        
        # Parse axis names and extract primary axis name for TVA
        axis_names = parse_axes(axes_str)
        primary_axis_name = axis_names[0] if axis_names else "_none_axis"
        
        concept_entry = {
            "id": concept_name_to_id(name),
            "concept_name": format_concept_name(name, concept_type),
            "type": extract_concept_type_marker(concept_type),
            "flow_indices": sorted(list(set(data["flow_indices"]))),
            "description": None,
            "is_ground_concept": is_ground,
            "is_final_concept": data.get("is_final", False),
            "is_invariant": is_invariant,
            "reference_data": reference_data,
            "axis_name": primary_axis_name,  # Primary axis for TVA list-to-axis creation
            "reference_axis_names": axis_names,
            "reference_element_type": element_type,
            "natural_name": name,
        }
        concept_repo.append(concept_entry)
    
    # Third pass: build concept repo entries for FUNCTION concepts
    for nc_main, data in function_concepts.items():
        attached_comments = data.get("attached_comments", [])
        operator_type = data.get("operator_type")
        concept_type = data.get("concept_type", "operator")
        
        # Strip the <= marker first (it's inference syntax, not part of the concept)
        concept_name = re.sub(r"^<=\s*", "", nc_main)
        
        # Determine function concept type marker
        # Check for imperative markers: :: (standard), :>: (user-facing), :<: (final)
        is_imperative = bool(re.match(r'^:[:><]?:', concept_name))
        
        if (")<{" in concept_name) or ("<{" in concept_name and "}>" in concept_name):
            # Judgement: ::(...).<{...}> (new) or ::<{...}><...> (legacy)
            func_type_marker = "<{}>"
            element_type = "paradigm"
        elif is_imperative and ")<{" not in concept_name:
            # Imperative (::, :>:, :<:)
            func_type_marker = "({})"
            element_type = "paradigm"
        else:
            # Operator (assigning, grouping, timing, looping)
            func_type_marker = "({})"
            element_type = "operator"
        
        # Generate natural name from concept_name (already stripped of <=)
        natural_name = concept_name
        # Try to extract a cleaner name for imperatives/judgements
        # Handle all imperative variants: ::(...), :>:(...), :<:(...)
        name_match = re.search(r':[:><]?:\(([^)]+)\)', concept_name)
        if name_match:
            natural_name = name_match.group(1)
        else:
            # Try new syntax first: ::(name)<{...}>
            name_match = re.search(r':[:><]?:\(([^)]+)\)<\{', concept_name)
            if not name_match:
                # Fall back to legacy: ::<{name}><...>
                name_match = re.search(r"::<\{([^}]+)\}>", concept_name)
            if name_match:
                natural_name = name_match.group(1)
        
        # Generate unique ID
        func_id = "fc-" + re.sub(r"[^a-z0-9]+", "-", natural_name.lower()).strip("-")[:50]
        
        # Build reference field for function concepts
        reference_data = None
        if element_type == "paradigm":
            # Check for vertical inputs (v_input_provision annotation)
            v_input_provision = get_annotation_value(attached_comments, "v_input_provision")
            v_function_name = get_annotation_value(attached_comments, "v_function_name")
            
            if v_input_provision:
                # Determine norm based on file extension
                if v_input_provision.endswith(".md"):
                    norm = "prompt_location"
                elif v_input_provision.endswith(".py"):
                    norm = "script_location"
                else:
                    norm = "file_location"
                
                # Generate random 3-char hex ID
                import random
                hex_id = ''.join(random.choices('0123456789abcdef', k=3))
                
                # Create perceptual sign
                reference_data = [f"%{{{norm}}}{hex_id}({v_input_provision})"]
            else:
                # No vertical inputs - use dummy reference
                reference_data = ["%{dummy}(_)"]
        else:
            # Operators and other function concepts also get dummy reference
                reference_data = ["%{dummy}(_)"]
        
        concept_entry = {
            "id": func_id,
            "concept_name": concept_name,
            "type": func_type_marker,
            "flow_indices": sorted(list(set(data["flow_indices"]))),
            "description": natural_name,
            "is_ground_concept": True,  # Function concepts are ground (predefined, not computed)
            "is_final_concept": False,
            "reference_data": reference_data,
            "reference_axis_names": ["_none_axis"],
            "reference_element_type": element_type,
            "natural_name": natural_name,
        }
        concept_repo.append(concept_entry)
    
    # Sort by first flow_index
    def flow_sort_key(x):
        if not x["flow_indices"]:
            return [999]
        idx = x["flow_indices"][0]
        return [int(p) for p in idx.split(".")]
    
    concept_repo.sort(key=flow_sort_key)
    
    return concept_repo


def build_working_interpretation(inference: dict, sequence_type: str) -> dict:
    """Build working_interpretation based on sequence type
    
    WARNING: When a value concept receives bundled data (e.g., from a grouping operation),
    you may need to manually add 'value_selectors' with 'packed: true' to prevent the MVP
    step from unpacking the list/dict into multiple separate inputs.
    
    IMPORTANT: The field name and structure must match what _mvp.py expects:
    
    CORRECT structure:
        "value_selectors": {                    # <-- PLURAL: "value_selectors"
            "{bundled value}": { "packed": true }  # <-- concept name as KEY
        }
    
    WRONG structure (will silently fail):
        "value_selector": { "packed": true }    # <-- singular name, no concept key
    
    Why? The MVP code does:
        value_selectors = states.value_selectors or {}
        selector = value_selectors.get(concept_name) or {}  # <-- looks up BY concept name
        is_packed = selector.get("packed", False)
    
    So without the concept name as a key, the lookup returns {} and packed=False.
    
    This is hard to detect automatically because it depends on runtime data flow.
    Look for:
    - Values produced by grouping operations (inference_sequence: "grouping")
    - Values that pass through assigning from grouping outputs
    - Any structured data (dicts/lists) that should stay as a single input
    """
    func_concept = inference.get("function_concept", {})
    cti = inference.get("concept_to_infer", {})
    value_concepts = inference.get("value_concepts", [])
    other_concepts = inference.get("other_concepts", [])
    
    func_comments = func_concept.get("attached_comments", [])
    cti_flow_index = cti.get("flow_index", "")
    
    # Common fields
    wi = {
        "workspace": {},
        "flow_info": {"flow_index": cti_flow_index}
    }
    
    if sequence_type == "imperative":
        # Extract paradigm from norm_input
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        
        # Check for explicit value_order annotation first
        explicit_value_order = get_annotation_value(func_comments, "value_order")
        
        # Build value_order and value_selectors from value concepts
        value_order = {}
        value_selectors = {}
        
        if explicit_value_order:
            # Parse explicit value_order like [{all testing information}, {other concept}]
            # Remove outer brackets if present
            inner = explicit_value_order.strip()
            if inner.startswith('[') and inner.endswith(']'):
                inner = inner[1:-1].strip()
            
            # Split by comma to get individual concept references
            # But be careful - concept names can contain commas, so split carefully
            # Use regex to find concept patterns: {name}, [name], or <name>
            concept_patterns = re.findall(r'(\{[^}]+\}|\[[^\]]+\]|<[^>]+>)', inner)
            
            for i, pattern in enumerate(concept_patterns):
                # Pattern already includes the brackets, use as-is
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
                        # Explicit binding - use the specified order
                        value_order[formatted_name] = int(binding_match.group(1))
                        
                        # Check for value_selector annotations
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
                        
                        if selector:
                            value_selectors[formatted_name] = selector
                            
                    elif not has_any_binding:
                        # No bindings in any value_concept - fall back to position-based ordering
                        value_order[formatted_name] = i + 1
                    # If has_any_binding but this concept doesn't have one, skip it (it's a tree descendant, not an input)
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
        if value_selectors:
            wi["value_selectors"] = value_selectors
    
    elif sequence_type == "judgement":
        # Same as imperative plus assertion_condition
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        
        # Build value_order and value_selectors - ONLY those with explicit <:{N}> bindings
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
                    
                    # Check for value_selector annotations
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
                    
                    if selector:
                        value_selectors[formatted_name] = selector
                        
                elif not has_any_binding:
                    value_order[formatted_name] = i + 1
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
        if value_selectors:
            wi["value_selectors"] = value_selectors
        
        # Extract assertion from function concept
        nc_main = func_concept.get("nc_main", "")
        if "<ALL True>" in nc_main:
            wi["assertion_condition"] = {
                "quantifiers": {"axis": "all"},
                "condition": True
            }
    
    elif sequence_type == "assigning":
        operator_type = func_concept.get("operator_type", "specification")
        nc_main = func_concept.get("nc_main", "")
        marker = extract_operator_marker(operator_type)
        
        assign_source = None
        
        if marker == "%":
            # ABSTRACTION ($%) - create reference from literal face value
            # Extract face_value from %{literal<$% name>}: value annotation
            _, face_value = get_literal_annotation(func_comments, "%")
            
            # Extract axis_names from the concept_to_infer's ref_axes annotation
            cti_comments = cti.get("attached_comments", [])
            axes_str = get_annotation_value(cti_comments, "ref_axes")
            axis_names = parse_axes(axes_str) if axes_str else None
            
            wi["syntax"] = {
                "marker": marker,
                "face_value": face_value,
                "axis_names": axis_names,
            }
        
        elif marker == ".":
            # SPECIFICATION ($.) - "select/specify this value"
            # 
            # Source specification (in priority order):
            # 1. Annotation: %{assign_sources}: [{src1}, {src2}] - explicit list of candidate sources
            # 2. Inline list: $. %>({output}) %<[{src1}, {src2}] - inline source list
            # 3. Inline single: $. %>({X}) - the %>({...}) is both output and source
            #
            # Examples:
            #   $. %>({all AOC schema})
            #     -> assign_source: "{all AOC schema}"
            #
            #   $. %>({output}) %<[{src1}, {src2}]
            #     -> assign_source: ["{src1}", "{src2}"]
            #
            #   <= $. %>({output}) | %{assign_sources}: [{src1}, {src2}]
            #     -> assign_source: ["{src1}", "{src2}"]
            
            assign_source = None
            
            # Priority 1: Check for %{assign_sources} annotation
            assign_sources_str = get_annotation_value(func_comments, "assign_sources")
            if assign_sources_str:
                # Parse the list: [{src1}, {src2}] or [[src1], [src2]] or mixed
                import ast
                try:
                    sources_list = ast.literal_eval(assign_sources_str)
                    if isinstance(sources_list, list):
                        # Format each source with proper brackets
                        formatted_sources = []
                        for src in sources_list:
                            src_str = str(src).strip()
                            # Detect concept type from brackets
                            if src_str.startswith("{") or src_str.startswith("[") or src_str.startswith("<"):
                                formatted_sources.append(src_str)
                            else:
                                # Default to object notation
                                formatted_sources.append(f"{{{src_str}}}")
                        assign_source = formatted_sources if len(formatted_sources) > 1 else formatted_sources[0]
                except (ValueError, SyntaxError):
                    # Try manual parsing for [{name1}, {name2}] format
                    sources = re.findall(r'[\[{<]([^\]}>]+)[\]}>]', assign_sources_str)
                    if sources:
                        # Re-add brackets based on original format
                        formatted_sources = []
                        for match in re.finditer(r'([\[{<])([^\]}>]+)([\]}>])', assign_sources_str):
                            open_b, name, close_b = match.groups()
                            formatted_sources.append(f"{open_b}{name}{close_b}")
                        assign_source = formatted_sources if len(formatted_sources) > 1 else formatted_sources[0]
            
            # Priority 2: Check for inline %<[...] pattern (source list)
            if assign_source is None:
                inline_sources_match = re.search(r"%<\[([^\]]+)\]", nc_main)
                if inline_sources_match:
                    sources_text = inline_sources_match.group(1)
                    # Parse by tracking bracket depth
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
                    
                    assign_source = sources if len(sources) > 1 else (sources[0] if sources else None)
            
            # Priority 3: Extract single source from %>({...}), %>([...]), or %>(<...>)
            if assign_source is None:
                # Try object pattern %>({...})
                source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
                if source_match:
                    source_name = source_match.group(1)
                    assign_source = f"{{{source_name}}}"
                else:
                    # Try relation/list pattern %>([...])
                    source_match_list = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
                    if source_match_list:
                        source_name = source_match_list.group(1)
                        assign_source = f"[{source_name}]"
                    else:
                        # Try proposition pattern %>(<...>)
                        source_match_prop = re.search(r"%>\(<([^>]+)>\)", nc_main)
                        if source_match_prop:
                            source_name = source_match_prop.group(1)
                            assign_source = f"<{source_name}>"
                        else:
                            # No source found - this is an error
                            import logging
                            logging.warning(
                                f"Specification operator '.' at {cti_flow_index} has no source in %>(...)."
                            )
            
            wi["syntax"] = {
                "marker": marker,
                "assign_source": assign_source,
            }
        
        elif marker == "+":
            # CONTINUATION ($+) - append element to list
            # Syntax: $+ %>([dest_list]) %<({source_element}) %:(axis)
            # - %>([dest]) is the destination list
            # - %<({source}) is the element to append
            # - %:(axis) is the axis name
            
            assign_source = None
            assign_destination = None
            by_axes = None
            
            # Extract destination list from %>([...])
            dest_match = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
            if dest_match:
                assign_destination = f"[{dest_match.group(1)}]"
            
            # Extract source element from %<({...})
            source_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
            if source_match:
                assign_source = f"{{{source_match.group(1)}}}"
            
            # Extract axis from %:(...)
            axis_match = re.search(r"%:\(([^)]+)\)", nc_main)
            if axis_match:
                by_axes = axis_match.group(1)
            
            wi["syntax"] = {
                "marker": marker,
                "assign_source": assign_source,
                "assign_destination": assign_destination,
                "by_axes": by_axes,
            }
        
        else:
            # Other assigning operators (=, -) - use legacy extraction
            source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
            source_match_list = re.search(r"%>\[([^\]]+)\]", nc_main)
            
            if source_match:
                assign_source = f"{{{source_match.group(1)}}}"
            elif source_match_list:
                # Multiple sources from explicit list
                assign_source = source_match_list.group(1)
            
            # Only set syntax for the 'else' case - other markers set their own syntax
            wi["syntax"] = {
                "marker": marker,
                "assign_source": assign_source,
            }
    
    elif sequence_type == "grouping":
        nc_main = func_concept.get("nc_main", "")
        
        # Determine marker: &[{}] = in, &[#] = across
        if "&[{}]" in nc_main:
            marker = "in"
        elif "&[#]" in nc_main:
            marker = "across"
        else:
            marker = "in"
        
        # Extract create_axis from %+(...), default to None if not specified
        # When None, Grouper wraps all elements into a single element with shape (1,)
        create_axis_match = re.search(r"%\+\(([^)]+)\)", nc_main)
        create_axis = create_axis_match.group(1) if create_axis_match else None
        
        # Extract sources from %>[...] - handle nested brackets in concept names
        # Pattern: %>[{...}, [...], ...] where items can have internal brackets
        sources_section_match = re.search(r"%>\[(.+)\]", nc_main)
        sources = []
        if sources_section_match:
            sources_text = sources_section_match.group(1)
            # Parse by tracking bracket depth
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
        
        # Build by_axes to collapse _none_axis from each value concept
        # This triggers per-ref mode in Grouper and properly extracts elements
        # All value concepts have _none_axis (even after continuation, only shape changes)
        by_axes = [["_none_axis"] for _ in value_concepts]
        
        wi["syntax"] = {
            "marker": marker,
            "sources": sources,
            "create_axis": create_axis,
            "by_axes": by_axes,
        }
    
    elif sequence_type == "timing":
        operator_type = func_concept.get("operator_type", "timing_conditional")
        nc_main = func_concept.get("nc_main", "")
        
        # Determine marker
        if "@:!" in nc_main:
            marker = "if!"
        elif "@:'" in nc_main:
            marker = "if"
        elif "@." in nc_main:
            marker = "after"
        else:
            marker = "if"
        
        # Extract condition
        condition_match = re.search(r"@[:'!\.]+\s*\(<?([^>)]+)>?\)", nc_main)
        condition = condition_match.group(1) if condition_match else None
        
        wi["syntax"] = {
            "marker": marker,
            "condition": f"<{condition}>" if condition else None,
        }
        wi["blackboard"] = None
    
    elif sequence_type == "looping":
        nc_main = func_concept.get("nc_main", "")
        
        # Extract components from *. %>(...) %<(...) %:(...) %^(...) %@(...)
        base_match = re.search(r"%>\(\[?([^\])\]]+)\]?\)", nc_main)
        result_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
        axis_match = re.search(r"%:\(\{([^}]+)\}\)", nc_main)
        carry_match = re.search(r"%\^\(\{([^}]+)\}\)", nc_main)  # Carry state
        index_match = re.search(r"%@\((\d+)\)", nc_main)
        
        # Get context concepts (current element and carry state)
        current_element = None
        current_element_source = None
        carry_element = None
        carry_element_source = None
        
        for oc in other_concepts:
            if oc.get("inference_marker") == "<*":
                oc_nc_main = oc.get("nc_main", "")
                oc_name = oc.get("concept_name")
                
                # Extract source from <$([source])*> or <$({source})*-1>
                source_match = re.search(r"<\$\(([^)]+)\)\*(-?\d+)?", oc_nc_main)
                
                if source_match:
                    source_concept = source_match.group(1)
                    offset = source_match.group(2)  # e.g., "-1" for carry state
                    
                    if offset and int(offset) < 0:
                        # This is a carry state (e.g., previous active rules)
                        carry_element = oc_name
                        carry_element_source = source_concept
                    else:
                        # This is the current loop element
                        current_element = oc_name
                        current_element_source = source_concept
                else:
                    # No source specified, assume it's the current element
                    current_element = oc_name
        
        wi["syntax"] = {
            "marker": "every",
            "loop_index": int(index_match.group(1)) if index_match else 1,
            "LoopBaseConcept": f"[{base_match.group(1)}]" if base_match else None,
            "CurrentLoopBaseConcept": f"{{{current_element}}}" if current_element else None,
            "CurrentLoopBaseSource": current_element_source,
            "group_base": axis_match.group(1) if axis_match else None,
            "ConceptToInfer": [f"{{{result_match.group(1)}}}"] if result_match else [],
        }
        
        # Add carry state info if present
        if carry_element:
            wi["syntax"]["CarryStateConcept"] = f"{{{carry_element}}}"
            wi["syntax"]["CarryStateSource"] = carry_element_source
    
    return wi


def infer_sequence_type_from_nc_main(nc_main: str, concept_data: dict) -> str | None:
    """Infer sequence type from nc_main pattern - extracted for reuse"""
    # Judgement: ::(...).<{...}> (new syntax) or ::<{...}><...> (legacy)
    if "::" in nc_main and ")<{" in nc_main:
        return "judgement"
    if "::<{" in nc_main and "}>" in nc_main:  # Legacy support
        return "judgement"
    # Grouping: &[{}] or &[#]
    if "&[{}]" in nc_main or "&[#]" in nc_main:
        return "grouping"
    # Looping: *. %>
    if "*." in nc_main and "%>" in nc_main:
        return "looping"
    # Assigning: $. %> or $= %> etc (with or without <= prefix)
    if re.match(r"(<=\s*)?\$[.=%+-]", nc_main):
        return "assigning"
    # Timing: @:' or @:! or @.
    if "@:'" in nc_main or "@:!" in nc_main or "@." in nc_main:
        return "timing"
    # Try to infer from operator_type
    if concept_data.get("operator_type"):
        op_type = concept_data["operator_type"]
        if "timing" in op_type:
            return "timing"
        if op_type in ["specification", "identity", "abstraction", "continuation", "derelation"]:
            return "assigning"
    # Imperative: ::(...) without judgement markers
    if "::" in nc_main and "::<{" not in nc_main:
        return "imperative"
    if concept_data.get("concept_type") == "imperative":
        return "imperative"
    return None


def build_nested_operator_inference(oc: dict) -> dict | None:
    """Build an inference entry from a nested operator in other_concepts.
    
    This handles cases like:
        1.16.3.4.1.3: <= $. %>({classification})
    which are assigning operators nested inside loop bodies but placed in other_concepts.
    """
    nc_main = oc.get("nc_main", "")
    flow_index = oc.get("flow_index", "")
    
    # Infer sequence type
    sequence_type = infer_sequence_type_from_nc_main(nc_main, oc)
    if not sequence_type:
        return None
    
    # Strip <= marker for function_concept
    func_concept_name = re.sub(r"^<=\s*", "", nc_main)
    
    # Derive concept_to_infer based on sequence type
    concept_to_infer = None
    if sequence_type == "assigning":
        # For $. %>({x}), extract the source concept
        source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
        source_match_list = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
        if source_match:
            concept_to_infer = f"{{{source_match.group(1)}}}"
        elif source_match_list:
            concept_to_infer = f"[{source_match_list.group(1)}]"
        else:
            concept_to_infer = f"{{assigning_{flow_index.replace('.', '_')}}}"
    elif sequence_type == "timing":
        concept_to_infer = func_concept_name
    else:
        concept_to_infer = func_concept_name
    
    # Build working_interpretation for assigning
    wi = {
        "workspace": {},
        "flow_info": {"flow_index": flow_index}
    }
    
    if sequence_type == "assigning":
        operator_type = oc.get("operator_type", "specification")
        marker = extract_operator_marker(operator_type)
        
        if marker == "+":
            # CONTINUATION ($+) - append element to list
            assign_source = None
            assign_destination = None
            by_axes = None
            
            # Extract destination list from %>([...])
            dest_match = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
            if dest_match:
                assign_destination = f"[{dest_match.group(1)}]"
            
            # Extract source element from %<({...})
            source_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
            if source_match:
                assign_source = f"{{{source_match.group(1)}}}"
            
            # Extract axis from %:(...)
            axis_match = re.search(r"%:\(([^)]+)\)", nc_main)
            if axis_match:
                by_axes = axis_match.group(1)
            
            wi["syntax"] = {
                "marker": marker,
                "assign_source": assign_source,
                "assign_destination": assign_destination,
                "by_axes": by_axes,
            }
        else:
            # Other assigning operators - extract assign_source from %>(...)
            assign_source = None
            source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
            if source_match:
                assign_source = f"{{{source_match.group(1)}}}"
            
            wi["syntax"] = {
                "marker": marker,
                "assign_source": assign_source,
            }
        
    # Map sequence to inference_sequence
    sequence_mapping = {
        "imperative": "imperative_in_composition",
        "judgement": "judgement_in_composition",
        "assigning": "assigning",
        "grouping": "grouping",
        "timing": "timing",
        "looping": "looping",
    }
    
    return {
        "flow_info": {"flow_index": flow_index},
        "inference_sequence": sequence_mapping.get(sequence_type, sequence_type),
        "concept_to_infer": concept_to_infer,
        "function_concept": func_concept_name,
        "value_concepts": [],  # Nested operators typically don't have explicit value bindings
        "context_concepts": [],
        "working_interpretation": wi,
    }


def build_inference_repo(nci_data: list) -> list:
    """Build inference repository from NCI data"""
    inference_repo = []
    
    for inference in nci_data:
        cti = inference.get("concept_to_infer", {})
        func_concept = inference.get("function_concept", {})
        value_concepts = inference.get("value_concepts", [])
        other_concepts = inference.get("other_concepts", [])
        
        if not func_concept:
            continue
        
        # Get sequence type
        func_comments = func_concept.get("attached_comments", [])
        sequence_type = get_sequence_type(func_comments)
        
        if not sequence_type:
            # Try to infer from nc_main pattern first (most reliable)
            nc_main = func_concept.get("nc_main", "")
            
            # Judgement: ::(...).<{...}> (new syntax) or ::<{...}><...> (legacy)
            if "::" in nc_main and ")<{" in nc_main:
                sequence_type = "judgement"
            elif "::<{" in nc_main and "}>" in nc_main:  # Legacy support
                sequence_type = "judgement"
            # Grouping: &[{}] or &[#]
            elif "&[{}]" in nc_main or "&[#]" in nc_main:
                sequence_type = "grouping"
            # Looping: *. %>
            elif "*." in nc_main and "%>" in nc_main:
                sequence_type = "looping"
            # Assigning: $. %> or $= %> etc.
            elif re.match(r"<=\s*\$[.=%+-]", nc_main):
                sequence_type = "assigning"
            # Timing: @:' or @:! or @.
            elif "@:'" in nc_main or "@:!" in nc_main or "@." in nc_main:
                sequence_type = "timing"
            # Try to infer from operator_type
            elif func_concept.get("operator_type"):
                op_type = func_concept["operator_type"]
                if "timing" in op_type:
                    sequence_type = "timing"
                elif op_type in ["specification", "identity", "abstraction", "continuation", "derelation"]:
                    sequence_type = "assigning"
            # Imperative: ::(...) without judgement markers
            elif "::" in nc_main and "::<{" not in nc_main:
                sequence_type = "imperative"
            elif func_concept.get("concept_type") == "imperative":
                sequence_type = "imperative"
        
        if not sequence_type:
            continue
        
        # Build concept_to_infer name
        cti_name = cti.get("concept_name")
        cti_type = cti.get("concept_type", "object")
        cti_nc_main = cti.get("nc_main", "")
        
        # For function concept types (imperative, judgement, operator), use nc_main stripped of <=
        # For value concept types (object, proposition, relation), use formatted name
        if cti_type in ["imperative", "judgement", "operator"]:
            # Function concept - strip <= and use the function notation
            concept_to_infer = re.sub(r"^<=\s*", "", cti_nc_main) if cti_nc_main else None
        else:
            # Value concept - use formatted name with {} [] <> markers
            concept_to_infer = format_concept_name(cti_name, cti_type) if cti_name else None
        
        # Handle null concept_to_infer for specific sequence types
        if concept_to_infer is None:
            func_nc_main = func_concept.get("nc_main", "")
            
            if sequence_type == "assigning":
                # For assigning (e.g., $. %>({x})), derive from the source
                source_match = re.search(r"%>\(\{([^}]+)\}\)", func_nc_main)
                source_match_list = re.search(r"%>\[\{([^}]+)\}", func_nc_main)
                if source_match:
                    concept_to_infer = f"{{{source_match.group(1)}}}"
                elif source_match_list:
                    concept_to_infer = f"{{{source_match_list.group(1)}}}"
                else:
                    # Fallback: use flow_index as synthetic name
                    flow_idx = func_concept.get("flow_index", "unknown")
                    concept_to_infer = f"{{assigning_{flow_idx.replace('.', '_')}}}"
            
            elif sequence_type == "timing":
                # For timing, the concept_to_infer should already be set from nc_main
                # If still null, use the function concept's nc_main as fallback
                func_nc_main_stripped = re.sub(r"^<=\s*", "", func_nc_main)
                concept_to_infer = func_nc_main_stripped
        
        # Build function_concept string (strip <= marker - it's inference syntax, not part of concept)
        func_nc_main = func_concept.get("nc_main", "")
        func_concept_name = re.sub(r"^<=\s*", "", func_nc_main)
        
        # Build value_concepts list
        vc_list = []
        for vc in value_concepts:
            vc_name = vc.get("concept_name")
            if vc_name:
                vc_list.append(format_concept_name(vc_name, vc.get("concept_type", "object")))
        
        # Build context_concepts list
        ctx_list = []
        for oc in other_concepts:
            if oc.get("inference_marker") == "<*":
                oc_name = oc.get("concept_name")
                if oc_name:
                    ctx_list.append(format_concept_name(oc_name, oc.get("concept_type", "object")))
        
        # For timing sequences, context concepts should also be value concepts
        if sequence_type == "timing" and ctx_list:
            # Add context concepts to value_concepts for timing
            vc_list.extend(ctx_list)
        
        # Build working_interpretation
        wi = build_working_interpretation(inference, sequence_type)
        
        # Map sequence to inference_sequence
        sequence_mapping = {
            "imperative": "imperative_in_composition",
            "judgement": "judgement_in_composition",
            "assigning": "assigning",
            "grouping": "grouping",
            "timing": "timing",
            "looping": "looping",
        }
        
        # Use concept_to_infer's flow_index for consistency (it's the inference result position)
        cti_flow_index = cti.get("flow_index", func_concept.get("flow_index", ""))
        
        inference_entry = {
            "flow_info": {"flow_index": cti_flow_index},
            "inference_sequence": sequence_mapping.get(sequence_type, sequence_type),
            "concept_to_infer": concept_to_infer,
            "function_concept": func_concept_name,
            "value_concepts": vc_list,
            "context_concepts": ctx_list,
            "working_interpretation": wi,
        }
        
        inference_repo.append(inference_entry)
        
        # PATCH: Process nested operators in other_concepts as separate inferences
        # These are function concepts (like $. %>({x})) nested inside loops/timing gates
        for oc in other_concepts:
            if oc.get("inference_marker") == "<=":  # Operator marker
                nested_inf = build_nested_operator_inference(oc)
                if nested_inf:
                    inference_repo.append(nested_inf)
    
    # Sort by flow_index
    def flow_index_sort_key(item):
        idx = item.get("flow_info", {}).get("flow_index", "999")
        parts = idx.split(".")
        return [int(p) for p in parts]
    
    inference_repo.sort(key=flow_index_sort_key)
    
    return inference_repo


def main():
    # Paths
    base_dir = Path(__file__).parent
    nci_path = base_dir / "_.pf.nci.json"
    repos_dir = base_dir / "repos"
    repos_dir.mkdir(exist_ok=True)
    
    concept_repo_path = repos_dir / "concept_repo.json"
    inference_repo_path = repos_dir / "inference_repo.json"
    
    # Load NCI data
    print(f"Loading NCI from: {nci_path}")
    with open(nci_path, "r", encoding="utf-8") as f:
        nci_data = json.load(f)
    
    print(f"Found {len(nci_data)} inferences in NCI")
    
    # Build repositories
    print("Building concept repository...")
    concept_repo = build_concept_repo(nci_data)
    print(f"  -> {len(concept_repo)} unique concepts")
    
    print("Building inference repository...")
    inference_repo = build_inference_repo(nci_data)
    print(f"  -> {len(inference_repo)} inferences")
    
    # Write repositories
    print(f"\nWriting concept repo to: {concept_repo_path}")
    with open(concept_repo_path, "w", encoding="utf-8") as f:
        json.dump(concept_repo, f, indent=2, ensure_ascii=False)
    
    print(f"Writing inference repo to: {inference_repo_path}")
    with open(inference_repo_path, "w", encoding="utf-8") as f:
        json.dump(inference_repo, f, indent=2, ensure_ascii=False)
    
    print("\n[OK] Activation complete!")
    
    # Summary
    print("\n--- Summary ---")
    value_concepts = [c for c in concept_repo if c["type"] in ["{}", "[]", "<>"]]
    func_concepts = [c for c in concept_repo if c["type"] in ["({})", "<{}>"]]
    ground_concepts = [c for c in concept_repo if c["is_ground_concept"]]
    final_concepts = [c for c in concept_repo if c["is_final_concept"]]
    
    print(f"Value concepts: {len(value_concepts)}")
    print(f"Function concepts: {len(func_concepts)}")
    
    print(f"\nGround concepts ({len(ground_concepts)}):")
    for c in ground_concepts:
        print(f"  - {c['concept_name']}")
    
    print(f"\nFinal concepts ({len(final_concepts)}):")
    for c in final_concepts:
        print(f"  - {c['concept_name']}")
    
    # Inference sequence breakdown
    seq_counts = defaultdict(int)
    for inf in inference_repo:
        seq_counts[inf["inference_sequence"]] += 1
    
    print(f"\nInference sequences:")
    for seq, count in sorted(seq_counts.items()):
        print(f"  - {seq}: {count}")
    
    # Warning about packed values
    grouping_infs = [inf for inf in inference_repo if inf["inference_sequence"] == "grouping"]
    if grouping_infs:
        print("\n" + "="*60)
        print("[!] WARNING: Bundled values detected (grouping operations)")
        print("="*60)
        print("The following grouping operations produce bundled data:")
        for g in grouping_infs:
            flow_idx = g["flow_info"]["flow_index"]
            cti = g["concept_to_infer"]
            print(f"  - {flow_idx}: {cti}")
        print("\nIf these values are used as inputs to other inferences,")
        print("you may need to add 'value_selectors' with 'packed: true'")
        print("to prevent the MVP from unpacking them into multiple inputs.")
        print("="*60)


if __name__ == "__main__":
    main()
