"""
PPT Client Routes

Serves the PPT generation client UI.
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

# Static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"


@router.get("/")
async def ppt_redirect():
    """Redirect /ppt to /ppt/ui"""
    return RedirectResponse(url="/ppt/ui")


@router.get("/ui")
async def ppt_client_ui():
    """Serve the PPT generation client UI."""
    html_path = STATIC_DIR / "ppt_client.html"
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "PPT client UI not found"}

