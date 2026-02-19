"""
Parser Script: .pf.ncd → .pf.nci.json

A parser that converts Post-Formalized NormCode (.pf.ncd)
to NormCode Inference format (.nci.json) for activation.

Version: v291 (2026-01-29)
Uses: nc_compiler package

Usage:
    python parse_to_nci.py <path/to/file.pf.ncd>
"""

import sys
from pathlib import Path

# Add script directory to path so nc_compiler can be found when run from any directory
_script_dir = Path(__file__).parent.resolve()
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from nc_compiler import parse_pf_ncd_to_nci


def main(input_1: dict = None, input_2: str = None, **kwargs) -> dict:
    """
    Paradigm-compatible entry point.
    
    Args:
        input_1: {pf ncd file written} - dict with 'status' and 'path' keys
        input_2: {project dir} - string path to project directory
    
    Returns:
        dict: {"status": "success/error", "path": "path to nci.json"}
    """
    try:
        if isinstance(input_1, dict):
            pf_ncd_path = input_1.get('path')
        else:
            pf_ncd_path = str(input_1) if input_1 else None
        
        if not pf_ncd_path:
            return {"status": "error", "message": "No pf.ncd path provided"}
        
        output_path = parse_pf_ncd_to_nci(pf_ncd_path)
        
        return {"status": "success", "path": str(output_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def cli_main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_to_nci.py <path/to/file.pf.ncd>")
        print("\nThis script parses a Post-Formalized NormCode file and outputs")
        print("a NormCode Inference JSON file for activation.")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    try:
        output_path = parse_pf_ncd_to_nci(input_path)
        print(f"\n[SUCCESS] NCI file created: {output_path}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()

