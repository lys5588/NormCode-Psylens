"""
Tools API - List available deployment tools, inspect configuration, and test them.
"""

import logging
import time
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from service.config import get_config, get_available_llm_models, SETTINGS_PATH, SERVER_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


def _tool_module_available(module_name: str) -> bool:
    """Check if a tool's Python module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _get_settings() -> dict:
    """Load settings.yaml content (with API keys masked)."""
    if not SETTINGS_PATH or not SETTINGS_PATH.exists():
        return {}
    try:
        import yaml
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f) or {}
        masked = {}
        for k, v in settings.items():
            if isinstance(v, dict):
                masked[k] = {
                    ek: (ev[:8] + "..." if isinstance(ev, str) and len(ev) > 12 else ev)
                    for ek, ev in v.items()
                }
            else:
                masked[k] = v
        return masked
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}")
        return {}


TOOL_DEFINITIONS = [
    {
        "id": "llm",
        "name": "Language Model",
        "description": "LLM text generation via OpenAI-compatible API. Supports multiple providers and models.",
        "module": "tools.llm_tool",
        "class": "DeploymentLLMTool",
        "category": "core",
        "configurable": True,
        "testable": True,
    },
    {
        "id": "file_system",
        "name": "File System",
        "description": "Read/write/delete files within a sandboxed base directory with workspace isolation.",
        "module": "tools.file_system_tool",
        "class": "DeploymentFileSystemTool",
        "category": "core",
        "configurable": True,
        "testable": True,
    },
    {
        "id": "python_interpreter",
        "name": "Python Interpreter",
        "description": "Execute Python scripts with body injection and configurable package pre-imports.",
        "module": "tools.python_interpreter_tool",
        "class": "DeploymentPythonInterpreterTool",
        "category": "core",
        "configurable": True,
        "testable": True,
    },
    {
        "id": "gim",
        "name": "Generative Image Model",
        "description": "Text-to-image generation via Dashscope or compatible APIs.",
        "module": "tools.gim_tool",
        "class": "DeploymentGimTool",
        "category": "media",
        "configurable": True,
        "testable": True,
    },
    {
        "id": "prompt",
        "name": "Prompt Manager",
        "description": "Load, cache, and render prompt templates with variable substitution.",
        "module": "tools.prompt_tool",
        "class": "DeploymentPromptTool",
        "category": "core",
        "configurable": False,
        "testable": False,
    },
    {
        "id": "formatter",
        "name": "Formatter",
        "description": "JSON parsing, template substitution, data wrapping, and code extraction.",
        "module": "tools.formatter_tool",
        "class": "DeploymentFormatterTool",
        "category": "utility",
        "configurable": False,
        "testable": False,
    },
    {
        "id": "composition",
        "name": "Composition Engine",
        "description": "Multi-step function composition with context passing and conditional execution.",
        "module": "tools.composition_tool",
        "class": "DeploymentCompositionTool",
        "category": "core",
        "configurable": False,
        "testable": False,
    },
    {
        "id": "user_input",
        "name": "User Input",
        "description": "Human-in-the-loop input via CLI or API with pending request queue.",
        "module": "tools.user_input_tool",
        "class": "DeploymentUserInputTool",
        "category": "interaction",
        "configurable": True,
        "testable": False,
    },
]


@router.get("")
async def list_tools():
    """List all available deployment tools with their status and configuration."""
    settings = _get_settings()
    llm_models = get_available_llm_models()
    cfg = get_config()

    tools = []
    for defn in TOOL_DEFINITIONS:
        available = _tool_module_available(defn["module"])

        config: Dict[str, Any] = {}
        if defn["id"] == "llm":
            config = {
                "models": llm_models,
                "settings_path": str(SETTINGS_PATH) if SETTINGS_PATH and SETTINGS_PATH.exists() else None,
                "base_url": settings.get("BASE_URL"),
            }
        elif defn["id"] == "file_system":
            config = {"base_dir": str(cfg.plans_dir.parent)}
        elif defn["id"] == "python_interpreter":
            config = {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "python_path": sys.executable,
            }
        elif defn["id"] == "gim":
            config = {
                "default_model": "z-image-turbo",
                "default_size": "1024*1024",
                "api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            }
        elif defn["id"] == "user_input":
            config = {"modes": ["blocking", "async", "disabled"]}

        tools.append({
            **{k: v for k, v in defn.items() if k != "module"},
            "available": available,
            "config": config,
        })

    return {"tools": tools}


# ---------------------------------------------------------------------------
# Test endpoints
# ---------------------------------------------------------------------------

class LLMTestRequest(BaseModel):
    model: str = "demo"
    prompt: str = "Say hello in one sentence."
    temperature: float = 0.0
    max_tokens: Optional[int] = 100


@router.post("/llm/test")
async def test_llm(req: LLMTestRequest):
    """Test the LLM tool with a prompt."""
    try:
        from tools.llm_tool import DeploymentLLMTool

        settings_path = str(SETTINGS_PATH) if SETTINGS_PATH and SETTINGS_PATH.exists() else None
        tool = DeploymentLLMTool(
            model_name=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            settings_path=settings_path,
        )

        start = time.time()
        response = tool.generate(req.prompt)
        duration_ms = int((time.time() - start) * 1000)

        return {
            "status": "success",
            "response": response,
            "model": req.model,
            "is_mock": tool.is_mock_mode,
            "duration_ms": duration_ms,
            "stats": tool.get_stats(),
        }
    except Exception as e:
        logger.exception("LLM test failed")
        return {"status": "error", "error": str(e)}


class PythonTestRequest(BaseModel):
    code: str = "result = 2 + 2"
    packages: list[str] = []


@router.post("/python/test")
async def test_python(req: PythonTestRequest):
    """Test the Python interpreter tool."""
    try:
        from tools.python_interpreter_tool import DeploymentPythonInterpreterTool

        tool = DeploymentPythonInterpreterTool(
            packages=req.packages if req.packages else None,
            timeout=10,
        )

        start = time.time()
        result = tool.execute(req.code, {})
        duration_ms = int((time.time() - start) * 1000)

        return {
            "status": "success",
            "result": str(result),
            "duration_ms": duration_ms,
            "stats": tool.get_stats(),
        }
    except Exception as e:
        logger.exception("Python test failed")
        return {"status": "error", "error": str(e)}


class FileSystemTestRequest(BaseModel):
    operation: str = "list"
    path: str = "."


@router.post("/filesystem/test")
async def test_filesystem(req: FileSystemTestRequest):
    """Test the file system tool."""
    try:
        from tools.file_system_tool import DeploymentFileSystemTool

        cfg = get_config()
        tool = DeploymentFileSystemTool(base_dir=str(cfg.plans_dir))

        start = time.time()

        if req.operation == "list":
            result = tool.list_dir(req.path)
        elif req.operation == "read":
            result = tool.read(req.path)
        elif req.operation == "exists":
            result = {"exists": tool.exists(req.path)}
        else:
            return {"status": "error", "error": f"Unknown operation: {req.operation}"}

        duration_ms = int((time.time() - start) * 1000)

        return {
            "status": "success",
            "result": result,
            "operation": req.operation,
            "duration_ms": duration_ms,
        }
    except Exception as e:
        logger.exception("Filesystem test failed")
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Python package management endpoints
# ---------------------------------------------------------------------------

@router.get("/python/packages")
async def list_python_packages():
    """List all installed pip packages for the current Python interpreter."""
    import subprocess, json as _json
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return {"status": "error", "error": proc.stderr.strip() or "pip list failed", "packages": []}
        packages = _json.loads(proc.stdout) if proc.stdout.strip() else []
        return {"status": "success", "packages": packages, "python_path": sys.executable}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "pip list timed out", "packages": []}
    except Exception as e:
        logger.exception("Failed to list packages")
        return {"status": "error", "error": str(e), "packages": []}


class PackageInstallRequest(BaseModel):
    packages: list[str]


@router.post("/python/packages/install")
async def install_python_packages(req: PackageInstallRequest):
    """Install pip packages into the current Python environment."""
    import subprocess
    if not req.packages:
        return {"status": "error", "error": "No packages specified", "installed": [], "failed": []}
    installed = []
    failed = []
    for pkg in req.packages:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode == 0:
                installed.append(pkg)
            else:
                failed.append({"package": pkg, "error": proc.stderr.strip()})
        except subprocess.TimeoutExpired:
            failed.append({"package": pkg, "error": "Installation timed out"})
        except Exception as e:
            failed.append({"package": pkg, "error": str(e)})
    return {
        "status": "success" if not failed else ("partial" if installed else "error"),
        "installed": installed,
        "failed": failed,
        "message": f"Installed {len(installed)} package(s)" + (f", {len(failed)} failed" if failed else ""),
    }


class PackageUninstallRequest(BaseModel):
    packages: list[str]


@router.post("/python/packages/uninstall")
async def uninstall_python_packages(req: PackageUninstallRequest):
    """Uninstall pip packages from the current Python environment."""
    import subprocess
    if not req.packages:
        return {"status": "error", "error": "No packages specified"}
    removed = []
    failed = []
    for pkg in req.packages:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", pkg],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                removed.append(pkg)
            else:
                failed.append({"package": pkg, "error": proc.stderr.strip()})
        except Exception as e:
            failed.append({"package": pkg, "error": str(e)})
    return {
        "status": "success" if not failed else ("partial" if removed else "error"),
        "removed": removed,
        "failed": failed,
        "message": f"Removed {len(removed)} package(s)" + (f", {len(failed)} failed" if failed else ""),
    }


class GIMTestRequest(BaseModel):
    prompt: str = "A simple blue square"
    mock_mode: bool = True


@router.post("/gim/test")
async def test_gim(req: GIMTestRequest):
    """Test the GIM (image generation) tool."""
    try:
        from tools.gim_tool import DeploymentGimTool
        from tools.file_system_tool import DeploymentFileSystemTool

        cfg = get_config()
        fs = DeploymentFileSystemTool(base_dir=str(cfg.runs_dir))
        tool = DeploymentGimTool(
            file_tool=fs,
            mock_mode=req.mock_mode,
            settings_path=str(SETTINGS_PATH) if SETTINGS_PATH and SETTINGS_PATH.exists() else None,
        )

        start = time.time()
        gen_result = tool.generate(req.prompt)
        duration_ms = int((time.time() - start) * 1000)

        return {
            "status": "success",
            "result": gen_result.to_dict() if hasattr(gen_result, "to_dict") else str(gen_result),
            "is_mock": gen_result.is_mock if hasattr(gen_result, "is_mock") else req.mock_mode,
            "duration_ms": duration_ms,
        }
    except Exception as e:
        logger.exception("GIM test failed")
        return {"status": "error", "error": str(e)}
