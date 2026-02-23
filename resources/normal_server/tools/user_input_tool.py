"""
Deployment User Input Tool - CLI/API-based user input for NormCode deployment.

A standalone user input tool that provides:
- CLI-based input for interactive mode
- API-based input for server mode (with pending request queue)
- WebSocket/SSE notification for real-time client updates
- Workspace association for run-specific inputs
- Non-interactive defaults for headless mode
- Same interface as infra UserInputTool
"""

import asyncio
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from service.userbench import UserBench

logger = logging.getLogger(__name__)


class InputStatus(str, Enum):
    """Status of an input request."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class InteractionType(str, Enum):
    """Types of user interactions."""
    SIMPLE_TEXT = "simple_text"
    TEXT_EDITOR = "text_editor"
    CONFIRM = "confirm"
    SELECT = "select"
    FILE_UPLOAD = "file_upload"
    MULTI_SELECT = "multi_select"


@dataclass
class UserInputRequest:
    """A pending user input request."""
    id: str
    prompt: str
    interaction_type: str
    run_id: Optional[str] = None
    workspace_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    response: Optional[Any] = None
    status: InputStatus = InputStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "request_id": self.id,
            "prompt": self.prompt,
            "interaction_type": self.interaction_type,
            "run_id": self.run_id,
            "workspace_id": self.workspace_id,
            "options": self.options,
            "status": self.status.value,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


# Global registry for input requests (for API access)
_global_input_requests: Dict[str, UserInputRequest] = {}
_global_input_events: Dict[str, threading.Event] = {}
_global_lock = threading.Lock()
_event_callbacks: List[Callable[[str, Dict], None]] = []


def register_input_event_callback(callback: Callable[[str, Dict], None]):
    """Register a callback for input events (for broadcasting to clients)."""
    _event_callbacks.append(callback)


def unregister_input_event_callback(callback: Callable[[str, Dict], None]):
    """Unregister an input event callback."""
    if callback in _event_callbacks:
        _event_callbacks.remove(callback)


def _emit_global_event(event_type: str, data: Dict[str, Any]):
    """Emit an event to all registered callbacks."""
    for callback in _event_callbacks:
        try:
            callback(event_type, data)
        except Exception as e:
            logger.error(f"Input event callback error: {e}")


def get_all_pending_requests() -> List[Dict[str, Any]]:
    """Get all pending input requests across all tools (for API)."""
    with _global_lock:
        return [
            req.to_dict()
            for req in _global_input_requests.values()
            if req.status == InputStatus.PENDING
        ]


def get_pending_requests_for_run(run_id: str) -> List[Dict[str, Any]]:
    """Get pending input requests for a specific run."""
    with _global_lock:
        return [
            req.to_dict()
            for req in _global_input_requests.values()
            if req.status == InputStatus.PENDING and req.run_id == run_id
        ]


def submit_global_response(request_id: str, response: Any) -> bool:
    """Submit a response to any pending request (for API)."""
    with _global_lock:
        if request_id not in _global_input_requests:
            return False
        
        request = _global_input_requests[request_id]
        if request.status != InputStatus.PENDING:
            return False
        
        request.response = response
        request.status = InputStatus.COMPLETED
        request.completed_at = time.time()
        
        if request_id in _global_input_events:
            _global_input_events[request_id].set()
    
    _emit_global_event("input:completed", {
        "request_id": request_id,
        "run_id": request.run_id,
    })
    
    return True


def cancel_global_request(request_id: str) -> bool:
    """Cancel a pending request (for API)."""
    with _global_lock:
        if request_id not in _global_input_requests:
            return False
        
        request = _global_input_requests[request_id]
        request.status = InputStatus.CANCELLED
        request.completed_at = time.time()
        
        if request_id in _global_input_events:
            _global_input_events[request_id].set()
    
    _emit_global_event("input:cancelled", {
        "request_id": request_id,
        "run_id": request.run_id,
    })
    
    return True


class DeploymentUserInputTool:
    """
    A user input tool for deployment/server execution.
    
    Supports three modes:
    1. CLI mode (interactive=True): Prompts user via command line
    2. API mode (interactive=False): Waits for API response submission
    3. Non-interactive mode: Uses default values
    
    Features:
    - Workspace association for run-specific inputs
    - Event emission for real-time client updates
    - Global request registry for API access
    - Multiple interaction types (text, confirm, select, etc.)
    
    Interface matches infra._agent._models._user_input_tool.UserInputTool
    """
    
    def __init__(
        self,
        interactive: bool = True,
        non_interactive_defaults: Optional[Dict[str, Any]] = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
        run_id: Optional[str] = None,
        userbench: Optional["UserBench"] = None,
        timeout: int = 300,  # 5 minutes default
    ):
        """
        Initialize the user input tool.
        
        Args:
            interactive: If True, prompt via CLI. If False, use API mode.
            non_interactive_defaults: Default values for non-interactive mode
            log_callback: Optional callback for logging events
            run_id: Associated run ID (for userbench tracking)
            userbench: Associated userbench (for file uploads)
            timeout: Timeout in seconds for API mode (default 5 minutes)
        """
        self.interactive = interactive
        self.non_interactive_defaults = non_interactive_defaults or {}
        self._log_callback = log_callback
        self.run_id = run_id
        self.userbench = userbench
        self.timeout = timeout
        
        # Local tracking (in addition to global)
        self._local_requests: Dict[str, UserInputRequest] = {}
    
    def set_run_context(self, run_id: str, userbench: Optional["UserBench"] = None):
        """Set the run context for this tool instance."""
        self.run_id = run_id
        self.userbench = userbench
        logger.info(f"UserInputTool context set: run_id={run_id}")
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    # =========================================================================
    # Main Interface (matches infra UserInputTool)
    # =========================================================================
    
    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        """Creates a function that prompts the user for simple text input."""
        config = {"interaction_type": "simple_text", "prompt_key": prompt_key}
        return self.create_interaction(**config)
    
    def create_text_editor_function(
        self,
        prompt_key: str = "prompt_text",
        initial_text_key: str = "initial_text"
    ) -> Callable:
        """Creates a function that opens a text editor for the user."""
        config = {
            "interaction_type": "text_editor",
            "prompt_key": prompt_key,
            "initial_text_key": initial_text_key
        }
        return self.create_interaction(**config)
    
    def create_confirm_function(self, prompt_key: str = "prompt_text") -> Callable:
        """Creates a function that asks for yes/no confirmation."""
        config = {"interaction_type": "confirm", "prompt_key": prompt_key}
        return self.create_interaction(**config)
    
    def create_select_function(
        self,
        prompt_key: str = "prompt_text",
        choices_key: str = "choices"
    ) -> Callable:
        """Creates a function that presents a selection list."""
        config = {
            "interaction_type": "select",
            "prompt_key": prompt_key,
            "choices_key": choices_key
        }
        return self.create_interaction(**config)
    
    def create_interaction(self, **config: Any) -> Callable:
        """
        Create an interaction function based on the provided configuration.
        
        Args:
            **config: Configuration including:
                - interaction_type: Type of interaction
                - prompt_key: Key in kwargs containing the prompt text
                - initial_text_key: Key for initial text (for text_editor)
                - choices_key: Key for choices (for select)
                - non_interactive_default: Default value if non-interactive
                
        Returns:
            A callable that takes **kwargs and returns user input
        """
        def interaction_fn(**kwargs: Any) -> Any:
            prompt_key = config.get("prompt_key", "prompt_text")
            prompt_text = kwargs.get(prompt_key, "Enter input: ")
            interaction_type = config.get("interaction_type", "simple_text")
            
            # Build options
            options = config.copy()
            
            # Handle text_editor initial text
            if interaction_type == "text_editor":
                initial_text_key = config.get("initial_text_key", "initial_text")
                initial_text = kwargs.get(initial_text_key, "")
                options["initial_content"] = initial_text
            
            # Handle select choices
            if interaction_type == "select":
                choices_key = config.get("choices_key", "choices")
                choices = kwargs.get(choices_key, [])
                options["choices"] = choices
            
            # Handle multi_select choices
            if interaction_type == "multi_select":
                choices_key = config.get("choices_key", "choices")
                choices = kwargs.get(choices_key, [])
                options["choices"] = choices
            
            # Check for non-interactive default
            non_interactive_default = config.get("non_interactive_default")
            if non_interactive_default is None:
                non_interactive_default = self.non_interactive_defaults.get(interaction_type)
            
            # Add metadata
            options["metadata"] = {
                "run_id": self.run_id,
                "userbench_id": self.userbench.userbench_id if self.userbench else None,
            }
            
            return self._get_input(prompt_text, interaction_type, options, non_interactive_default)
        
        return interaction_fn
    
    def _get_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Any:
        """
        Get user input based on mode.
        
        Args:
            prompt: The prompt to show
            interaction_type: Type of input
            options: Additional options
            default: Default value for non-interactive mode
            
        Returns:
            User input or default
        """
        self._log("user_input:request", {
            "prompt": prompt,
            "interaction_type": interaction_type,
            "options": options,
            "run_id": self.run_id,
        })
        
        if self.interactive:
            return self._cli_input(prompt, interaction_type, options)
        else:
            return self._api_input(prompt, interaction_type, options, default)
    
    def _cli_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get input via command line."""
        try:
            if interaction_type == "confirm":
                response = input(f"{prompt} [y/n]: ").strip().lower()
                result = response in ("y", "yes", "true", "1")
            elif interaction_type == "select":
                choices = options.get("choices", []) if options else []
                print(f"{prompt}")
                for i, choice in enumerate(choices, 1):
                    print(f"  {i}. {choice}")
                response = input("Enter number: ").strip()
                try:
                    idx = int(response) - 1
                    result = choices[idx] if 0 <= idx < len(choices) else choices[0]
                except (ValueError, IndexError):
                    result = choices[0] if choices else ""
            elif interaction_type == "multi_select":
                choices = options.get("choices", []) if options else []
                print(f"{prompt}")
                for i, choice in enumerate(choices, 1):
                    print(f"  {i}. {choice}")
                response = input("Enter numbers (comma-separated): ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in response.split(",")]
                    result = [choices[i] for i in indices if 0 <= i < len(choices)]
                except (ValueError, IndexError):
                    result = []
            elif interaction_type == "text_editor":
                initial = options.get("initial_content", "") if options else ""
                print(f"{prompt}")
                if initial:
                    print(f"[Initial: {initial[:100]}...]")
                print("Enter text (end with Ctrl+D or empty line):")
                lines = []
                try:
                    while True:
                        line = input()
                        if not line:
                            break
                        lines.append(line)
                except EOFError:
                    pass
                result = "\n".join(lines) if lines else initial
            else:
                # simple_text
                result = input(f"{prompt}: ").strip()
            
            self._log("user_input:completed", {
                "interaction_type": interaction_type,
                "response_type": type(result).__name__,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"CLI input failed: {e}")
            return ""
    
    def _api_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Any:
        """Wait for input via API (submit_response)."""
        request_id = str(uuid.uuid4())[:8]
        event = threading.Event()
        
        userbench_id = None
        if self.userbench:
            userbench_id = self.userbench.userbench_id
        
        request = UserInputRequest(
            id=request_id,
            prompt=prompt,
            interaction_type=interaction_type,
            run_id=self.run_id,
            workspace_id=userbench_id,  # Keep field name for API compatibility
            options=options or {},
            metadata=options.get("metadata", {}) if options else {},
        )
        
        # Register in both local and global registries
        self._local_requests[request_id] = request
        
        with _global_lock:
            _global_input_requests[request_id] = request
            _global_input_events[request_id] = event
        
        # Emit event for clients
        _emit_global_event("input:pending", request.to_dict())
        
        self._log("user_input:pending", {
            "request_id": request_id,
            "prompt": prompt,
            "interaction_type": interaction_type,
            "run_id": self.run_id,
        })
        
        logger.info(f"Waiting for user input: {request_id} ({interaction_type})")
        logger.info(f"Prompt: {prompt}")
        
        # Wait with timeout
        received = event.wait(timeout=self.timeout)
        
        # Get response and determine status
        with _global_lock:
            if request_id in _global_input_requests:
                response = _global_input_requests[request_id].response
                status = _global_input_requests[request_id].status
                
                # Update status if timed out
                if not received and status == InputStatus.PENDING:
                    _global_input_requests[request_id].status = InputStatus.TIMEOUT
                    _global_input_requests[request_id].completed_at = time.time()
                    status = InputStatus.TIMEOUT
                
                # Clean up old requests (keep for a while for history)
                # del _global_input_requests[request_id]
            else:
                response = default
                status = InputStatus.TIMEOUT
            
            if request_id in _global_input_events:
                del _global_input_events[request_id]
        
        if not received:
            logger.warning(f"Timeout waiting for input {request_id}, using default")
            _emit_global_event("input:timeout", {
                "request_id": request_id,
                "run_id": self.run_id,
            })
            response = default
        
        self._log("user_input:completed", {
            "request_id": request_id,
            "timed_out": not received,
            "status": status.value,
        })
        
        return self._parse_response(response, interaction_type)
    
    def _parse_response(self, response: Any, interaction_type: str) -> Any:
        """Parse the response based on interaction type."""
        if response is None:
            if interaction_type == "confirm":
                return False
            if interaction_type in ("select", "multi_select"):
                return [] if interaction_type == "multi_select" else ""
            return ""
        
        if interaction_type == "confirm":
            if isinstance(response, bool):
                return response
            return str(response).lower() in ("yes", "y", "true", "1", "confirm")
        
        if interaction_type == "multi_select":
            if isinstance(response, list):
                return response
            return [response] if response else []
        
        return str(response) if response is not None else ""
    
    # =========================================================================
    # API Methods (for external submission)
    # =========================================================================
    
    def submit_response(self, request_id: str, response: Any) -> bool:
        """
        Submit a response for a pending input request.
        
        Called by API when user provides input.
        
        Args:
            request_id: The request ID
            response: The user's response
            
        Returns:
            True if request was found and completed
        """
        return submit_global_response(request_id, response)
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending input request."""
        return cancel_global_request(request_id)
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get pending input requests for this tool's run."""
        if self.run_id:
            return get_pending_requests_for_run(self.run_id)
        
        # Return local requests
        return [
            req.to_dict()
            for req in self._local_requests.values()
            if req.status == InputStatus.PENDING
        ]
    
    def has_pending_requests(self) -> bool:
        """Check if there are any pending requests."""
        return len(self.get_pending_requests()) > 0
    
    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get all requests (including completed) for this run."""
        if self.run_id:
            with _global_lock:
                return [
                    req.to_dict()
                    for req in _global_input_requests.values()
                    if req.run_id == self.run_id
                ]
        return [req.to_dict() for req in self._local_requests.values()]
