"""
Concept Type Detection and Formatting

Functions for identifying concept types and formatting concept names.
"""

import re
from typing import Any, Dict

from .annotations import get_annotation_value, get_literal_annotation
from .utils import is_literal_concept


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


def is_ground_concept(concept_data: dict, attached_comments: list) -> bool:
    """
    Determine if a concept has explicit ground annotations.
    
    NOTE: This only checks for EXPLICIT ground markers. The main ground determination
    logic is in build_concept_repo() which checks if a concept is inferred (produced
    by an operation). A concept is ground if:
    1. It is NOT produced by any operation, OR
    2. It has :>: marker (user input), OR  
    3. It has one of these explicit annotations
    """
    # Check for explicit %{is_ground}: true annotation
    is_ground_annotation = get_annotation_value(attached_comments, "is_ground")
    if is_ground_annotation and is_ground_annotation.lower() == "true":
        return True
    
    # Check for %{literal_value} annotation (hardcoded values are ground)
    if get_annotation_value(attached_comments, "literal_value"):
        return True
    
    # Check for %{literal<$% ...>}: annotation (literal assignment - the concept receiving
    # a literal value IS a ground concept because its value is hardcoded, not computed)
    _, literal_value = get_literal_annotation(attached_comments)
    if literal_value is not None:
        return True
    
    # Check for /: Ground: comment
    for comment in attached_comments:
        nc_comment = comment.get("nc_comment", "")
        if "/: Ground:" in nc_comment:
            return True
    
    # Check for file_location annotation (explicit input file)
    if get_annotation_value(attached_comments, "file_location"):
        return True
    
    # NOTE: perceptual_sign does NOT indicate ground - it just means file-like data
    # The file could be an input OR an output. Ground is determined by whether
    # the concept is produced by an operation or not.
    
    # Check for literal concepts like {phase_name: "phase_1"}
    concept_name = concept_data.get("concept_name", "")
    if is_literal_concept(concept_name):
        return True
    
    return False


def detect_concept_type(content: str) -> Dict[str, Any]:
    """
    Detect the concept type from content.
    
    Returns:
        Dict with:
            - inference_marker: '<-', '<=', '<*', ':<:', ':>:' or None
            - concept_type: 'object', 'proposition', 'relation', 'subject', 
                           'imperative', 'judgement', 'operator', 'comment', 'informal'
            - operator_type: For operators - 'assigning', 'grouping', 'timing', 'looping'
            - concept_name: Extracted name if applicable
    """
    result = {
        'inference_marker': None,
        'concept_type': None,
        'operator_type': None,
        'concept_name': None,
        'warnings': []
    }
    
    content = content.strip()
    if not content:
        return result
    
    # Extract inference marker first
    inference_markers = [':<:', ':>:', '<=', '<-', '<*']
    remaining = content
    for marker in inference_markers:
        if content.startswith(marker):
            result['inference_marker'] = marker
            remaining = content[len(marker):].strip()
            break
    
    # --- Syntactic Operators ---
    if remaining.startswith('$='):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'identity'
    elif remaining.startswith('$%'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'abstraction'
    elif remaining.startswith('$.'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'specification'
    elif remaining.startswith('$+'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'continuation'
    elif remaining.startswith('$-'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'selection'
    elif remaining.startswith('$::'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'nominalization'
    # Grouping
    elif remaining.startswith('&[{}]') or remaining.startswith('&[#]'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'grouping'
    # Timing
    elif remaining.startswith("@:'") or remaining.startswith('@:!'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'timing_conditional'
    elif remaining.startswith('@.'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'timing_completion'
    elif remaining.startswith('@::'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'timing_action'
    # Looping
    elif remaining.startswith('*.'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'looping'
    
    # --- Semantic Concepts ---
    elif remaining.startswith('::'):
        # Imperative or Judgement
        if re.search(r'::\([^)]*\)\s*<', remaining) or '::<{' in remaining:
            result['concept_type'] = 'judgement'
            match = re.search(r'::\(([^)]*)\)', remaining)
            if not match:
                match = re.search(r'::<\{([^}]+)\}>', remaining)
            if match:
                result['concept_name'] = match.group(1)
        else:
            result['concept_type'] = 'imperative'
            match = re.search(r'::\(([^)]*)\)', remaining)
            if match:
                result['concept_name'] = match.group(1)
    
    # Subject: :Name:
    elif re.match(r'^:[A-Za-z_][A-Za-z0-9_]*:', remaining):
        result['concept_type'] = 'subject'
        match = re.match(r'^:([A-Za-z_][A-Za-z0-9_]*):', remaining)
        if match:
            result['concept_name'] = match.group(1)
    
    # Proposition: <name>
    elif remaining.startswith('<') and not remaining.startswith(('<$', '<:', '<=', '<-', '<*')):
        if '>' in remaining:
            result['concept_type'] = 'proposition'
            match = re.match(r'^<([^>]+)>', remaining)
            if match:
                result['concept_name'] = match.group(1)
        else:
            result['concept_type'] = 'informal'
            result['warnings'].append('Unclosed proposition marker <')
    
    # Relation: [name]
    elif remaining.startswith('['):
        if ']' in remaining:
            result['concept_type'] = 'relation'
            match = re.match(r'^\[([^\]]+)\]', remaining)
            if match:
                result['concept_name'] = match.group(1)
        else:
            result['concept_type'] = 'informal'
            result['warnings'].append('Unclosed relation marker [')
    
    # Object: {name}
    elif remaining.startswith('{'):
        if '}' in remaining:
            result['concept_type'] = 'object'
            match = re.match(r'^\{([^}]+)\}', remaining)
            if match:
                result['concept_name'] = match.group(1)
        else:
            result['concept_type'] = 'informal'
            result['warnings'].append('Unclosed object marker {')
    
    # Comment markers
    elif remaining.startswith('/:') or remaining.startswith('?:') or remaining.startswith('...:'):
        result['concept_type'] = 'comment'
    elif remaining.startswith('%{') or remaining.startswith('?{'):
        result['concept_type'] = 'comment'
    
    # Inference marker but no recognized concept
    elif result['inference_marker'] and not result['concept_type']:
        result['concept_type'] = 'informal'
        result['warnings'].append(f"Unrecognized concept format after {result['inference_marker']}")
        if remaining:
            result['concept_name'] = remaining.split()[0] if remaining.split() else remaining[:30]
    
    # No inference marker
    elif not result['inference_marker']:
        if content.startswith('/') or content.startswith('?') or content.startswith('%'):
            result['concept_type'] = 'comment'
        else:
            result['concept_type'] = 'informal'
            if content and not content.startswith('|'):
                result['warnings'].append('Line without inference marker or comment prefix')
    
    return result


def infer_sequence_type_from_nc_main(nc_main: str, concept_data: dict) -> str | None:
    """Infer sequence type from nc_main pattern"""
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

