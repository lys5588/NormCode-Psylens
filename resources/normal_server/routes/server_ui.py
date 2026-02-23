"""
NormCode Server UI

Unified web dashboard for the NormCode Deployment Server.
Combines monitoring, plan management, and run control.
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

# Get the path to the static HTML file
STATIC_DIR = Path(__file__).parent.parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


@router.get("/dashboard")
async def server_dashboard():
    """Serve the unified NormCode Server dashboard."""
    return FileResponse(INDEX_HTML)


@router.get("/server/ui")
async def server_ui_redirect():
    """Redirect old /server/ui path to /dashboard for backwards compatibility."""
    return RedirectResponse(url="/dashboard")
