#!/usr/bin/env python3
"""
NormCode Deployment Server

Minimal standalone FastAPI server for executing NormCode plans.
Independent from Canvas App - can run plans without the UI.

Usage:
    python server.py
    python server.py --port 9000
    python server.py --plans-dir ./my_plans
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Server directory (where this file is located)
SERVER_DIR = Path(__file__).resolve().parent

# Detect if running from built package or source
# Built package has infra/ copied into the server directory
IS_BUILT_PACKAGE = (SERVER_DIR / "infra").exists() and (SERVER_DIR / "tools").exists()

if IS_BUILT_PACKAGE:
    # Built package: all dependencies are in SERVER_DIR
    if str(SERVER_DIR) not in sys.path:
        sys.path.insert(0, str(SERVER_DIR))
else:
    # Running from source: infra/ is at project root (normCode/)
    # SERVER_DIR = canvas_app/normal_server
    # canvas_app_dir = canvas_app/
    # project_root = normCode/ (where infra/ lives)
    PROJECT_ROOT = SERVER_DIR.parent.parent  # Go up TWO levels to project root
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # Also add canvas_app for backend imports
    CANVAS_APP_DIR = SERVER_DIR.parent
    if str(CANVAS_APP_DIR) not in sys.path:
        sys.path.insert(0, str(CANVAS_APP_DIR))

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
    sys.exit(1)

# Import local modules
from version import __version__, SERVER_NAME
from service import get_config, get_available_llm_models, SETTINGS_PATH
from routes import include_all_routes


# ============================================================================
# FastAPI App Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - startup/shutdown."""
    cfg = get_config()
    
    # Startup
    logging.basicConfig(
        level=getattr(logging, cfg.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logging.info("NormCode Deployment Server starting...")
    logging.info(f"  Plans directory: {cfg.plans_dir}")
    logging.info(f"  Runs directory: {cfg.runs_dir}")
    
    # Log LLM settings
    if SETTINGS_PATH and SETTINGS_PATH.exists():
        llm_models = get_available_llm_models()
        model_names = [m["id"] for m in llm_models if not m.get("is_mock")]
        logging.info(f"  LLM settings: {SETTINGS_PATH}")
        logging.info(f"  Available models: {', '.join(model_names) if model_names else 'demo only'}")
    else:
        logging.warning(f"  LLM settings not found: {SETTINGS_PATH}")
        logging.info("  Only demo (mock) mode available")
    
    # Ensure directories exist
    cfg.ensure_directories()
    
    yield
    
    # Shutdown
    logging.info("NormCode Deployment Server shutting down...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title=SERVER_NAME,
    description="Execute NormCode plans via REST API",
    version=__version__,
    lifespan=lifespan
)

# CORS middleware - allows canvas_app to connect from different origin
# This is essential for RemoteProxyExecutor to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Global Error Handlers - ensure JSON responses for all errors
# ============================================================================
# When behind Nginx, unhandled errors can cause HTML responses that break
# JavaScript clients expecting JSON. These handlers ensure consistent JSON.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clear JSON errors for validation failures (e.g. missing file upload)."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in err.get("loc", [])),
                    "message": err.get("msg", "Unknown error"),
                    "type": err.get("type", "unknown"),
                }
                for err in exc.errors()
            ]
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler to prevent HTML error pages."""
    logging.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}",
            "message": str(exc),
        }
    )


# Mount static files for server UI
STATIC_DIR = SERVER_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include all route modules
include_all_routes(app)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="NormCode Deployment Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    
    # Determine default paths
    if IS_BUILT_PACKAGE:
        default_plans_dir = SERVER_DIR / "data" / "plans"
        default_runs_dir = SERVER_DIR / "data" / "runs"
    else:
        default_plans_dir = SERVER_DIR / "data" / "plans"
        default_runs_dir = SERVER_DIR / "data" / "runs"
    
    parser.add_argument("--plans-dir", type=Path, default=default_plans_dir, help="Plans directory")
    parser.add_argument("--runs-dir", type=Path, default=default_runs_dir, help="Runs directory")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variables for config (picked up by ServerConfig)
    os.environ["NORMCODE_HOST"] = args.host
    os.environ["NORMCODE_PORT"] = str(args.port)
    os.environ["NORMCODE_PLANS_DIR"] = str(args.plans_dir.resolve())
    os.environ["NORMCODE_RUNS_DIR"] = str(args.runs_dir.resolve())
    
    print("Starting NormCode Deployment Server...")
    print(f"  API: http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Plans: {args.plans_dir.resolve()}")
    print(f"  Runs: {args.runs_dir.resolve()}")
    
    # Determine the correct module path for uvicorn
    if IS_BUILT_PACKAGE:
        app_path = "server:app"
    else:
        # When running from source, we're in canvas_app/normal_server/
        app_path = "canvas_app.normal_server.server:app"
    
    uvicorn.run(
        app_path,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
