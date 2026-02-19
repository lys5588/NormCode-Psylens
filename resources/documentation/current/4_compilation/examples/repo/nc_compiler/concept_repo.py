"""
Concept Repository Builder

Builds concept_repo.json from NCI data.
"""

import re
import random

from .utils import parse_axes, extract_literal_value, is_literal_concept
from .annotations import get_annotation_value, get_literal_annotation, extract_file_location
from .concepts import (
    extract_concept_type_marker,
    concept_name_to_id,
    format_concept_name,
    is_ground_concept,
)


def build_concept_repo(nci_data: list) -> list:
    """Build concept repository from NCI data"""
    concepts = {}  # concept_name -> concept_data
    function_concepts = {}  # function_concept nc_main -> function_concept_data
    inferred_concepts = set()  # Track concepts that are produced by operations (NOT ground)
    
    # First pass: collect all concepts and their flow indices
    for inference in nci_data:
        _collect_concept_to_infer(inference, concepts, inferred_concepts)
        _collect_function_concept(inference, function_concepts)
        _collect_value_concepts(inference, concepts)
        _collect_other_concepts(inference, concepts, inferred_concepts)
    
    # Second pass: build concept repo entries for VALUE concepts
    concept_repo = []
    for name, data in concepts.items():
        entry = _build_value_concept_entry(name, data, inferred_concepts)
        concept_repo.append(entry)
    
    # Third pass: build concept repo entries for FUNCTION concepts
    for nc_main, data in function_concepts.items():
        entry = _build_function_concept_entry(nc_main, data)
        concept_repo.append(entry)
    
    # Sort by first flow_index
    concept_repo.sort(key=_flow_sort_key)
    
    return concept_repo


def _collect_concept_to_infer(inference: dict, concepts: dict, inferred_concepts: set):
    """Collect concept_to_infer from inference"""
    cti = inference.get("concept_to_infer", {})
    if cti and cti.get("concept_name"):
        name = cti["concept_name"]
        concept_type = cti.get("concept_type", "object")
        attached_comments = cti.get("attached_comments", [])
        flow_index = cti.get("flow_index")
        
        # Track that this concept is PRODUCED by an operation (not ground)
        inference_marker = cti.get("inference_marker", "")
        if inference_marker != ":>:":
            inferred_concepts.add(name)
        
        if name not in concepts:
            concepts[name] = {
                "concept_name": name,
                "concept_type": concept_type,
                "flow_indices": [],
                "attached_comments": attached_comments,
                "is_final": inference_marker == ":<:",
                "is_user_input": inference_marker == ":>:",
            }
        if flow_index:
            concepts[name]["flow_indices"].append(flow_index)
        if len(attached_comments) > len(concepts[name].get("attached_comments", [])):
            concepts[name]["attached_comments"] = attached_comments


def _collect_function_concept(inference: dict, function_concepts: dict):
    """Collect function_concept from inference"""
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


def _collect_value_concepts(inference: dict, concepts: dict):
    """Collect value_concepts from inference"""
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


def _collect_other_concepts(inference: dict, concepts: dict, inferred_concepts: set):
    """Collect other_concepts (context concepts like <*) from inference"""
    for oc in inference.get("other_concepts", []):
        if oc.get("concept_name"):
            name = oc["concept_name"]
            concept_type = oc.get("concept_type", "object")
            attached_comments = oc.get("attached_comments", [])
            flow_index = oc.get("flow_index")
            
            # Context concepts are NOT ground - they're derived from loop iteration
            inferred_concepts.add(name)
            
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


