"""
UserBench Manager

Manages isolated user benches for each run/client, providing:
- Unique folder creation per run
- File tracking and change events
- Accessible outputs for clients to download
- UserBench lifecycle management
"""

import os
import json
import shutil
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FileEventType(str, Enum):
    """Types of file events."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    DIRECTORY_CREATED = "directory_created"


@dataclass
class FileEvent:
    """A file change event."""
    event_type: FileEventType
    path: str  # Relative path within userbench
    absolute_path: str
    timestamp: str
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "path": self.path,
            "absolute_path": self.absolute_path,
            "timestamp": self.timestamp,
            "size": self.size,
            "metadata": self.metadata,
        }


@dataclass
class FileInfo:
    """Information about a file in the userbench."""
    name: str
    path: str  # Relative to userbench
    absolute_path: str
    is_dir: bool
    size: int
    modified: str
    created: str
    content_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UserBench:
    """
    A user bench - an isolated folder for a specific USER (not run).
    
    Each user has ONE bench that persists across multiple runs.
    Runs share the user's bench for file storage.
    
    Provides:
    - Sandboxed file operations within the bench
    - File change tracking
    - Event emission for real-time updates
    - Per-run output subdirectories
    """
    
    def __init__(
        self,
        user_id: str,
        base_path: Path,
        event_callback: Optional[Callable[[FileEvent], None]] = None,
    ):
        """
        Initialize a user bench.
        
        Args:
            user_id: User ID (bench is per-user, not per-run)
            base_path: Root path where bench folder will be created
            event_callback: Callback for file events (async-compatible)
        """
        self.user_id = user_id
        self.userbench_id = user_id  # Same as user_id
        # Keep workspace_id as alias for compatibility
        self.workspace_id = user_id
        
        # Track runs that use this bench
        self.active_runs: List[str] = []
        self.current_run_id: Optional[str] = None
        self.current_plan_id: Optional[str] = None
        
        self._event_callback = event_callback
        
        # Create bench folder structure
        self.root = base_path / user_id
        self.productions_dir = self.root / "productions"  # Main outputs
        self.provisions_dir = self.root / "provisions"    # Prompts, scripts, data
        self.inputs_dir = self.root / "inputs"            # Input files
        self.logs_dir = self.root / "logs"
        self.temp_dir = self.root / ".temp"
        self.runs_dir = self.root / "runs"                # Per-run subdirectories
        
        # Legacy alias for compatibility
        self.outputs_dir = self.productions_dir
        
        # File tracking
        self._file_events: List[FileEvent] = []
        self._file_hashes: Dict[str, str] = {}
        
        # Metadata
        self.created_at = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}
    
    def set_current_run(self, run_id: str, plan_id: Optional[str] = None, plan_dir: Optional[Path] = None):
        """
        Set the current active run for this bench.
        
        This allows the bench to organize outputs by run.
        
        Args:
            run_id: Current run ID
            plan_id: Plan being executed
            plan_dir: Plan directory (to copy provisions)
        """
        self.current_run_id = run_id
        self.current_plan_id = plan_id
        
        if run_id not in self.active_runs:
            self.active_runs.append(run_id)
        
        # Create run-specific output directory
        run_output_dir = self.runs_dir / run_id
        run_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy plan files if this is a new plan
        if plan_dir and plan_dir.exists():
            self._copy_plan_files(plan_dir)
        
        # Save metadata to disk so it persists across restarts
        self._save_metadata()
        
        logger.info(f"UserBench {self.user_id}: Run {run_id} started (plan: {plan_id})")
    
    def get_run_output_dir(self, run_id: Optional[str] = None) -> Path:
        """Get the output directory for a specific run."""
        rid = run_id or self.current_run_id
        if rid:
            run_dir = self.runs_dir / rid
            run_dir.mkdir(parents=True, exist_ok=True)
            return run_dir
        return self.productions_dir  # Fallback to shared productions
    
    def initialize(self) -> "UserBench":
        """
        Create the bench directory structure.
        
        Plan files are copied when a run starts via set_current_run().
        """
        self.root.mkdir(parents=True, exist_ok=True)
        self.productions_dir.mkdir(exist_ok=True)
        self.provisions_dir.mkdir(exist_ok=True)
        self.inputs_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.runs_dir.mkdir(exist_ok=True)
        
        # Save bench metadata
        self._save_metadata()
        
        logger.info(f"UserBench initialized: {self.root}")
        return self
    
    def _copy_plan_files(self, plan_dir: Path):
        """
        Copy important files from the plan directory to the bench.
        
        Copies:
        - provisions/ directory (prompts, scripts, paradigms, data)
        - productions/ directory (if exists, for structure)
        - inputs.json
        - Any .ncd or .ncds files (NormCode plan definitions)
        - manifest.json or .normcode-canvas.json (plan config)
        """
        if not plan_dir or not plan_dir.exists():
            logger.warning(f"Plan directory not found: {plan_dir}")
            return
        
        copied_count = 0
        
        # 1. Copy provisions/ directory
        src_provisions = plan_dir / "provisions"
        if not src_provisions.exists():
            # Try alternate name
            src_provisions = plan_dir / "provision"
        
        if src_provisions.exists():
            copied_count += self._copy_directory(src_provisions, self.provisions_dir)
            logger.info(f"Copied provisions/ to bench")
        
        # 2. Copy or create productions/ structure
        src_productions = plan_dir / "productions"
        if src_productions.exists():
            # Copy existing structure (but not outputs from previous runs)
            for item in src_productions.iterdir():
                if item.is_dir():
                    (self.productions_dir / item.name).mkdir(exist_ok=True)
        
        # 3. Copy inputs.json
        inputs_file = plan_dir / "inputs.json"
        if inputs_file.exists():
            shutil.copy2(inputs_file, self.root / "inputs.json")
            copied_count += 1
            logger.info(f"Copied inputs.json to bench")
        
        # 4. Copy .ncd and .ncds files (NormCode plan definitions)
        for pattern in ["*.ncd", "*.ncds", "*.pf.ncd"]:
            for ncd_file in plan_dir.glob(pattern):
                if ncd_file.is_file():
                    shutil.copy2(ncd_file, self.root / ncd_file.name)
                    copied_count += 1
                    logger.info(f"Copied {ncd_file.name} to bench")
        
        # 5. Copy manifest or config files
        for config_name in ["manifest.json", "*.normcode-canvas.json", "*.agent.json"]:
            for config_file in plan_dir.glob(config_name):
                if config_file.is_file():
                    shutil.copy2(config_file, self.root / config_file.name)
                    copied_count += 1
        
        # 6. Copy instruction file if exists
        instruction_file = plan_dir / "_.instruction.md"
        if instruction_file.exists():
            shutil.copy2(instruction_file, self.root / "_.instruction.md")
            copied_count += 1
        
        # 7. Copy repository files (for reference)
        repos_dir = plan_dir / "repos"
        if repos_dir.exists():
            dst_repos = self.root / "repos"
            dst_repos.mkdir(exist_ok=True)
            for repo_file in repos_dir.glob("*.json"):
                shutil.copy2(repo_file, dst_repos / repo_file.name)
                copied_count += 1
        else:
            # Check for repo files in root
            for repo_name in ["concept_repo.json", "inference_repo.json"]:
                repo_file = plan_dir / repo_name
                if repo_file.exists():
                    shutil.copy2(repo_file, self.root / repo_name)
                    copied_count += 1
        
        logger.info(f"UserBench initialized with {copied_count} files from plan")
        self.metadata["copied_files_count"] = copied_count
    
    def _copy_directory(self, src: Path, dst: Path, exclude_patterns: List[str] = None) -> int:
        """
        Recursively copy a directory, excluding certain patterns.
        
        Returns:
            Number of files copied
        """
        exclude_patterns = exclude_patterns or ["__pycache__", "*.pyc", ".git", ".DS_Store"]
        copied = 0
        
        dst.mkdir(parents=True, exist_ok=True)
        
        for item in src.iterdir():
            # Check exclusions
            skip = False
            for pattern in exclude_patterns:
                if pattern.startswith("*"):
                    if item.name.endswith(pattern[1:]):
                        skip = True
                        break
                elif item.name == pattern:
                    skip = True
                    break
            
            if skip:
                continue
            
            dst_item = dst / item.name
            
            if item.is_dir():
                copied += self._copy_directory(item, dst_item, exclude_patterns)
            else:
                shutil.copy2(item, dst_item)
                copied += 1
        
        return copied
    
    def _save_metadata(self):
        """Save bench metadata to disk."""
        meta = {
            "user_id": self.user_id,
            "userbench_id": self.userbench_id,
            "workspace_id": self.userbench_id,  # Compatibility
            "created_at": self.created_at,
            "active_runs": self.active_runs,
            "current_run_id": self.current_run_id,
            "current_plan_id": self.current_plan_id,
            "metadata": self.metadata,
        }
        meta_file = self.root / ".userbench.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    
    def _emit_event(self, event: FileEvent):
        """Emit a file event."""
        self._file_events.append(event)
        if self._event_callback:
            try:
                self._event_callback(event)
            except Exception as e:
                logger.error(f"Event callback failed: {e}")
    
    def _compute_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _get_content_type(self, filepath: Path) -> str:
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
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
        }
        return content_types.get(ext, "application/octet-stream")
    
    def resolve_path(self, path: str, category: str = "outputs") -> Path:
        """
        Resolve a path within the bench.
        
        Args:
            path: Relative path within the bench
            category: Category folder (productions/outputs, provisions, inputs, logs)
            
        Returns:
            Absolute path within bench
        """
        # Get category directory (support both old and new names)
        category_dirs = {
            # Primary names
            "productions": self.productions_dir,
            "provisions": self.provisions_dir,
            "inputs": self.inputs_dir,
            "logs": self.logs_dir,
            "temp": self.temp_dir,
            "root": self.root,
            # Legacy aliases
            "outputs": self.productions_dir,
            "output": self.productions_dir,
            "provision": self.provisions_dir,
            "input": self.inputs_dir,
            "log": self.logs_dir,
        }
        base = category_dirs.get(category.lower(), self.productions_dir)
        
        # Resolve and ensure within bench
        resolved = (base / path).resolve()
        
        # Security check: ensure path is within bench
        try:
            resolved.relative_to(self.root)
        except ValueError:
            raise ValueError(f"Path escapes bench: {path}")
        
        return resolved
    
    def write_file(
        self,
        path: str,
        content: str,
        category: str = "outputs",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileInfo:
        """
        Write a file to the bench.
        
        Args:
            path: Relative path within category
            content: File content
            category: Category folder (outputs, inputs, temp)
            metadata: Optional metadata to attach to event
            
        Returns:
            FileInfo for the created/modified file
        """
        resolved = self.resolve_path(path, category)
        
        # Create parent directories
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists (for event type)
        is_new = not resolved.exists()
        
        # Write content
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Create file info (use forward slashes for URL compatibility)
        stat = resolved.stat()
        rel_path = resolved.relative_to(self.root).as_posix()
        
        file_info = FileInfo(
            name=resolved.name,
            path=rel_path,
            absolute_path=str(resolved),
            is_dir=False,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            content_type=self._get_content_type(resolved),
        )
        
        # Emit event
        event = FileEvent(
            event_type=FileEventType.CREATED if is_new else FileEventType.MODIFIED,
            path=rel_path,
            absolute_path=str(resolved),
            timestamp=datetime.now().isoformat(),
            size=stat.st_size,
            metadata=metadata or {},
        )
        self._emit_event(event)
        
        # Update hash tracking
        self._file_hashes[rel_path] = self._compute_hash(resolved)
        
        logger.debug(f"UserBench file written: {rel_path}")
        return file_info
    
    def write_binary(
        self,
        path: str,
        content: bytes,
        category: str = "outputs",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileInfo:
        """Write binary content to the bench."""
        resolved = self.resolve_path(path, category)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        is_new = not resolved.exists()
        
        with open(resolved, "wb") as f:
            f.write(content)
        
        stat = resolved.stat()
        rel_path = resolved.relative_to(self.root).as_posix()
        
        file_info = FileInfo(
            name=resolved.name,
            path=rel_path,
            absolute_path=str(resolved),
            is_dir=False,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            content_type=self._get_content_type(resolved),
        )
        
        event = FileEvent(
            event_type=FileEventType.CREATED if is_new else FileEventType.MODIFIED,
            path=rel_path,
            absolute_path=str(resolved),
            timestamp=datetime.now().isoformat(),
            size=stat.st_size,
            metadata=metadata or {},
        )
        self._emit_event(event)
        
        return file_info
    
    def read_file(self, path: str, category: str = "outputs") -> Optional[str]:
        """Read a file from the bench."""
        resolved = self.resolve_path(path, category)
        
        if not resolved.exists():
            return None
        
        with open(resolved, "r", encoding="utf-8") as f:
            return f.read()
    
    def read_binary(self, path: str, category: str = "outputs") -> Optional[bytes]:
        """Read binary content from the bench."""
        resolved = self.resolve_path(path, category)
        
        if not resolved.exists():
            return None
        
        with open(resolved, "rb") as f:
            return f.read()
    
    def delete_file(self, path: str, category: str = "outputs") -> bool:
        """Delete a file from the bench."""
        resolved = self.resolve_path(path, category)
        
        if not resolved.exists():
            return False
        
        rel_path = resolved.relative_to(self.root).as_posix()
        resolved.unlink()
        
        event = FileEvent(
            event_type=FileEventType.DELETED,
            path=rel_path,
            absolute_path=str(resolved),
            timestamp=datetime.now().isoformat(),
        )
        self._emit_event(event)
        
        return True
    
    def mkdir(self, path: str, category: str = "outputs") -> Path:
        """Create a directory within the bench."""
        resolved = self.resolve_path(path, category)
        resolved.mkdir(parents=True, exist_ok=True)
        
        rel_path = resolved.relative_to(self.root).as_posix()
        event = FileEvent(
            event_type=FileEventType.DIRECTORY_CREATED,
            path=rel_path,
            absolute_path=str(resolved),
            timestamp=datetime.now().isoformat(),
        )
        self._emit_event(event)
        
        return resolved
    
    def list_files(
        self,
        path: str = "",
        category: str = "outputs",
        recursive: bool = False,
    ) -> List[FileInfo]:
        """
        List files in a directory within the bench.
        
        Args:
            path: Subdirectory path (empty for root of category)
            category: Category folder
            recursive: Include subdirectories recursively
            
        Returns:
            List of FileInfo objects
        """
        resolved = self.resolve_path(path, category)
        
        if not resolved.exists() or not resolved.is_dir():
            return []
        
        files = []
        iterator = resolved.rglob("*") if recursive else resolved.iterdir()
        
        for item in iterator:
            if item.name.startswith("."):
                continue  # Skip hidden files
            
            try:
                stat = item.stat()
                rel_path = item.relative_to(self.root).as_posix()
                
                files.append(FileInfo(
                    name=item.name,
                    path=rel_path,
                    absolute_path=str(item),
                    is_dir=item.is_dir(),
                    size=stat.st_size if item.is_file() else 0,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    content_type=self._get_content_type(item) if item.is_file() else None,
                ))
            except Exception as e:
                logger.warning(f"Error listing file {item}: {e}")
        
        return sorted(files, key=lambda f: (not f.is_dir, f.name.lower()))
    
    def get_all_outputs(self) -> List[FileInfo]:
        """Get all output files (convenience method)."""
        return self.list_files(category="outputs", recursive=True)
    
    def get_events(self, since: Optional[str] = None) -> List[FileEvent]:
        """
        Get file events, optionally filtered by timestamp.
        
        Args:
            since: ISO timestamp to filter events after
            
        Returns:
            List of FileEvent objects
        """
        if since:
            return [e for e in self._file_events if e.timestamp > since]
        return list(self._file_events)
    
    def get_userbench_info(self) -> Dict[str, Any]:
        """Get bench summary info."""
        production_files = self.list_files(category="productions", recursive=True)
        provision_files = self.list_files(category="provisions", recursive=True)
        
        return {
            "user_id": self.user_id,
            "userbench_id": self.userbench_id,
            "workspace_id": self.userbench_id,  # Compatibility
            "current_run_id": self.current_run_id,
            "current_plan_id": self.current_plan_id,
            "active_runs": self.active_runs,
            "created_at": self.created_at,
            "root_path": str(self.root),
            "productions_path": str(self.productions_dir),
            "provisions_path": str(self.provisions_dir),
            "outputs_path": str(self.productions_dir),  # Legacy alias
            "runs_path": str(self.runs_dir),
            "file_count": len([f for f in production_files if not f.is_dir]),
            "total_size": sum(f.size for f in production_files if not f.is_dir),
            "provision_count": len([f for f in provision_files if not f.is_dir]),
            "event_count": len(self._file_events),
            "metadata": self.metadata,
        }
    
    # Alias for compatibility
    def get_workspace_info(self) -> Dict[str, Any]:
        """Alias for get_userbench_info for compatibility."""
        return self.get_userbench_info()
    
    def get_userbench_structure(self) -> Dict[str, Any]:
        """
        Get the full bench structure for client display.
        
        Returns a tree structure of the bench contents.
        """
        def build_tree(directory: Path, prefix: str = "") -> List[Dict]:
            """Build a tree structure of a directory."""
            items = []
            if not directory.exists():
                return items
            
            for item in sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith("."):
                    continue
                
                # Use forward slashes for URL compatibility (Windows uses backslashes)
                rel_path = item.relative_to(self.root).as_posix()
                
                if item.is_dir():
                    items.append({
                        "name": item.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": build_tree(item, rel_path),
                    })
                else:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": rel_path,
                        "type": "file",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "url": f"/api/userbenches/{self.userbench_id}/files/{rel_path}",
                    })
            
            return items
        
        return {
            "userbench_id": self.userbench_id,
            "workspace_id": self.userbench_id,  # Compatibility
            "plan_id": self.current_plan_id,
            "created_at": self.created_at,
            "structure": {
                "productions": build_tree(self.productions_dir),
                "provisions": build_tree(self.provisions_dir),
                "inputs": build_tree(self.inputs_dir),
                "logs": build_tree(self.logs_dir),
                "root_files": [
                    {
                        "name": f.name,
                        "path": f.name,
                        "type": "file",
                        "size": f.stat().st_size,
                        "url": f"/api/userbenches/{self.userbench_id}/files/{f.name}",
                    }
                    for f in self.root.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                ],
            },
        }
    
    # Alias for compatibility
    def get_workspace_structure(self) -> Dict[str, Any]:
        """Alias for get_userbench_structure for compatibility."""
        return self.get_userbench_structure()
    
    def cleanup(self, keep_outputs: bool = True):
        """
        Cleanup bench.
        
        Args:
            keep_outputs: If True, only clean temp files; if False, delete everything
        """
        if keep_outputs:
            # Only clean temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir()
        else:
            # Delete entire bench
            if self.root.exists():
                shutil.rmtree(self.root)


# Compatibility alias
ClientWorkspace = UserBench


class UserBenchManager:
    """
    Manages user benches across the server.
    
    Provides:
    - Bench creation and lookup
    - Global event routing
    - Bench cleanup
    """
    
    def __init__(self, userbenches_dir: Path):
        """
        Initialize the bench manager.
        
        Args:
            userbenches_dir: Base directory for all benches
        """
        self.userbenches_dir = userbenches_dir
        # Keep workspaces_dir as alias for compatibility
        self.workspaces_dir = userbenches_dir
        self.userbenches_dir.mkdir(parents=True, exist_ok=True)
        
        self._active_benches: Dict[str, UserBench] = {}
        # Keep _active_workspaces as alias for compatibility
        self._active_workspaces = self._active_benches
        self._event_subscribers: Dict[str, List[Callable]] = {}
    
    def get_or_create_userbench(self, user_id: str) -> UserBench:
        """
        Get or create a bench for a user.
        
        UserBenches are keyed by user_id, not run_id.
        A user has ONE bench that persists across runs.
        
        Args:
            user_id: User ID
            
        Returns:
            UserBench for this user (created if doesn't exist)
        """
        # Check if already active
        if user_id in self._active_benches:
            return self._active_benches[user_id]
        
        # Try to load from disk
        bench_path = self.userbenches_dir / user_id
        if bench_path.exists():
            bench = self._load_userbench(user_id)
            if bench:
                return bench
        
        # Create new bench
        def event_callback(event: FileEvent):
            self._route_event(user_id, event)
        
        bench = UserBench(
            user_id=user_id,
            base_path=self.userbenches_dir,
            event_callback=event_callback,
        )
        bench.initialize()
        
        self._active_benches[user_id] = bench
        logger.info(f"Created userbench for user: {user_id}")
        
        return bench
    
    def start_run_in_bench(
        self,
        user_id: str,
        run_id: str,
        plan_id: Optional[str] = None,
        plan_dir: Optional[Path] = None,
    ) -> UserBench:
        """
        Start a run in a user's bench.
        
        Gets or creates the user's bench, then sets the current run context.
        
        Args:
            user_id: User ID
            run_id: Run ID  
            plan_id: Plan being executed
            plan_dir: Source plan directory to copy files from
            
        Returns:
            UserBench ready for this run
        """
        bench = self.get_or_create_userbench(user_id)
        bench.set_current_run(run_id, plan_id, plan_dir)
        return bench
    
    # Compatibility alias for old code
    def create_userbench(
        self,
        userbench_id: str,
        plan_id: Optional[str] = None,
        plan_dir: Optional[Path] = None,
        copy_plan_files: bool = True,
    ) -> UserBench:
        """Compatibility: creates bench with userbench_id as user_id."""
        bench = self.get_or_create_userbench(userbench_id)
        if plan_dir:
            bench.set_current_run(userbench_id, plan_id, plan_dir)
        return bench
    
    # Compatibility alias
    def create_workspace(
        self,
        workspace_id: str,
        plan_id: Optional[str] = None,
        plan_dir: Optional[Path] = None,
        copy_plan_files: bool = True,
    ) -> UserBench:
        """Alias for create_userbench for compatibility."""
        return self.create_userbench(workspace_id, plan_id, plan_dir, copy_plan_files)
    
    def get_userbench(self, user_id: str) -> Optional[UserBench]:
        """Get an active bench by user ID."""
        return self._active_benches.get(user_id)
    
    # Compatibility alias
    def get_workspace(self, workspace_id: str) -> Optional[UserBench]:
        """Alias for get_userbench for compatibility."""
        return self.get_userbench(workspace_id)
    
    def _load_userbench(self, user_id: str) -> Optional[UserBench]:
        """Load a bench from disk."""
        bench_path = self.userbenches_dir / user_id
        if not bench_path.exists():
            return None
        
        # Try new format first, then old
        meta_file = bench_path / ".userbench.json"
        if not meta_file.exists():
            meta_file = bench_path / ".workspace.json"
        
        if not meta_file.exists():
            return None
        
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            def event_callback(event: FileEvent):
                self._route_event(user_id, event)
            
            bench = UserBench(
                user_id=user_id,
                base_path=self.userbenches_dir,
                event_callback=event_callback,
            )
            bench.created_at = meta.get("created_at", datetime.now().isoformat())
            bench.metadata = meta.get("metadata", {})
            bench.active_runs = meta.get("active_runs", [])
            bench.current_run_id = meta.get("current_run_id")
            bench.current_plan_id = meta.get("current_plan_id")
            
            self._active_benches[user_id] = bench
            return bench
        except Exception as e:
            logger.error(f"Failed to load userbench {user_id}: {e}")
            return None
    
    def get_or_load_userbench(self, user_id: str) -> Optional[UserBench]:
        """Get active bench or load from disk if exists."""
        # Check active first
        if user_id in self._active_benches:
            return self._active_benches[user_id]
        
        return self._load_userbench(user_id)
    
    # Compatibility alias
    def get_or_load_workspace(self, workspace_id: str) -> Optional[UserBench]:
        """Alias for get_or_load_userbench for compatibility."""
        return self.get_or_load_userbench(workspace_id)
    
    def list_userbenches(self) -> List[Dict[str, Any]]:
        """List all benches (active and on disk)."""
        benches = []
        
        if not self.userbenches_dir.exists():
            return benches
        
        for bench_dir in self.userbenches_dir.iterdir():
            if bench_dir.is_dir() and not bench_dir.name.startswith("."):
                # Try new format first, then old
                meta_file = bench_dir / ".userbench.json"
                if not meta_file.exists():
                    meta_file = bench_dir / ".workspace.json"
                
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        
                        # Count outputs
                        outputs_dir = bench_dir / "productions"
                        if not outputs_dir.exists():
                            outputs_dir = bench_dir / "outputs"
                        file_count = 0
                        total_size = 0
                        if outputs_dir.exists():
                            for f in outputs_dir.rglob("*"):
                                if f.is_file():
                                    file_count += 1
                                    total_size += f.stat().st_size
                        
                        benches.append({
                            "user_id": meta.get("user_id", bench_dir.name),
                            "userbench_id": bench_dir.name,
                            "workspace_id": bench_dir.name,  # Compatibility
                            "current_run_id": meta.get("current_run_id"),
                            "current_plan_id": meta.get("current_plan_id"),
                            "active_runs": meta.get("active_runs", []),
                            "created_at": meta.get("created_at"),
                            "is_active": bench_dir.name in self._active_benches,
                            "file_count": file_count,
                            "total_size": total_size,
                        })
                    except Exception as e:
                        logger.warning(f"Error reading userbench {bench_dir.name}: {e}")
        
        return sorted(benches, key=lambda b: b.get("created_at", ""), reverse=True)
    
    # Compatibility alias
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """Alias for list_userbenches for compatibility."""
        return self.list_userbenches()
    
    def subscribe_to_events(
        self,
        userbench_id: str,
        callback: Callable[[FileEvent], None],
    ) -> Callable[[], None]:
        """
        Subscribe to file events for a bench.
        
        Args:
            userbench_id: Bench to subscribe to
            callback: Function to call on events
            
        Returns:
            Unsubscribe function
        """
        if userbench_id not in self._event_subscribers:
            self._event_subscribers[userbench_id] = []
        
        self._event_subscribers[userbench_id].append(callback)
        
        def unsubscribe():
            if userbench_id in self._event_subscribers:
                try:
                    self._event_subscribers[userbench_id].remove(callback)
                except ValueError:
                    pass
        
        return unsubscribe
    
    def _route_event(self, userbench_id: str, event: FileEvent):
        """Route a file event to subscribers."""
        subscribers = self._event_subscribers.get(userbench_id, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event subscriber error: {e}")
    
    def delete_userbench(self, userbench_id: str):
        """Delete a bench and its contents."""
        # Remove from active
        if userbench_id in self._active_benches:
            del self._active_benches[userbench_id]
        
        # Remove subscribers
        if userbench_id in self._event_subscribers:
            del self._event_subscribers[userbench_id]
        
        # Delete from disk
        bench_path = self.userbenches_dir / userbench_id
        if bench_path.exists():
            shutil.rmtree(bench_path)
            logger.info(f"Deleted userbench: {userbench_id}")
    
    # Compatibility alias
    def delete_workspace(self, workspace_id: str):
        """Alias for delete_userbench for compatibility."""
        self.delete_userbench(workspace_id)


# Compatibility alias
WorkspaceManager = UserBenchManager


# Global userbench manager instance
_userbench_manager: Optional[UserBenchManager] = None


def get_userbench_manager() -> UserBenchManager:
    """Get or create the global userbench manager."""
    global _userbench_manager
    if _userbench_manager is None:
        from .config import get_config
        cfg = get_config()
        # Store benches in runs_dir parent or alongside
        userbenches_dir = cfg.runs_dir.parent / "userbenches"
        _userbench_manager = UserBenchManager(userbenches_dir)
    return _userbench_manager


# Compatibility alias
def get_workspace_manager() -> UserBenchManager:
    """Alias for get_userbench_manager for compatibility."""
    return get_userbench_manager()

