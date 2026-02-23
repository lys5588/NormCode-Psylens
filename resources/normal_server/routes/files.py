"""
Files API Routes

Endpoints for client file access:
- List userbench files
- Download files
- Stream file events (SSE)
- Get file metadata
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class FileInfo(BaseModel):
    """File information."""
    name: str
    path: str
    absolute_path: str
    is_dir: bool
    size: int
    modified: str
    created: str
    content_type: Optional[str] = None
    url: Optional[str] = None


class UserBenchInfo(BaseModel):
    """UserBench summary."""
    userbench_id: str
    workspace_id: str  # Compatibility alias
    plan_id: Optional[str]
    created_at: str
    root_path: str
    outputs_path: str
    file_count: int
    total_size: int
    is_active: bool = False


# Compatibility alias
WorkspaceInfo = UserBenchInfo


class FileEventResponse(BaseModel):
    """File event."""
    event_type: str
    path: str
    absolute_path: str
    timestamp: str
    size: Optional[int] = None
    metadata: dict = {}


# ============================================================================
# UserBench Endpoints
# ============================================================================

@router.get("/userbenches", response_model=List[UserBenchInfo])
async def list_userbenches():
    """
    List all client userbenches.
    
    Returns userbenches sorted by creation time (newest first).
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    benches = manager.list_userbenches()
    
    return [
        UserBenchInfo(
            userbench_id=b.get("userbench_id", b.get("workspace_id", "")),
            workspace_id=b.get("userbench_id", b.get("workspace_id", "")),
            plan_id=b.get("plan_id"),
            created_at=b.get("created_at", ""),
            root_path="",  # Don't expose full path
            outputs_path=f"/api/userbenches/{b.get('userbench_id', b.get('workspace_id', ''))}/files/productions",
            file_count=b.get("file_count", 0),
            total_size=b.get("total_size", 0),
            is_active=b.get("is_active", False),
        )
        for b in benches
    ]


# Compatibility alias
@router.get("/workspaces", response_model=List[UserBenchInfo])
async def list_workspaces():
    """Alias for list_userbenches for compatibility."""
    return await list_userbenches()


@router.get("/userbenches/{userbench_id}", response_model=UserBenchInfo)
async def get_userbench(userbench_id: str):
    """
    Get userbench details.
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    info = bench.get_userbench_info()
    
    return UserBenchInfo(
        userbench_id=info.get("userbench_id", info.get("workspace_id", "")),
        workspace_id=info.get("userbench_id", info.get("workspace_id", "")),
        plan_id=info.get("plan_id"),
        created_at=info["created_at"],
        root_path="",  # Don't expose
        outputs_path=f"/api/userbenches/{userbench_id}/files/productions",
        file_count=info["file_count"],
        total_size=info["total_size"],
        is_active=userbench_id in manager._active_benches,
    )


# Compatibility alias
@router.get("/workspaces/{workspace_id}", response_model=UserBenchInfo)
async def get_workspace(workspace_id: str):
    """Alias for get_userbench for compatibility."""
    return await get_userbench(workspace_id)


@router.get("/userbenches/{userbench_id}/structure")
async def get_userbench_structure(userbench_id: str):
    """
    Get the full userbench structure as a tree.
    
    Returns a hierarchical view of all files in the bench including:
    - productions/ (outputs)
    - provisions/ (prompts, scripts, data)
    - inputs/
    - logs/
    - root files (.ncd, .ncds, inputs.json, etc.)
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    return bench.get_userbench_structure()


# Compatibility alias
@router.get("/workspaces/{workspace_id}/structure")
async def get_workspace_structure(workspace_id: str):
    """Alias for get_userbench_structure for compatibility."""
    return await get_userbench_structure(workspace_id)


@router.delete("/userbenches/{userbench_id}")
async def delete_userbench(userbench_id: str):
    """
    Delete a userbench and all its files.
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    manager.delete_userbench(userbench_id)
    
    return {"status": "deleted", "userbench_id": userbench_id}


# Compatibility alias
@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Alias for delete_userbench for compatibility."""
    return await delete_userbench(workspace_id)


# ============================================================================
# File Listing Endpoints
# ============================================================================

