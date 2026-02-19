"""
Annotation Extraction Module

Functions for extracting annotation values from attached comments.
"""

import re
import ast
from typing import Any

from .utils import parse_comment_value, parse_inline_comment


def get_annotation_value(attached_comments: list, key: str) -> str | None:
    """Extract annotation value from attached comments"""
    for comment in attached_comments:
        if comment.get("type") == "comment":
            nc_comment = comment.get("nc_comment", "")
            value = parse_comment_value(nc_comment, key)
            if value:
                return value
    return None


def get_literal_annotation(attached_comments: list, marker: str = None) -> tuple[str | None, Any]:
    """
    Extract literal value from %{literal<$% name>}: value annotations.
    
    Args:
        attached_comments: List of comment objects
        marker: Optional marker to match (e.g., "$%")
    
    Returns:
        Tuple of (concept_name, wrapped_value) or (None, None) if not found
        The value is wrapped in literal notation like %(value)
    """
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


def extract_file_location(attached_comments: list) -> str | None:
    """Extract file_location from annotations"""
    return get_annotation_value(attached_comments, "file_location")

