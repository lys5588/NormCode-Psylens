"""
Plans API Routes

Endpoints for plan discovery, deployment, and management.
"""

import json
import logging
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, File

from service import get_config, PlanInfo, discover_plans, get_plan_inputs_outputs, load_plan_graph

router = APIRouter()


async def install_python_requirements(requirements_file: Path, plan_id: str) -> Dict[str, Any]:
    """
    Install Python requirements from a requirements file.
    
    Args:
        requirements_file: Path to requirements.txt file
        plan_id: Plan ID for logging
        
    Returns:
        Dict with installation status and details
    """
    logging.info(f"Installing Python requirements for plan '{plan_id}' from {requirements_file}")
    
    try:
        # Read requirements to log what we're installing
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements_content = f.read()
        
        # Filter out comments and empty lines for display
        packages = [
            line.strip() for line in requirements_content.splitlines()
            if line.strip() and not line.strip().startswith('#')
        ]
        
        if not packages:
            return {
                "status": "skipped",
                "message": "No packages to install (file empty or only comments)",
                "file": str(requirements_file),
            }
        
        logging.info(f"Installing packages: {packages}")
        
        # Run pip install
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logging.info(f"Successfully installed requirements for plan '{plan_id}'")
            return {
                "status": "success",
                "packages": packages,
                "file": str(requirements_file),
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            logging.error(f"Failed to install requirements for plan '{plan_id}': {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "packages": packages,
                "file": str(requirements_file),
            }
            
    except subprocess.TimeoutExpired:
        logging.error(f"Timeout installing requirements for plan '{plan_id}'")
        return {
            "status": "error",
            "message": "Installation timed out after 5 minutes",
            "file": str(requirements_file),
        }
    except Exception as e:
        logging.error(f"Error installing requirements for plan '{plan_id}': {e}")
        return {
            "status": "error",
            "message": str(e),
            "file": str(requirements_file),
        }


@router.get("", response_model=List[PlanInfo])
async def list_plans():
    """List all available plans."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    result = []
    
    for plan_id, plan_config in plans.items():
        inputs, outputs = get_plan_inputs_outputs(plan_config)
        
        result.append(PlanInfo(
            id=plan_id,
            name=plan_config.name,
            description=plan_config.description,
            inputs=inputs,
            outputs=outputs
        ))
    
    return result


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    """Get details for a specific plan."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    
    return {
        "id": plan_id,
        "name": plan_config.name,
        "description": plan_config.description,
        "config_path": plan_config.config_path.as_posix(),
        "concept_repo": plan_config.concept_repo_path.as_posix() if plan_config.concept_repo_path else None,
        "inference_repo": plan_config.inference_repo_path.as_posix() if plan_config.inference_repo_path else None,
        "llm_model": plan_config.llm_model,
        "max_cycles": plan_config.max_cycles
    }


@router.get("/{plan_id}/graph")
async def get_plan_graph(plan_id: str):
    """
    Get the full graph data (concepts + inferences) for a plan.
    
    This allows the Canvas App to load and render a remote plan's graph
    without needing local files.
    """
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    return load_plan_graph(plan_config)


@router.get("/{plan_id}/files/{file_path:path}")
async def get_plan_file(plan_id: str, file_path: str):
    """
    Get a specific file from a plan's directory.
    
    Useful for fetching prompts, paradigms, or other provision files.
    Only allows access to files within the plan directory (security).
    """
    import base64
    
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    plan_dir = plan_config.project_dir
    
    # Resolve the requested file path
    requested_path = (plan_dir / file_path).resolve()
    
    # Security: ensure the path is within the plan directory
    try:
        requested_path.relative_to(plan_dir.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied: path outside plan directory")
    
    if not requested_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")
    
    if not requested_path.is_file():
        raise HTTPException(400, "Path is not a file")
    
    # Read and return content
    try:
        with open(requested_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "path": file_path,
            "content": content,
            "size": requested_path.stat().st_size,
        }
    except UnicodeDecodeError:
        # Binary file - return base64 encoded
        with open(requested_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('ascii')
        return {
            "path": file_path,
            "content": content,
            "encoding": "base64",
            "size": requested_path.stat().st_size,
        }


@router.post("/deploy")
async def deploy_plan_from_path(request_data: dict = None):
    """
    Deploy a plan from a local directory path on the server.
    
    Body JSON:
    - path: Local filesystem path to the plan directory
    - plan_id: Optional custom plan ID (defaults to directory name)
    """
    cfg = get_config()
    
    if not request_data or 'path' not in request_data:
        return {
            "status": "info",
            "plans_dir": str(cfg.plans_dir),
            "endpoints": {
                "deploy_from_path": "POST /api/plans/deploy with {'path': '/path/to/plan'}",
                "deploy_zip": "POST /api/plans/deploy-file with file upload",
            },
            "message": "Provide a 'path' field with the local directory path to deploy"
        }
    
    source_path = Path(request_data['path']).resolve()
    
    if not source_path.exists():
        raise HTTPException(404, f"Path not found: {source_path}")
    
    if not source_path.is_dir():
        raise HTTPException(400, f"Path is not a directory: {source_path}")
    
    # Look for manifest or config file
    manifest_path = None
    manifest_data = {}
    
    # Check for manifest.json
    if (source_path / "manifest.json").exists():
        manifest_path = source_path / "manifest.json"
    # Check for .normcode-canvas.json
    else:
        for config_file in source_path.glob("*.normcode-canvas.json"):
            manifest_path = config_file
            break
    
    if manifest_path:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    
    # Determine plan ID
    plan_id = request_data.get('plan_id') or manifest_data.get('name') or manifest_data.get('id') or source_path.name
    
    # Validate required files exist
    has_concepts = (source_path / "concept_repo.json").exists() or any(source_path.glob("*.concept.json"))
    has_inferences = (source_path / "inference_repo.json").exists() or any(source_path.glob("*.inference.json"))
    
    if not has_concepts and not has_inferences and not manifest_path:
        raise HTTPException(400, f"Directory doesn't appear to be a valid NormCode plan. Missing concept/inference repos or manifest.")
    
    # Copy to plans directory
    dest_dir = cfg.plans_dir / plan_id
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    try:
        shutil.copytree(source_path, dest_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', '.venv', 'venv'))
        logging.info(f"Deployed plan '{plan_id}' from {source_path}")
        
        # Install Python requirements if present
        requirements_installed = None
        requirements_file = dest_dir / "python_requirements.txt"
        if not requirements_file.exists():
            # Also check common alternative names
            for alt_name in ["requirements.txt", "python-requirements.txt"]:
                alt_file = dest_dir / alt_name
                if alt_file.exists():
                    requirements_file = alt_file
                    break
        
        if requirements_file.exists():
            requirements_installed = await install_python_requirements(requirements_file, plan_id)
        
        return {
            "status": "deployed",
            "plan_id": plan_id,
            "plan_name": manifest_data.get('name', plan_id),
            "source": str(source_path),
            "destination": str(dest_dir),
            "requirements_installed": requirements_installed,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to copy plan: {e}")


@router.post("/deploy-file")
async def deploy_plan_file(plan: bytes = File(...)):
    """
    Deploy a plan package (zip file) to this server.
    Accepts the zip file as the request body.
    """
    cfg = get_config()
    
    try:
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="normcode_upload_"))
        
        try:
            # Save and extract zip
            zip_path = temp_dir / "upload.zip"
            with open(zip_path, 'wb') as f:
                f.write(plan)
            
            # Extract
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Find manifest.json or .normcode-canvas.json
            manifest_path = None
            plan_dir = None
            
            for item in extract_dir.iterdir():
                if item.is_dir():
                    if (item / "manifest.json").exists():
                        manifest_path = item / "manifest.json"
                        plan_dir = item
                        break
                elif item.name == "manifest.json":
                    manifest_path = item
                    plan_dir = extract_dir
                    break
            
            # Also check for .normcode-canvas.json (with or without prefix)
            # Matches both "xxx.normcode-canvas.json" and "normcode-canvas.json"
            if not manifest_path:
                # First try pattern with prefix
                for config_file in extract_dir.rglob("*.normcode-canvas.json"):
                    manifest_path = config_file
                    plan_dir = config_file.parent
                    break
                
                # Also try exact filename without prefix
                if not manifest_path:
                    for config_file in extract_dir.rglob("normcode-canvas.json"):
                        manifest_path = config_file
                        plan_dir = config_file.parent
                        break
            
            if not manifest_path:
                raise HTTPException(400, "No manifest.json or .normcode-canvas.json found in package")
            
            # Load manifest to get plan ID
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            plan_id = manifest.get('name') or manifest.get('id') or 'unknown'
            
            # Copy to plans directory
            dest_dir = cfg.plans_dir / plan_id
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            
            shutil.copytree(plan_dir, dest_dir)
            
            logging.info(f"Deployed plan '{plan_id}' to {dest_dir}")
            
            # Install Python requirements if present
            requirements_installed = None
            requirements_file = dest_dir / "python_requirements.txt"
            if not requirements_file.exists():
                for alt_name in ["requirements.txt", "python-requirements.txt"]:
                    alt_file = dest_dir / alt_name
                    if alt_file.exists():
                        requirements_file = alt_file
                        break
            
            if requirements_file.exists():
                requirements_installed = await install_python_requirements(requirements_file, plan_id)
            
            return {
                "status": "deployed",
                "plan_id": plan_id,
                "plan_name": manifest.get('name', plan_id),
                "destination": str(dest_dir),
                "requirements_installed": requirements_installed,
            }
            
        finally:
            # Cleanup temp
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Deploy failed: {e}")
        raise HTTPException(500, f"Deploy failed: {e}")


@router.post("/{plan_id}/install-requirements")
async def install_plan_requirements(plan_id: str):
    """
    Install Python requirements for a deployed plan.
    
    Useful for:
    - Retrying failed installations
    - Installing requirements after manual plan updates
    """
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    plan_dir = plan_config.project_dir
    
    # Find requirements file
    requirements_file = None
    for name in ["python_requirements.txt", "requirements.txt", "python-requirements.txt"]:
        candidate = plan_dir / name
        if candidate.exists():
            requirements_file = candidate
            break
    
    if not requirements_file:
        return {
            "status": "skipped",
            "message": "No requirements file found in plan directory",
            "plan_id": plan_id,
            "checked_files": ["python_requirements.txt", "requirements.txt", "python-requirements.txt"],
        }
    
    result = await install_python_requirements(requirements_file, plan_id)
    result["plan_id"] = plan_id
    return result


@router.delete("/{plan_id}")
async def undeploy_plan(plan_id: str):
    """Remove a deployed plan."""
    cfg = get_config()
    
    # First, try to find the plan in discovered plans (plan_id may differ from folder name)
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id in plans:
        # Use the actual project_dir from the plan config
        plan_dir = plans[plan_id].project_dir
    else:
        # Fallback: try using plan_id as folder name directly
        plan_dir = cfg.plans_dir / plan_id
    
    if not plan_dir.exists():
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    try:
        shutil.rmtree(plan_dir)
        logging.info(f"Undeployed plan: {plan_id} (dir: {plan_dir})")
        return {"status": "undeployed", "plan_id": plan_id, "removed_dir": str(plan_dir)}
    except Exception as e:
        raise HTTPException(500, f"Failed to undeploy: {e}")


@router.delete("")
async def clear_all_plans():
    """Remove ALL deployed plans from the server."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    removed = []
    failed = []
    
    for plan_id, plan_config in plans.items():
        try:
            plan_dir = plan_config.project_dir
            if plan_dir.exists():
                shutil.rmtree(plan_dir)
                removed.append(plan_id)
                logging.info(f"Removed plan: {plan_id}")
        except Exception as e:
            failed.append({"plan_id": plan_id, "error": str(e)})
            logging.error(f"Failed to remove plan {plan_id}: {e}")
    
    return {
        "status": "completed",
        "removed_count": len(removed),
        "removed": removed,
        "failed": failed
    }

