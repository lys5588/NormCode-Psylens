"""
Inference Repository Builder

Builds inference_repo.json from NCI data.
"""

import re

from .annotations import get_sequence_type
from .concepts import format_concept_name, extract_operator_marker, infer_sequence_type_from_nc_main
from .working_interp import build_working_interpretation


# Sequence type mapping
SEQUENCE_MAPPING = {
    "imperative": "imperative_in_composition",
    "judgement": "judgement_in_composition",
    "assigning": "assigning",
    "grouping": "grouping",
    "timing": "timing",
    "looping": "looping",
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
            nc_main = func_concept.get("nc_main", "")
            sequence_type = infer_sequence_type_from_nc_main(nc_main, func_concept)
        
        if not sequence_type:
            continue
        
        # Build inference entry
        entry = _build_inference_entry(
            cti, func_concept, value_concepts, other_concepts, sequence_type, inference
        )
        inference_repo.append(entry)
        
        # Process nested operators
        for oc in other_concepts:
            if oc.get("inference_marker") == "<=":
                nested_inf = _build_nested_operator_inference(oc)
                if nested_inf:
                    inference_repo.append(nested_inf)
    
    # Sort by flow_index
    inference_repo.sort(key=_flow_index_sort_key)
    
    return inference_repo


def _build_inference_entry(
    cti: dict,
    func_concept: dict,
    value_concepts: list,
    other_concepts: list,
    sequence_type: str,
    inference: dict,
) -> dict:
    """Build a single inference entry"""
    cti_name = cti.get("concept_name")
    cti_type = cti.get("concept_type", "object")
    cti_nc_main = cti.get("nc_main", "")
    
    # Build concept_to_infer name
    if cti_type in ["imperative", "judgement", "operator"]:
        concept_to_infer = re.sub(r"^<=\s*", "", cti_nc_main) if cti_nc_main else None
    else:
        concept_to_infer = format_concept_name(cti_name, cti_type) if cti_name else None
    
    # Handle null concept_to_infer
    if concept_to_infer is None:
        concept_to_infer = _derive_concept_to_infer(func_concept, sequence_type)
    
    # Build function_concept string
    func_nc_main = func_concept.get("nc_main", "")
    func_concept_name = re.sub(r"^<=\s*", "", func_nc_main)
    
    # Build value_concepts list
    vc_list = [
        format_concept_name(vc.get("concept_name"), vc.get("concept_type", "object"))
        for vc in value_concepts
        if vc.get("concept_name")
    ]
    
    # Build context_concepts list
    ctx_list = [
        format_concept_name(oc.get("concept_name"), oc.get("concept_type", "object"))
        for oc in other_concepts
        if oc.get("inference_marker") == "<*" and oc.get("concept_name")
    ]
    
    # For timing sequences, add context to value_concepts
    if sequence_type == "timing" and ctx_list:
        vc_list.extend(ctx_list)
    
    # Build working_interpretation
    wi = build_working_interpretation(inference, sequence_type)
    
    # If explicit value_order, use only those concepts
    if wi.get("value_order"):
        explicit_vc = list(wi["value_order"].keys())
        if explicit_vc:
            vc_list = explicit_vc
    
    cti_flow_index = cti.get("flow_index", func_concept.get("flow_index", ""))
    
    return {
        "flow_info": {"flow_index": cti_flow_index},
        "inference_sequence": SEQUENCE_MAPPING.get(sequence_type, sequence_type),
        "concept_to_infer": concept_to_infer,
        "function_concept": func_concept_name,
        "value_concepts": vc_list,
        "context_concepts": ctx_list,
        "working_interpretation": wi,
    }


def _derive_concept_to_infer(func_concept: dict, sequence_type: str) -> str | None:
    """Derive concept_to_infer when it's null"""
    func_nc_main = func_concept.get("nc_main", "")
    
    if sequence_type == "assigning":
        source_match = re.search(r"%>\(\{([^}]+)\}\)", func_nc_main)
        source_match_list = re.search(r"%>\[\{([^}]+)\}", func_nc_main)
        if source_match:
            return f"{{{source_match.group(1)}}}"
        elif source_match_list:
            return f"{{{source_match_list.group(1)}}}"
        else:
            flow_idx = func_concept.get("flow_index", "unknown")
            return f"{{assigning_{flow_idx.replace('.', '_')}}}"
    
    elif sequence_type == "timing":
        return re.sub(r"^<=\s*", "", func_nc_main)
    
    return None


def _build_nested_operator_inference(oc: dict) -> dict | None:
    """Build an inference entry from a nested operator in other_concepts"""
    nc_main = oc.get("nc_main", "")
    flow_index = oc.get("flow_index", "")
    
    sequence_type = infer_sequence_type_from_nc_main(nc_main, oc)
    if not sequence_type:
        return None
    
    func_concept_name = re.sub(r"^<=\s*", "", nc_main)
    
    # Derive concept_to_infer
    concept_to_infer = None
    if sequence_type == "assigning":
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
    
    # Build working_interpretation
    wi = {
        "workspace": {},
        "flow_info": {"flow_index": flow_index}
    }
    
    if sequence_type == "assigning":
        wi["syntax"] = _build_nested_assigning_syntax(nc_main, oc)
    
    return {
        "flow_info": {"flow_index": flow_index},
        "inference_sequence": SEQUENCE_MAPPING.get(sequence_type, sequence_type),
        "concept_to_infer": concept_to_infer,
        "function_concept": func_concept_name,
        "value_concepts": [],
        "context_concepts": [],
        "working_interpretation": wi,
    }


def _build_nested_assigning_syntax(nc_main: str, oc: dict) -> dict:
    """Build syntax for nested assigning operator"""
    operator_type = oc.get("operator_type", "specification")
    marker = extract_operator_marker(operator_type)
    
    if marker == "+":
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
            "marker": marker,
            "assign_source": assign_source,
            "assign_destination": assign_destination,
            "by_axes": by_axes,
        }
    else:
        assign_source = None
        source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
        if source_match:
            assign_source = f"{{{source_match.group(1)}}}"
        
        return {
            "marker": marker,
            "assign_source": assign_source,
        }


def _flow_index_sort_key(item: dict) -> list:
    """Sort key for flow indices"""
    idx = item.get("flow_info", {}).get("flow_index", "999")
    parts = idx.split(".")
    return [int(p) for p in parts]

