"""
Monitor Routes

Server-wide monitoring and event streaming endpoints.
"""

import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from service.event_bus import event_bus
from service.globals import active_runs

router = APIRouter()


@router.get("/stream")
async def stream_server_events():
    """
    SSE endpoint for streaming ALL server events.
    
    This provides a unified event stream for monitoring the entire server,
    as opposed to per-run streams. Useful for dashboards and development.
    
    Event types include:
    - server:* - Server lifecycle events
    - run:* - Run lifecycle (started, completed, failed, stopped)
    - inference:* - Inference execution events
    - llm:* - LLM call tracking
    - cycle:* - Execution cycle events
    """
    async def event_generator():
        queue = event_bus.subscribe()
        
        try:
            # Send initial connection event with current state
            initial = {
                "event": "monitor:connected",
                "timestamp": datetime.now().isoformat(),
                "stats": event_bus.get_stats(),
                "active_runs": [
                    {
                        "run_id": run.run_id,
                        "plan_id": run.plan_id,
                        "status": run.status,
                        "progress": {
                            "completed_count": run.completed_count,
                            "total_count": run.total_count,
                            "cycle_count": run.cycle_count,
                        }
                    }
                    for run in active_runs.values()
                ],
            }
            yield f"data: {json.dumps(initial)}\n\n"
            
            # Stream events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    
        finally:
            event_bus.unsubscribe(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.websocket("/ws")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for server monitoring."""
    await websocket.accept()
    queue = event_bus.subscribe()
    
    try:
        # Send initial state
        initial = {
            "event": "monitor:connected",
            "stats": event_bus.get_stats(),
            "active_runs": [
                {
                    "run_id": run.run_id,
                    "plan_id": run.plan_id,
                    "status": run.status,
                }
                for run in active_runs.values()
            ],
        }
        await websocket.send_json(initial)
        
        # Create tasks for receiving and sending
        async def receive_messages():
            while True:
                try:
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")
                    elif data == "stats":
                        await websocket.send_json({
                            "event": "stats",
                            "data": event_bus.get_stats()
                        })
                except Exception:
                    break
        
        async def send_events():
            while True:
                event = await queue.get()
                await websocket.send_json(event)
        
        # Run both concurrently
        receive_task = asyncio.create_task(receive_messages())
        send_task = asyncio.create_task(send_events())
        
        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
            
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe(queue)


@router.get("/stats")
async def get_server_stats():
    """Get server statistics."""
    return {
        "stats": event_bus.get_stats(),
        "active_runs": {
            run_id: {
                "plan_id": run.plan_id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "progress": {
                    "completed_count": run.completed_count,
                    "total_count": run.total_count,
                    "cycle_count": run.cycle_count,
                    "current_inference": run.current_inference,
                }
            }
            for run_id, run in active_runs.items()
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/history")
async def get_event_history(limit: int = 100, event_type: str = None):
    """Get recent event history."""
    event_types = [event_type] if event_type else None
    history = event_bus.get_history(limit=limit, event_types=event_types)
    return {
        "events": history,
        "total": len(history),
    }


@router.post("/stats/reset")
async def reset_stats():
    """Reset server statistics."""
    event_bus.reset_stats()
    return {"status": "reset", "stats": event_bus.get_stats()}