@router.get("/userbenches/{userbench_id}/files", response_model=List[FileInfo])
async def list_userbench_files(
    userbench_id: str,
    category: str = Query("productions", description="Category: productions, provisions, inputs, logs"),
    path: str = Query("", description="Subdirectory path"),
    recursive: bool = Query(False, description="Include subdirectories"),
):
    """
    List files in a userbench.
    
    Default lists the productions directory where plans save outputs.
    
    Categories:
    - productions: Output files generated by the plan
    - provisions: Prompts, scripts, data files
    - inputs: Input configuration files
    - logs: Execution logs
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    files = bench.list_files(path=path, category=category, recursive=recursive)
    
    return [
        FileInfo(
            name=f.name,
            path=f.path,
            absolute_path=f.absolute_path,
            is_dir=f.is_dir,
            size=f.size,
            modified=f.modified,
            created=f.created,
            content_type=f.content_type,
            url=f"/api/userbenches/{userbench_id}/files/{f.path}" if not f.is_dir else None,
        )
        for f in files
    ]


# Compatibility alias
@router.get("/files/{workspace_id}", response_model=List[FileInfo])
async def list_workspace_files(
    workspace_id: str,
    category: str = Query("productions"),
    path: str = Query(""),
    recursive: bool = Query(False),
):
    """Alias for list_userbench_files for compatibility."""
    return await list_userbench_files(workspace_id, category, path, recursive)


@router.get("/userbenches/{userbench_id}/files/productions")
async def list_bench_productions(
    userbench_id: str,
    recursive: bool = Query(True),
):
    """List production (output) files."""
    return await list_userbench_files(userbench_id, category="productions", recursive=recursive)


@router.get("/files/{workspace_id}/productions")
async def list_productions(workspace_id: str, recursive: bool = Query(True)):
    """Compatibility alias."""
    return await list_bench_productions(workspace_id, recursive)


@router.get("/userbenches/{userbench_id}/files/provisions")
async def list_bench_provisions(
    userbench_id: str,
    recursive: bool = Query(True),
):
    """List provision files (prompts, scripts, data)."""
    return await list_userbench_files(userbench_id, category="provisions", recursive=recursive)


@router.get("/files/{workspace_id}/provisions")
async def list_provisions(workspace_id: str, recursive: bool = Query(True)):
    """Compatibility alias."""
    return await list_bench_provisions(workspace_id, recursive)


@router.get("/files/{workspace_id}/outputs")
async def list_outputs(workspace_id: str, recursive: bool = Query(True)):
    """Convenience endpoint to list output files (alias for productions)."""
    return await list_bench_productions(workspace_id, recursive)


@router.get("/userbenches/{userbench_id}/files/root")
async def list_bench_root_files(userbench_id: str):
    """
    List root-level files in the bench.
    
    These include:
    - .ncd, .ncds files (plan definitions)
    - inputs.json
    - manifest.json
    - .normcode-canvas.json
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    files = []
    for item in bench.root.iterdir():
        if item.is_file() and not item.name.startswith("."):
            stat = item.stat()
            files.append(FileInfo(
                name=item.name,
                path=item.name,
                absolute_path=str(item),
                is_dir=False,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                content_type=_get_content_type(item),
                url=f"/api/userbenches/{userbench_id}/files/{item.name}",
            ))
    
    return sorted(files, key=lambda f: f.name.lower())


@router.get("/files/{workspace_id}/root")
async def list_root_files(workspace_id: str):
    """Compatibility alias."""
    return await list_bench_root_files(workspace_id)


def _get_content_type(filepath: Path) -> str:
    """Guess content type from file extension."""
    ext = filepath.suffix.lower()
    content_types = {
        ".json": "application/json",
        ".html": "text/html",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".css": "text/css",
        ".ncd": "text/x-normcode",
        ".ncds": "text/x-normcode",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
        ".zip": "application/zip",
    }
    return content_types.get(ext, "application/octet-stream")


# ============================================================================
# File Events (SSE) - MUST come before catch-all route!
# ============================================================================

