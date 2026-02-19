"""
Activation Script: Transform .pf.nci.json → concept_repo.json + inference_repo.json

This script implements Phase 4 (Activation) of the NormCode compilation pipeline.

Version: v291 (2026-01-29)
Uses: nc_compiler package

Usage:
    python activate_nci.py <path/to/file.pf.nci.json>
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add script directory to path so nc_compiler can be found when run from any directory
_script_dir = Path(__file__).parent.resolve()
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from nc_compiler import build_concept_repo, build_inference_repo


def main(input_1: dict = None, input_2=None, input_3: str = None, **kwargs) -> dict:
    """
    Paradigm-compatible entry point.
    
    Args:
        input_1: {nci json} - dict with 'status' and 'path' keys
        input_2: [provisions saved] - list of provision save statuses (not used)
        input_3: {project dir} - string path to project directory
    
    Returns:
        dict: {"status": "success/error", "concept_repo": "path", "inference_repo": "path"}
    """
    try:
        if isinstance(input_1, dict):
            nci_path = Path(input_1.get('path'))
        else:
            nci_path = Path(str(input_1)) if input_1 else None
        
        if not nci_path or not nci_path.exists():
            return {"status": "error", "message": f"NCI file not found: {nci_path}"}
        
        project_dir = nci_path.parent
        repos_dir = project_dir / "repos"
        repos_dir.mkdir(exist_ok=True)
        
        concept_repo_path = repos_dir / "concept_repo.json"
        inference_repo_path = repos_dir / "inference_repo.json"
        
        with open(nci_path, "r", encoding="utf-8") as f:
            nci_data = json.load(f)
        
        concept_repo = build_concept_repo(nci_data)
        inference_repo = build_inference_repo(nci_data)
        
        with open(concept_repo_path, "w", encoding="utf-8") as f:
            json.dump(concept_repo, f, indent=2, ensure_ascii=False)
        
        with open(inference_repo_path, "w", encoding="utf-8") as f:
            json.dump(inference_repo, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "concept_repo": str(concept_repo_path),
            "inference_repo": str(inference_repo_path)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def cli_main():
    """CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        nci_path = Path(sys.argv[1]).resolve()
        base_dir = nci_path.parent
    else:
        base_dir = Path(__file__).parent
        nci_path = base_dir / "_.pf.nci.json"
    
    repos_dir = base_dir / "repos"
    repos_dir.mkdir(exist_ok=True)
    
    concept_repo_path = repos_dir / "concept_repo.json"
    inference_repo_path = repos_dir / "inference_repo.json"
    
    print(f"Loading NCI from: {nci_path}")
    with open(nci_path, "r", encoding="utf-8") as f:
        nci_data = json.load(f)
    
    print(f"Found {len(nci_data)} inferences in NCI")
    
    print("Building concept repository...")
    concept_repo = build_concept_repo(nci_data)
    print(f"  -> {len(concept_repo)} unique concepts")
    
    print("Building inference repository...")
    inference_repo = build_inference_repo(nci_data)
    print(f"  -> {len(inference_repo)} inferences")
    
    print(f"\nWriting concept repo to: {concept_repo_path}")
    with open(concept_repo_path, "w", encoding="utf-8") as f:
        json.dump(concept_repo, f, indent=2, ensure_ascii=False)
    
    print(f"Writing inference repo to: {inference_repo_path}")
    with open(inference_repo_path, "w", encoding="utf-8") as f:
        json.dump(inference_repo, f, indent=2, ensure_ascii=False)
    
    print("\n[OK] Activation complete!")
    
    # Summary
    _print_summary(concept_repo, inference_repo)


def _print_summary(concept_repo: list, inference_repo: list):
    """Print activation summary."""
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
    
    seq_counts = defaultdict(int)
    for inf in inference_repo:
        seq_counts[inf["inference_sequence"]] += 1
    
    print(f"\nInference sequences:")
    for seq, count in sorted(seq_counts.items()):
        print(f"  - {seq}: {count}")
    
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
    cli_main()

