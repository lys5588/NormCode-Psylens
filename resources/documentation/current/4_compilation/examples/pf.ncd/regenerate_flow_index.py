"""
Flow Index Regeneration Script

Automatically regenerates flow indices in .pf.ncd files based on hierarchical structure.

Usage:
    python regenerate_flow_index.py <path/to/file.pf.ncd>
    
This script:
1. Parses the .pf.ncd file
2. Identifies inference lines (<- and <=)
3. Assigns flow indices based on indentation hierarchy
4. Writes the updated file

The flow index pattern follows:
- Root level: 1
- Children: 1.1, 1.2, 1.3, ...
- Grandchildren: 1.1.1, 1.1.2, 1.2.1, ...
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


# Patterns for identifying inference lines
INFERENCE_PATTERNS = [
    r'^(\s*)<-\s+',        # Value concept
    r'^(\s*)<=\s+',        # Functional concept
    r'^(\s*)<\*\s+',       # Context concept
]

# Pattern to match existing flow_index
FLOW_INDEX_PATTERN = r'\?\{flow_index\}:\s*[\d.]+'


def count_leading_spaces(line: str) -> int:
    """Count leading spaces in a line."""
    return len(line) - len(line.lstrip())


def is_inference_line(line: str) -> bool:
    """Check if line is an inference line (<-, <=, <*, :<:, :>:)."""
    stripped = line.lstrip()
    # Standard inference markers
    if stripped.startswith('<-') or stripped.startswith('<=') or stripped.startswith('<*'):
        return True
    # Root concept and ground markers
    if stripped.startswith(':<:') or stripped.startswith(':>:'):
        return True
    return False


def is_comment_or_annotation(line: str) -> bool:
    """Check if line is a comment or annotation."""
    stripped = line.lstrip()
    return stripped.startswith('/') or stripped.startswith('|%')


def parse_hierarchy(lines: List[str]) -> List[Tuple[int, int, str]]:
    """
    Parse lines and return hierarchy info.
    
    Returns:
        List of (line_index, depth, line_content)
    """
    hierarchy = []
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        
        if is_inference_line(line):
            depth = count_leading_spaces(line)
            hierarchy.append((i, depth, line))
    
    return hierarchy


def calculate_flow_indices(hierarchy: List[Tuple[int, int, str]], 
                          base_index: str = "1") -> dict:
    """
    Calculate flow indices for each inference line.
    
    Args:
        hierarchy: List of (line_index, depth, line_content)
        base_index: Starting index (default "1")
    
    Returns:
        Dict mapping line_index to flow_index
    """
    if not hierarchy:
        return {}
    
    flow_indices = {}
    
    # Stack to track current index at each depth
    # Format: [(depth, current_count)]
    depth_stack = []
    
    # Find minimum depth (root level)
    min_depth = min(h[1] for h in hierarchy)
    
    for line_idx, depth, line in hierarchy:
        # Normalize depth relative to minimum
        rel_depth = (depth - min_depth) // 4  # Assuming 4-space indentation
        
        # Pop stack until we find parent depth
        while depth_stack and depth_stack[-1][0] >= rel_depth:
            depth_stack.pop()
        
        # Get parent index
        if depth_stack:
            parent_depth, parent_count, parent_index = depth_stack[-1]
            # Increment sibling counter if same depth as last
            if rel_depth == parent_depth:
                depth_stack.pop()
                new_count = parent_count + 1
                new_index = '.'.join(parent_index.split('.')[:-1] + [str(new_count)]) if '.' in parent_index else str(new_count)
            else:
                # New child level
                new_count = 1
                new_index = f"{parent_index}.{new_count}"
        else:
            # Root level
            new_count = 1
            new_index = base_index
        
        depth_stack.append((rel_depth, new_count, new_index))
        flow_indices[line_idx] = new_index
    
    return flow_indices


def calculate_flow_indices_v2(lines: List[str], base_index: str = "1") -> dict:
    """
    Calculate flow indices using indentation-based hierarchy.
    
    NormCode flow index pattern:
    - Root concept: 1
    - Direct children of root: 1.1, 1.2, 1.3, ...
    - Children of 1.1: 1.1.1, 1.1.2, ...
    - Siblings are counted sequentially at each depth
    
    Args:
        lines: All lines of the file
        base_index: Starting index (default "1")
    
    Returns:
        Dict mapping line_index to flow_index
    """
    flow_indices = {}
    
    # Find all inference lines first
    inference_lines = []
    for i, line in enumerate(lines):
        if line.strip() and is_inference_line(line):
            indent = count_leading_spaces(line)
            inference_lines.append((i, indent, line))
    
    if not inference_lines:
        return flow_indices
    
    # Find the minimum indent (root level)
    min_indent = min(il[1] for il in inference_lines)
    
    # Stack: [(indent, flow_index, child_count)]
    # child_count is how many children have been assigned under this node
    stack = []
    
    for line_idx, indent, line in inference_lines:
        if indent == min_indent:
            # Root level - always use base_index
            current_index = base_index
            # Clear stack and start fresh with root
            stack = [(indent, current_index, 0)]
        else:
            # Pop stack until we find a parent (strictly lower indent)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            
            if not stack:
                # Shouldn't happen if min_indent is correct, but fallback
                current_index = base_index
                stack.append((indent, current_index, 0))
            else:
                # Child of the top of stack
                parent_indent, parent_index, child_count = stack[-1]
                child_count += 1
                current_index = f"{parent_index}.{child_count}"
                
                # Update parent's child count
                stack[-1] = (parent_indent, parent_index, child_count)
                
                # Push current as potential parent for deeper children
                stack.append((indent, current_index, 0))
        
        flow_indices[line_idx] = current_index
    
    return flow_indices


def update_line_with_flow_index(line: str, flow_index: str) -> str:
    """
    Update a line with the new flow index.
    
    - If line has existing flow_index, replace it
    - If line has no flow_index but has other annotations, add it
    - If line has no annotations, add the flow_index annotation
    """
    # Check if line already has flow_index
    if '?{flow_index}' in line:
        # Replace existing
        new_line = re.sub(
            r'\?\{flow_index\}:\s*[\d.]+',
            f'?{{flow_index}}: {flow_index}',
            line
        )
        return new_line
    
    # Check if line has inline annotations (|)
    if ' | ' in line:
        # Insert flow_index after the first |
        parts = line.split(' | ', 1)
        return f"{parts[0]} | ?{{flow_index}}: {flow_index} | {parts[1]}"
    
    # No existing annotations - add at end
    line_stripped = line.rstrip()
    return f"{line_stripped} | ?{{flow_index}}: {flow_index}"


def regenerate_flow_indices(file_path: str, base_index: str = "1", 
                           dry_run: bool = False) -> str:
    """
    Regenerate flow indices in a .pf.ncd file.
    
    Args:
        file_path: Path to the .pf.ncd file
        base_index: Starting index (default "1")
        dry_run: If True, return result without writing to file
    
    Returns:
        The updated file content
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Calculate flow indices
    flow_indices = calculate_flow_indices_v2(lines, base_index)
    
    # Update lines with flow indices
    updated_lines = []
    for i, line in enumerate(lines):
        if i in flow_indices:
            updated_line = update_line_with_flow_index(line, flow_indices[i])
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)
    
    result = '\n'.join(updated_lines)
    
    if not dry_run:
        path.write_text(result, encoding='utf-8')
        print(f"[OK] Updated {len(flow_indices)} flow indices in {file_path}")
    
    return result


