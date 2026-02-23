"""
Server-Wide Event Bus

Provides global event broadcasting for monitoring all server activity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Set
from collections import deque

logger = logging.getLogger(__name__)


class ServerEventBus:
    """
    Global event bus for server-wide event broadcasting.
    
    Supports:
    - Multiple subscribers (SSE connections, WebSockets)
    - Event history for late joiners
    - Event filtering by type
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._subscribers: List[asyncio.Queue] = []
        self._history: deque = deque(maxlen=500)  # Keep last 500 events
        self._stats = {
            "total_events": 0,
            "events_by_type": {},
            "runs_started": 0,
            "runs_completed": 0,
            "runs_failed": 0,
            "inferences_executed": 0,
            "llm_calls": 0,
            "llm_tokens_in": 0,
            "llm_tokens_out": 0,
            "start_time": datetime.now().isoformat(),
        }
        logger.info("ServerEventBus initialized")
    
    def subscribe(self) -> asyncio.Queue:
        """Create a new subscription queue."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        logger.debug(f"New subscriber added. Total: {len(self._subscribers)}")
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Remove a subscription."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
            logger.debug(f"Subscriber removed. Total: {len(self._subscribers)}")
    
    async def emit(self, event_type: str, data: Dict[str, Any], run_id: str = None):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: Type of event (e.g., 'run:started', 'inference:completed')
            data: Event payload
            run_id: Associated run ID (optional)
        """
        event = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
            **data,
        }
        
        # Update stats
        self._stats["total_events"] += 1
        self._stats["events_by_type"][event_type] = self._stats["events_by_type"].get(event_type, 0) + 1
        
        # Track specific events
        if event_type == "run:started":
            self._stats["runs_started"] += 1
        elif event_type == "run:completed":
            self._stats["runs_completed"] += 1
        elif event_type == "run:failed":
            self._stats["runs_failed"] += 1
        elif event_type == "inference:completed":
            self._stats["inferences_executed"] += 1
        elif event_type == "llm:call":
            self._stats["llm_calls"] += 1
            self._stats["llm_tokens_in"] += data.get("tokens_in", 0)
            self._stats["llm_tokens_out"] += data.get("tokens_out", 0)
        
        # Add to history
        self._history.append(event)
        
        # Broadcast to subscribers
        disconnected = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except Exception as e:
                logger.warning(f"Failed to send to subscriber: {e}")
                disconnected.append(queue)
        
        # Clean up disconnected
        for queue in disconnected:
            self.unsubscribe(queue)
    
    def get_history(self, limit: int = 100, event_types: List[str] = None) -> List[Dict]:
        """Get recent events from history."""
        events = list(self._history)
        
        if event_types:
            events = [e for e in events if e["event"] in event_types]
        
        return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            **self._stats,
            "subscriber_count": len(self._subscribers),
            "history_size": len(self._history),
        }
    
    def reset_stats(self):
        """Reset statistics (keeps history)."""
        self._stats = {
            "total_events": 0,
            "events_by_type": {},
            "runs_started": 0,
            "runs_completed": 0,
            "runs_failed": 0,
            "inferences_executed": 0,
            "llm_calls": 0,
            "llm_tokens_in": 0,
            "llm_tokens_out": 0,
            "start_time": datetime.now().isoformat(),
        }


# Singleton instance
event_bus = ServerEventBus()


async def emit_server_event(event_type: str, data: Dict[str, Any], run_id: str = None):
    """Convenience function to emit events."""
    await event_bus.emit(event_type, data, run_id)

