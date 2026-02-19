"""
NormCode Compiler Package

Modular components for NormCode compilation pipeline:
- Parsing: .pf.ncd → .nci.json
- Activation: .nci.json → concept_repo.json + inference_repo.json

Version: v291 (2026-01-29)
"""

from .parser import parse_pf_ncd_to_nci, parse_ncdn, to_nci
from .concept_repo import build_concept_repo
from .inference_repo import build_inference_repo

__all__ = [
    'parse_pf_ncd_to_nci',
    'parse_ncdn',
    'to_nci',
    'build_concept_repo',
    'build_inference_repo',
]