def _build_value_concept_entry(name: str, data: dict, inferred_concepts: set) -> dict:
    """Build a concept repo entry for a value concept"""
    attached_comments = data.get("attached_comments", [])
    concept_type = data.get("concept_type", "object")
    
    # Extract annotations
    axes_str = get_annotation_value(attached_comments, "ref_axes")
    element_type = get_annotation_value(attached_comments, "ref_element")
    shape_str = get_annotation_value(attached_comments, "ref_shape")
    file_location = extract_file_location(attached_comments)
    is_invariant_str = get_annotation_value(attached_comments, "is_invariant")
    
    # Determine if ground
    is_inferred = name in inferred_concepts
    is_user_input = data.get("is_user_input", False)
    has_ground_annotations = is_ground_concept(data, attached_comments)
    is_ground = (not is_inferred) or is_user_input or has_ground_annotations
    is_invariant = is_invariant_str and is_invariant_str.lower() == "true"
    
    # Build reference_data for ground concepts
    reference_data = None
    literal_value_annotation = get_annotation_value(attached_comments, "literal_value")
    if is_ground:
        if file_location:
            reference_data = [f"%{{file_location}}({file_location})"]
        elif literal_value_annotation:
            lv = literal_value_annotation.strip('"\'')
            reference_data = [lv]
        elif is_literal_concept(name):
            literal_value = extract_literal_value(name)
            if literal_value:
                reference_data = [literal_value]
    
    # Parse axis names
    axis_names = parse_axes(axes_str)
    primary_axis_name = axis_names[0] if axis_names else "_none_axis"
    
    return {
        "id": concept_name_to_id(name),
        "concept_name": format_concept_name(name, concept_type),
        "type": extract_concept_type_marker(concept_type),
        "flow_indices": sorted(list(set(data["flow_indices"]))),
        "description": None,
        "is_ground_concept": is_ground,
        "is_final_concept": data.get("is_final", False),
        "is_invariant": is_invariant,
        "reference_data": reference_data,
        "axis_name": primary_axis_name,
        "reference_axis_names": axis_names,
        "reference_element_type": element_type,
        "natural_name": name,
    }


def _build_function_concept_entry(nc_main: str, data: dict) -> dict:
    """Build a concept repo entry for a function concept"""
    attached_comments = data.get("attached_comments", [])
    operator_type = data.get("operator_type")
    
    # Strip the <= marker
    concept_name = re.sub(r"^<=\s*", "", nc_main)
    
    # Determine function concept type marker
    is_imperative = bool(re.match(r'^:[:><]?:', concept_name))
    
    if (")<{" in concept_name) or ("<{" in concept_name and "}>" in concept_name):
        func_type_marker = "<{}>"
        element_type = "paradigm"
    elif is_imperative and ")<{" not in concept_name:
        func_type_marker = "({})"
        element_type = "paradigm"
    else:
        func_type_marker = "({})"
        element_type = "operator"
    
    # Generate natural name
    natural_name = concept_name
    name_match = re.search(r':[:><]?:\(([^)]+)\)', concept_name)
    if name_match:
        natural_name = name_match.group(1)
    else:
        name_match = re.search(r':[:><]?:\(([^)]+)\)<\{', concept_name)
        if not name_match:
            name_match = re.search(r"::<\{([^}]+)\}>", concept_name)
        if name_match:
            natural_name = name_match.group(1)
    
    # Generate unique ID
    func_id = "fc-" + re.sub(r"[^a-z0-9]+", "-", natural_name.lower()).strip("-")[:50]
    
    # Build reference field
    reference_data = None
    if element_type == "paradigm":
        v_input_provision = get_annotation_value(attached_comments, "v_input_provision")
        
        if v_input_provision:
            if v_input_provision.endswith(".md"):
                norm = "prompt_location"
            elif v_input_provision.endswith(".py"):
                norm = "script_location"
            else:
                norm = "file_location"
            
            hex_id = ''.join(random.choices('0123456789abcdef', k=3))
            reference_data = [f"%{{{norm}}}{hex_id}({v_input_provision})"]
        else:
            reference_data = ["%{dummy}(_)"]
    else:
        reference_data = ["%{dummy}(_)"]
    
    return {
        "id": func_id,
        "concept_name": concept_name,
        "type": func_type_marker,
        "flow_indices": sorted(list(set(data["flow_indices"]))),
        "description": natural_name,
        "is_ground_concept": True,
        "is_final_concept": False,
        "reference_data": reference_data,
        "reference_axis_names": ["_none_axis"],
        "reference_element_type": element_type,
        "natural_name": natural_name,
    }


def _flow_sort_key(x: dict) -> list:
    """Sort key for flow indices"""
    if not x["flow_indices"]:
        return [999]
    idx = x["flow_indices"][0]
    return [int(p) for p in idx.split(".")]

