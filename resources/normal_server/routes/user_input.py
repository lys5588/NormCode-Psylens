"""
User Input API Routes

Endpoints for handling human-in-the-loop user input:
- List pending input requests
- Submit responses
- Cancel requests
- Stream input events (SSE)
"""

import json
import asyncio
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tools.user_input_tool import (
    get_all_pending_requests,
    get_pending_requests_for_run,
    submit_global_response,
    cancel_global_request,
    register_input_event_callback,
    unregister_input_event_callback,
    _global_input_requests,
    _global_lock,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class InputRequestInfo(BaseModel):
    """Information about an input request."""
    request_id: str
    prompt: str
    interaction_type: str
    run_id: Optional[str] = None
    workspace_id: Optional[str] = None
    options: Optional[dict] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None


class SubmitResponseRequest(BaseModel):
    """Request to submit a response."""
    response: str  # Can be string, will be parsed based on interaction_type


class SubmitConfirmRequest(BaseModel):
    """Request to submit a confirm response."""
    confirmed: bool


class SubmitSelectRequest(BaseModel):
    """Request to submit a selection."""
    selected: str  # For single select
    # selected_items: List[str] = []  # For multi-select


# ============================================================================
# List Endpoints
# ============================================================================

@router.get("/inputs", response_model=List[InputRequestInfo])
async def list_pending_inputs(
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    include_completed: bool = Query(False, description="Include completed requests"),
):
    """
    List pending user input requests.
    
    Use this to discover what inputs are waiting for user response.
    """
    if run_id:
        requests = get_pending_requests_for_run(run_id)
    else:
        requests = get_all_pending_requests()
    
    if include_completed:
        # Include all requests, not just pending
        with _global_lock:
            if run_id:
                requests = [
                    req.to_dict()
                    for req in _global_input_requests.values()
                    if req.run_id == run_id
                ]
            else:
                requests = [req.to_dict() for req in _global_input_requests.values()]
    
    return [
        InputRequestInfo(
            request_id=r["request_id"],
            prompt=r["prompt"],
            interaction_type=r["interaction_type"],
            run_id=r.get("run_id"),
            workspace_id=r.get("workspace_id"),
            options=r.get("options"),
            status=r["status"],
            created_at=r["created_at"],
            completed_at=r.get("completed_at"),
        )
        for r in requests
    ]


# ============================================================================
# Event Streaming (SSE) - MUST come before {request_id} routes!
# ============================================================================

@router.get("/inputs/stream")
async def stream_input_events(
    run_id: Optional[str] = Query(None, description="Filter events by run ID"),
):
    """
    Stream user input events via Server-Sent Events.
    
    Events:
    - input:pending - New input request waiting
    - input:completed - Input was submitted
    - input:cancelled - Input was cancelled
    - input:timeout - Input timed out
    """
    async def event_generator():
        event_queue: asyncio.Queue = asyncio.Queue()
        
        def on_event(event_type: str, data: dict):
            # Filter by run_id if specified
            if run_id and data.get("run_id") != run_id:
                return
            try:
                event_queue.put_nowait({"event": event_type, "data": data})
            except Exception:
                pass
        
        # Register callback
        register_input_event_callback(on_event)
        
        try:
            # Send current pending requests as initial state
            if run_id:
                pending = get_pending_requests_for_run(run_id)
            else:
                pending = get_all_pending_requests()
            
            for req in pending:
                yield f"event: input:pending\ndata: {json.dumps(req)}\n\n"
            
            # Stream events
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive
                    yield f"event: keepalive\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            unregister_input_event_callback(on_event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================================
# Single Request Endpoints - {request_id} routes come after /stream
# ============================================================================

@router.get("/inputs/{request_id}", response_model=InputRequestInfo)
async def get_input_request(request_id: str):
    """
    Get details of a specific input request.
    """
    with _global_lock:
        if request_id not in _global_input_requests:
            raise HTTPException(status_code=404, detail=f"Input request not found: {request_id}")
        
        r = _global_input_requests[request_id].to_dict()
    
    return InputRequestInfo(
        request_id=r["request_id"],
        prompt=r["prompt"],
        interaction_type=r["interaction_type"],
        run_id=r.get("run_id"),
        workspace_id=r.get("workspace_id"),
        options=r.get("options"),
        status=r["status"],
        created_at=r["created_at"],
        completed_at=r.get("completed_at"),
    )


# ============================================================================
# Response Submission Endpoints
# ============================================================================

@router.post("/inputs/{request_id}/submit")
async def submit_input_response(request_id: str, body: SubmitResponseRequest):
    """
    Submit a text response to a pending input request.
    
    The response will be parsed according to the interaction type.
    """
    success = submit_global_response(request_id, body.response)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Request not found or already completed: {request_id}"
        )
    
    return {"status": "submitted", "request_id": request_id}


@router.post("/inputs/{request_id}/confirm")
async def submit_confirm_response(request_id: str, body: SubmitConfirmRequest):
    """
    Submit a confirm/deny response.
    """
    success = submit_global_response(request_id, body.confirmed)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Request not found or already completed: {request_id}"
        )
    
    return {"status": "submitted", "request_id": request_id, "confirmed": body.confirmed}


@router.post("/inputs/{request_id}/select")
async def submit_select_response(request_id: str, body: SubmitSelectRequest):
    """
    Submit a selection response.
    """
    success = submit_global_response(request_id, body.selected)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Request not found or already completed: {request_id}"
        )
    
    return {"status": "submitted", "request_id": request_id, "selected": body.selected}


@router.post("/inputs/{request_id}/cancel")
async def cancel_input_request(request_id: str):
    """
    Cancel a pending input request.
    
    The plan will receive a default/null value.
    """
    success = cancel_global_request(request_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Request not found or already completed: {request_id}"
        )
    
    return {"status": "cancelled", "request_id": request_id}


# ============================================================================
# Run-specific Endpoints
# ============================================================================

@router.get("/runs/{run_id}/inputs", response_model=List[InputRequestInfo])
async def list_run_inputs(
    run_id: str,
    include_completed: bool = Query(False),
):
    """
    List input requests for a specific run.
    """
    return await list_pending_inputs(run_id=run_id, include_completed=include_completed)


@router.get("/runs/{run_id}/inputs/pending/count")
async def get_pending_count(run_id: str):
    """
    Get count of pending inputs for a run.
    
    Useful for UI indicators.
    """
    requests = get_pending_requests_for_run(run_id)
    return {"run_id": run_id, "pending_count": len(requests)}