def main(input_1=None, **kwargs):
    """
    Main function for NormCode orchestrator integration.
    
    Args:
        input_1: Path to the .pf.ncd file
    """
    if input_1 is None:
        return {"status": "error", "message": "No input file provided"}
    
    file_path = input_1 if isinstance(input_1, str) else input_1.get('path', '')
    
    if not file_path:
        return {"status": "error", "message": "Invalid file path"}
    
    try:
        regenerate_flow_indices(file_path)
        return {"status": "success", "file": file_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import io
    # Fix Windows console encoding for Chinese characters
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    if len(sys.argv) < 2:
        print("Usage: python regenerate_flow_index.py <path/to/file.pf.ncd>")
        print("\nOptions:")
        print("  --dry-run    Show changes without modifying file")
        sys.exit(1)
    
    file_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    try:
        result = regenerate_flow_indices(file_path, dry_run=dry_run)
        if dry_run:
            print("=== Dry Run Result ===")
            # Just show count of changes
            lines = result.split('\n')
            flow_count = sum(1 for line in lines if '?{flow_index}' in line)
            print(f"Total lines with flow_index: {flow_count}")
            # Show first few inference lines
            for i, line in enumerate(lines[:100]):
                if '?{flow_index}' in line:
                    print(f"  Line {i+1}: ...{line[-80:]}" if len(line) > 80 else f"  Line {i+1}: {line}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