@router.get("/userbenches/{userbench_id}/events/stream")
async def stream_bench_file_events(userbench_id: str):
    """
    Stream file events for a userbench via Server-Sent Events.
    
    Events are emitted when files are created, modified, or deleted
    in the bench during plan execution.
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    async def event_generator():
        """Generate SSE events."""
        event_queue: asyncio.Queue = asyncio.Queue()
        
        def on_event(event):
            try:
                event_queue.put_nowait(event)
            except Exception:
                pass
        
        # Subscribe to events
        unsubscribe = manager.subscribe_to_events(userbench_id, on_event)
        
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'userbench_id': userbench_id})}\n\n"
            
            while True:
                try:
                    # Wait for event with timeout (to send keepalives)
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    
                    yield f"event: file\ndata: {json.dumps(event.to_dict())}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"event: keepalive\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# Compatibility alias
@router.get("/files/{workspace_id}/events/stream")
async def stream_file_events(workspace_id: str):
    """Alias for compatibility."""
    return await stream_bench_file_events(workspace_id)


@router.get("/userbenches/{userbench_id}/events")
async def get_bench_file_events(
    userbench_id: str,
    since: Optional[str] = Query(None, description="ISO timestamp to filter events after"),
):
    """
    Get file events for a userbench (non-streaming).
    
    Use 'since' parameter to get only events after a certain time.
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    events = bench.get_events(since=since)
    
    return {
        "userbench_id": userbench_id,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


# Compatibility alias
@router.get("/files/{workspace_id}/events")
async def get_file_events(workspace_id: str, since: Optional[str] = Query(None)):
    """Alias for compatibility."""
    return await get_bench_file_events(workspace_id, since)


# ============================================================================
# File Upload Endpoints
# ============================================================================

@router.put("/userbenches/{userbench_id}/files/{file_path:path}")
async def upload_bench_file(userbench_id: str, file_path: str, request: Request):
    """
    Upload/write a file to a userbench.
    
    The file_path can include a category prefix:
    - provisions/inputs/content/data.md -> writes to provisions/inputs/content/
    - productions/results.json -> writes to productions/
    - inputs.json -> writes to root (special case for inputs.json)
    
    Content-Type determines how the body is interpreted:
    - application/json: JSON content
    - text/*: Text content
    - Other: Binary content
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    
    # Get or create userbench if it doesn't exist
    bench = manager.get_or_create_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=500, detail=f"Failed to create userbench: {userbench_id}")
    
    # Parse category from path
    parts = Path(file_path).parts
    category_map = {
        "provisions": "provisions",
        "productions": "productions",
        "outputs": "outputs",
        "inputs": "inputs",
        "logs": "logs",
    }
    
    # Determine category and relative path
    if len(parts) > 1 and parts[0].lower() in category_map:
        category = category_map[parts[0].lower()]
        relative_path = "/".join(parts[1:])
    else:
        # Root file (like inputs.json) - write directly to root
        category = "root"
        relative_path = file_path
    
    # Get content from request body
    content_type = request.headers.get("content-type", "application/octet-stream")
    body = await request.body()
    
    try:
        if "application/json" in content_type:
            # JSON content - write as string
            content = body.decode("utf-8")
            if category == "root":
                # Write directly to root
                file_path_full = bench.root / relative_path
                file_path_full.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path_full, "w", encoding="utf-8") as f:
                    f.write(content)
                result = FileInfo(
                    name=Path(relative_path).name,
                    path=relative_path,
                    absolute_path=str(file_path_full),
                    is_dir=False,
                    size=len(content.encode("utf-8")),
                    modified=datetime.now().isoformat(),
                    created=datetime.now().isoformat(),
                    content_type="application/json",
                )
            else:
                result = bench.write_file(relative_path, content, category=category)
        elif content_type.startswith("text/"):
            # Text content
            content = body.decode("utf-8")
            if category == "root":
                file_path_full = bench.root / relative_path
                file_path_full.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path_full, "w", encoding="utf-8") as f:
                    f.write(content)
                result = FileInfo(
                    name=Path(relative_path).name,
                    path=relative_path,
                    absolute_path=str(file_path_full),
                    is_dir=False,
                    size=len(content.encode("utf-8")),
                    modified=datetime.now().isoformat(),
                    created=datetime.now().isoformat(),
                    content_type=content_type,
                )
            else:
                result = bench.write_file(relative_path, content, category=category)
        else:
            # Binary content
            if category == "root":
                file_path_full = bench.root / relative_path
                file_path_full.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path_full, "wb") as f:
                    f.write(body)
                result = FileInfo(
                    name=Path(relative_path).name,
                    path=relative_path,
                    absolute_path=str(file_path_full),
                    is_dir=False,
                    size=len(body),
                    modified=datetime.now().isoformat(),
                    created=datetime.now().isoformat(),
                    content_type=content_type,
                )
            else:
                result = bench.write_binary(relative_path, body, category=category)
        
        return {
            "success": True,
            "file": {
                "name": result.name,
                "path": result.path,
                "size": result.size,
                "content_type": result.content_type,
            },
            "userbench_id": userbench_id,
        }
        
    except Exception as e:
        logger.error(f"Error writing file to userbench: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


# Compatibility alias
@router.put("/files/{workspace_id}/{file_path:path}")
async def upload_workspace_file(workspace_id: str, file_path: str, request: Request):
    """Alias for compatibility."""
    return await upload_bench_file(workspace_id, file_path, request)


# ============================================================================
# File Download Endpoints - Catch-all route MUST be last!
# ============================================================================

@router.get("/userbenches/{userbench_id}/files/{file_path:path}")
async def download_bench_file(userbench_id: str, file_path: str):
    """
    Download a file from a userbench.
    
    The file_path can include a category prefix:
    - productions/result.json
    - provisions/prompts/instruction.md
    - inputs/config.json
    - logs/run.log
    
    Or be a root file:
    - inputs.json
    - _.ncd
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    # Parse category from path
    parts = Path(file_path).parts
    if not parts:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Map common category names
    category_map = {
        "productions": "productions",
        "production": "productions",
        "outputs": "productions",
        "output": "productions",
        "provisions": "provisions",
        "provision": "provisions",
        "inputs": "inputs",
        "input": "inputs",
        "logs": "logs",
        "log": "logs",
        "temp": "temp",
        "repos": "root",  # repos/ is at root level
    }
    
    if parts[0].lower() in category_map:
        category = category_map[parts[0].lower()]
        if category == "root":
            # repos/ folder is at bench root
            relative_path = file_path
            category = "root"
        else:
            relative_path = "/".join(parts[1:]) if len(parts) > 1 else ""
    else:
        # Check if it's a root file (no category prefix)
        root_file = bench.root / file_path
        if root_file.exists():
            resolved = root_file
            category = None  # Already resolved
        else:
            # Default to productions if no category prefix
            category = "productions"
            relative_path = file_path
    
    # Resolve path if not already done
    if category is not None:
        try:
            resolved = bench.resolve_path(relative_path, category)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    if not resolved.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    if resolved.is_dir():
        raise HTTPException(status_code=400, detail="Cannot download directory")
    
    # Determine content type
    media_type = _get_content_type(resolved)
    
    return FileResponse(
        path=str(resolved),
        filename=resolved.name,
        media_type=media_type,
    )


# Compatibility alias - MUST be after userbench version
@router.get("/files/{workspace_id}/{file_path:path}")
async def download_file(workspace_id: str, file_path: str):
    """Alias for compatibility."""
    return await download_bench_file(workspace_id, file_path)


@router.get("/userbenches/{userbench_id}/files/{file_path:path}/content")
async def get_bench_file_content(userbench_id: str, file_path: str):
    """
    Get file content as JSON response (for text files).
    """
    from service.userbench import get_userbench_manager
    
    manager = get_userbench_manager()
    bench = manager.get_or_load_userbench(userbench_id)
    
    if not bench:
        raise HTTPException(status_code=404, detail=f"UserBench not found: {userbench_id}")
    
    # Parse category from path
    parts = Path(file_path).parts
    category_map = {"outputs": "outputs", "productions": "productions", "inputs": "inputs", "logs": "logs", "temp": "temp"}
    
    if parts and parts[0].lower() in category_map:
        category = category_map[parts[0].lower()]
        relative_path = "/".join(parts[1:])
    else:
        category = "outputs"
        relative_path = file_path
    
    content = bench.read_file(relative_path, category)
    
    if content is None:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    return {"content": content, "path": file_path}


@router.get("/files/{workspace_id}/{file_path:path}/content")
async def get_file_content(workspace_id: str, file_path: str):
    """Alias for compatibility."""
    return await get_bench_file_content(workspace_id, file_path)


# ============================================================================
# Run-Associated Files (Convenience)
# ============================================================================

@router.get("/runs/{run_id}/files")
async def list_run_files(
    run_id: str,
    recursive: bool = Query(True),
):
    """
    List output files for a run.
    
    This is a convenience endpoint that maps run_id to workspace_id
    (they are typically the same).
    """
    return await list_workspace_files(run_id, category="outputs", recursive=recursive)


@router.get("/runs/{run_id}/files/{file_path:path}")
async def download_run_file(run_id: str, file_path: str):
    """
    Download a file from a run's workspace.
    """
    # Prepend 'outputs/' if not already a category path
    parts = Path(file_path).parts
    category_map = {"outputs", "inputs", "logs", "temp"}
    
    if not parts or parts[0].lower() not in category_map:
        file_path = f"outputs/{file_path}"
    
    return await download_file(run_id, file_path)

