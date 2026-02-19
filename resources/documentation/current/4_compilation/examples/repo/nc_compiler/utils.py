"""
Common Utilities for NormCode Parsing

Low-level parsing helpers used across modules.
"""

import re
import ast
from typing import Any


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


def parse_axes(axes_str: str) -> list:
    """Parse axes string like '[_none_axis]' or '[date, signal]'"""
    if not axes_str:
        return ["_none_axis"]
    # Remove brackets and split
    axes_str = axes_str.strip("[]")
    axes = [a.strip() for a in axes_str.split(",")]
    return axes if axes else ["_none_axis"]


def parse_axis_list(value_str: str) -> list:
    """
    Parse axis list from annotation value, handling both quoted and unquoted forms.
    
    Handles:
        - "[[section]]" -> [["section"]]
        - "[["section"]]" -> [["section"]]
        - "[[section], [date]]" -> [["section"], ["date"]]
        - "[section, date]" -> ["section", "date"]
        - "section" -> ["section"]
    
    Returns a list (possibly nested) of axis names as strings.
    """
    value_str = value_str.strip()
    if not value_str:
        return ["_none_axis"]
    
    # First, try parsing as a Python literal (handles quoted forms)
    try:
        parsed = ast.literal_eval(value_str)
        if isinstance(parsed, list):
            return parsed
        else:
            return [str(parsed)]
    except (ValueError, SyntaxError):
        pass
    
    # Handle unquoted nested lists like [[section], [date]] or [[section]]
    if value_str.startswith("[["):
        # Parse nested brackets manually
        axis_groups = []
        current = ""
        depth = 0
        for char in value_str:
            if char == '[':
                depth += 1
                if depth == 2:
                    current = ""
                elif depth > 2:
                    current += char
            elif char == ']':
                depth -= 1
                if depth == 1:
                    # End of inner list
                    if current.strip():
                        inner_axes = [a.strip().strip('"\'') for a in current.split(',') if a.strip()]
                        axis_groups.append(inner_axes)
                elif depth >= 2:
                    current += char
            elif depth >= 2:
                current += char
        return axis_groups if axis_groups else [["_none_axis"]]
    
    # Handle single list like [section, date] or [section]
    elif value_str.startswith("["):
        inner = value_str.strip("[]")
        axes = [a.strip().strip('"\'') for a in inner.split(',') if a.strip()]
        return axes if axes else ["_none_axis"]
    
    # Single value without brackets
    else:
        return [value_str.strip().strip('"\'')]


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

