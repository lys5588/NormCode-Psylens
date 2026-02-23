"""
Deployment File System Tool - File operations for NormCode deployment.

A standalone file system tool that provides:
- Read/write/delete file operations
- Directory listing
- Path resolution relative to base directory
- Client workspace support for isolated outputs
- File event emission for real-time tracking
- Same interface as infra FileSystemTool
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List, Callable, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from service.workspace import ClientWorkspace

logger = logging.getLogger(__name__)


class DeploymentFileSystemTool:
    """
    A file system tool for deployment/server execution.
    
    Provides file operations within a sandboxed base directory.
    Supports:
    - Registered paths for provisions (data, scripts, etc.)
    - Client workspaces for isolated outputs per run
    - File event callbacks for real-time tracking
    """
    
    def __init__(
        self,
        base_dir: Optional[str] = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
        workspace: Optional["ClientWorkspace"] = None,
    ):
        """
        Initialize the file system tool.
        
        Args:
            base_dir: Base directory for file operations (defaults to cwd)
            log_callback: Optional callback for logging events
            workspace: Optional ClientWorkspace for isolated outputs
        """
        self.base_dir = base_dir or os.getcwd()
        self._log_callback = log_callback
        self._operation_count = 0
        
        # Client workspace for isolated outputs
        self._workspace = workspace
        
        # File event subscribers (for real-time updates)
        self._file_event_callbacks: List[Callable[[Dict], None]] = []
        
        # Registered paths for provisions (data, scripts, prompts, etc.)
        self._registered_paths: Dict[str, str] = {}
    
    def set_workspace(self, workspace: "ClientWorkspace"):
        """
        Attach a client workspace for isolated outputs.
        
        When a workspace is set, output files (writes) are redirected
        to the workspace's outputs directory, enabling per-client isolation.
        
        Args:
            workspace: ClientWorkspace instance
        """
        self._workspace = workspace
        logger.info(f"File system attached to workspace: {workspace.workspace_id}")
    
    def get_workspace(self) -> Optional["ClientWorkspace"]:
        """Get the attached workspace if any."""
        return self._workspace
    
    def get_productions_dir(self) -> Path:
        """
        Get the effective productions directory.
        
        Returns workspace productions dir if attached, otherwise base_dir/productions.
        Scripts should use this to find production output files.
        """
        if self._workspace:
            return Path(self._workspace.productions_dir)
        return Path(self.base_dir) / "productions"
    
    def list_files(self, directory: str, pattern: str = "*") -> List[Path]:
        """
        List files in a directory, checking workspace first for production paths.
        
        Args:
            directory: Directory path (relative or absolute)
            pattern: Glob pattern (e.g., "*.json", "slide_*.html")
            
        Returns:
            List of Path objects matching the pattern
        """
        # Check if this is a production path that should use workspace
        workspace_paths = ("productions/", "productions\\", "productions")
        should_check_workspace = self._workspace and (
            directory.startswith(workspace_paths) or 
            directory in workspace_paths or
            any(p in directory for p in workspace_paths)
        )
        
        if should_check_workspace:
            # Map to workspace productions directory
            if directory.startswith(("productions/", "productions\\")):
                subpath = directory.split("productions", 1)[1].lstrip("/\\")
                workspace_dir = self._workspace.productions_dir / subpath
            else:
                workspace_dir = self._workspace.productions_dir
            
            if workspace_dir.exists():
                logger.info(f"[FileSystemTool] Listing files from workspace: {workspace_dir}/{pattern}")
                return sorted(workspace_dir.glob(pattern))
        
        # Fallback to base_dir
        resolved = self._resolve_path(directory)
        if resolved.exists():
            logger.info(f"[FileSystemTool] Listing files from base_dir: {resolved}/{pattern}")
            return sorted(resolved.glob(pattern))
        
        return []
    
    def add_file_event_callback(self, callback: Callable[[Dict], None]):
        """
        Add a callback for file events.
        
        Callbacks receive dicts with:
        - event: "file:created", "file:modified", "file:deleted"
        - path: Relative path
        - absolute_path: Full path
        - size: File size (for creates/modifies)
        - timestamp: ISO timestamp
        """
        self._file_event_callbacks.append(callback)
    
    def _emit_file_event(self, event_type: str, path: str, absolute_path: str, size: int = 0, **extra):
        """Emit a file event to all subscribers."""
        event = {
            "event": f"file:{event_type}",
            "path": path,
            "absolute_path": absolute_path,
            "size": size,
            "timestamp": datetime.now().isoformat(),
            **extra,
        }
        
        for callback in self._file_event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"File event callback error: {e}")
    
    def register_path(self, name: str, path: str):
        """
        Register a named path for provision resolution.
        
        This allows provisions like data files to be resolved using
        a prefix like 'data:investor_profile.json' or by path lookup.
        
        Args:
            name: Name of the path (e.g., 'data', 'scripts', 'prompts')
            path: Absolute path to the directory
        """
        self._registered_paths[name] = path
        logger.info(f"Registered path '{name}': {path}")
    
    def get_registered_path(self, name: str) -> Optional[str]:
        """Get a registered path by name."""
        return self._registered_paths.get(name)
    
    def set_provisions_base(self, path: str):
        """
        Set the base directory for provisions.
        
        This is the directory containing subdirs like 'data', 'scripts', 'prompts'.
        Used to resolve paths like 'provision/scripts/file.py'.
        
        Args:
            path: Absolute path to the provisions base directory
        """
        self._provisions_base = path
        logger.info(f"Set provisions base: {path}")
    
    def get_provisions_base(self) -> Optional[str]:
        """Get the provisions base directory (parent of data, scripts, etc.)."""
        # Check for explicitly set provisions base
        if hasattr(self, '_provisions_base') and self._provisions_base:
            return self._provisions_base
        
        # Fallback: return the first registered path's parent
        for path in self._registered_paths.values():
            return str(Path(path).parent)
        return None
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to base_dir if not absolute.
        
        Supports:
        - Registered path prefixes like 'data:filename.json'
        - Provision paths like 'provision/scripts/file.py' or 'provisions/scripts/file.py'
        """
        logger.debug(f"[FileSystemTool] _resolve_path called with: '{path}'")
        logger.debug(f"[FileSystemTool]   base_dir: {self.base_dir}")
        logger.debug(f"[FileSystemTool]   registered_paths: {self._registered_paths}")
        
        # Check for registered path prefix (e.g., 'data:filename.json')
        if ':' in path and not Path(path).is_absolute():
            prefix, rest = path.split(':', 1)
            if prefix in self._registered_paths:
                resolved = Path(self._registered_paths[prefix]) / rest
                logger.debug(f"[FileSystemTool]   -> Resolved via prefix '{prefix}': {resolved}")
                return resolved
        
        p = Path(path)
        if not p.is_absolute():
            # Handle provision paths like 'provision/scripts/file.py' or 'provisions/scripts/file.py'
            # These need to be mapped to registered paths
            path_parts = p.parts
            logger.debug(f"[FileSystemTool]   path_parts: {path_parts}")
            
            if len(path_parts) >= 2 and path_parts[0] in ('provision', 'provisions'):
                # Extract provision type (data, scripts, prompts, etc.) and remaining path
                provision_type = path_parts[1]  # e.g., 'scripts', 'data', 'prompts'
                remaining = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
                logger.debug(f"[FileSystemTool]   Detected provision path: type='{provision_type}', remaining='{remaining}'")
                
                # Check if we have a registered path for this provision type
                if provision_type in self._registered_paths:
                    resolved = Path(self._registered_paths[provision_type])
                    if remaining:
                        resolved = resolved / remaining
                    logger.debug(f"[FileSystemTool]   Checking registered path: {resolved}, exists={resolved.exists()}")
                    if resolved.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{resolved}'")
                        return resolved.resolve()
                else:
                    logger.debug(f"[FileSystemTool]   provision_type '{provision_type}' NOT in registered_paths")
                
                # Try with variants (e.g., scripts_chinese for scripts)
                for name, reg_path in self._registered_paths.items():
                    if name.startswith(provision_type + '_') or name == provision_type:
                        possible = Path(reg_path)
                        if remaining:
                            possible = possible / remaining
                        if possible.exists():
                            logger.debug(f"Resolved provision path '{path}' -> '{possible}' via {name}")
                            return possible.resolve()
                
                # Also check provisions base if we have one
                provisions_base = self.get_provisions_base()
                logger.debug(f"[FileSystemTool]   provisions_base: {provisions_base}")
                if provisions_base:
                    # The provisions_base is the directory containing 'data', 'scripts', etc.
                    # So we just need to append the provision_type and remaining path
                    possible = Path(provisions_base) / provision_type
                    if remaining:
                        possible = possible / remaining
                    logger.debug(f"[FileSystemTool]   Checking provisions_base path: {possible}, exists={possible.exists()}")
                    if possible.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{possible}' via provisions_base")
                        return possible.resolve()
                
                # Try resolving directly relative to base_dir since path starts with provision/
                # This handles cases where base_dir is the project root and provision/ exists there
                direct_path = Path(self.base_dir) / path
                logger.debug(f"[FileSystemTool]   Checking direct path: {direct_path}, exists={direct_path.exists()}")
                if direct_path.exists():
                    logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{direct_path}' via base_dir")
                    return direct_path.resolve()
                
                # Try the alternative plural/singular form (provision vs provisions)
                alt_prefix = 'provisions' if path_parts[0] == 'provision' else 'provision'
                alt_path = Path(self.base_dir) / alt_prefix / '/'.join(path_parts[1:])
                logger.debug(f"[FileSystemTool]   Checking alt path: {alt_path}, exists={alt_path.exists()}")
                if alt_path.exists():
                    logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{alt_path}' via alt prefix")
                    return alt_path.resolve()
            
            # Try to resolve against registered paths
            for name, registered_path in self._registered_paths.items():
                possible = Path(registered_path) / path
                if possible.exists():
                    return possible.resolve()
            
            # Fall back to base_dir
            p = Path(self.base_dir) / path
            logger.debug(f"[FileSystemTool]   Fallback to base_dir path: {p}, exists={p.exists()}")
            
            # If base_dir path doesn't exist, try looking for provisions directory variations
            if not p.exists() and len(path_parts) >= 2:
                # Check if this might be a provision path without the prefix
                possible_type = path_parts[0]
                if possible_type in self._registered_paths:
                    alt = Path(self._registered_paths[possible_type]) / '/'.join(path_parts[1:])
                    logger.debug(f"[FileSystemTool]   Checking alt type path: {alt}, exists={alt.exists()}")
                    if alt.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved via type '{possible_type}': {alt}")
                        return alt.resolve()
        
        logger.debug(f"[FileSystemTool]   -> Final resolved path: {p.resolve()}")
        return p.resolve()
    
    def read(self, path: str = None, location: str = None) -> Dict[str, Any]:
        """
        Read content from a file.
        
        Args:
            path: Path to file (relative to base_dir or absolute)
            location: Alias for path (for compatibility with infra tool)
            
        Returns:
            Dict with status and content (matches infra FileSystemTool interface)
        """
        # Support both 'path' and 'location' parameter names
        filepath = path or location
        logger.info(f"[FileSystemTool] read() called with path='{path}', location='{location}'")
        
        if not filepath:
            logger.error("[FileSystemTool] read() called without path or location!")
            return {"status": "error", "message": "Either 'path' or 'location' must be provided"}
        
        self._operation_count += 1
        
        # Check if this is a production path that should be read from workspace
        # (matches the write() auto-redirect logic)
        workspace_paths = ("productions/", "productions\\", "intermediates/", "intermediates\\", "output/", "output\\")
        should_check_workspace = self._workspace and (
            filepath.startswith(workspace_paths) or any(p in filepath for p in workspace_paths)
        )
        
        # Try workspace first for production paths
        if should_check_workspace:
            try:
                # Map path prefix to category for workspace resolution
                read_path = filepath
                read_category = "productions"
                
                prefix_to_category = {
                    "productions/": "productions",
                    "productions\\": "productions",
                    "intermediates/": "productions",
                    "intermediates\\": "productions",
                    "output/": "productions",
                    "output\\": "productions",
                }
                
                for prefix, cat in prefix_to_category.items():
                    if filepath.startswith(prefix):
                        read_path = filepath[len(prefix):]
                        read_category = cat
                        break
                
                workspace_resolved = self._workspace.resolve_path(read_path, read_category)
                if workspace_resolved.exists():
                    logger.info(f"[FileSystemTool] Reading from workspace: {workspace_resolved}")
                    with open(workspace_resolved, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    self._log("file:read", {
                        "path": str(workspace_resolved),
                        "status": "completed",
                        "size": len(content),
                        "source": "workspace",
                    })
                    
                    return {"status": "success", "content": content, "source": "workspace"}
                else:
                    logger.info(f"[FileSystemTool] File not in workspace, falling back to base_dir")
            except Exception as e:
                logger.warning(f"[FileSystemTool] Workspace read failed, falling back: {e}")
        
        # Standard read from base_dir
        resolved = self._resolve_path(filepath)
        logger.info(f"[FileSystemTool] Resolved path: {resolved}")
        
        self._log("file:read", {
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            if not resolved.exists():
                logger.warning(f"File not found at {resolved}")
                return {"status": "error", "message": f"File not found at {resolved}"}
            
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._log("file:read", {
                "path": str(resolved),
                "status": "completed",
                "size": len(content),
            })
            
            return {"status": "success", "content": content}
            
        except Exception as e:
            self._log("file:read", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {"status": "error", "message": str(e)}
    
    def write(
        self,
        path: str,
        content: str,
        to_workspace: bool = None,
        category: str = "outputs",
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            path: Path to file
            content: Content to write
            to_workspace: If True and workspace is set, write to workspace instead.
                         If None (default), auto-detect based on path (productions/ → workspace)
            category: Workspace category (outputs, inputs, temp) if writing to workspace
            
        Returns:
            Result dict with status and location
        """
        self._operation_count += 1
        
        # Auto-detect workspace usage for production outputs
        # If path starts with "productions/" and workspace is set, use workspace
        if to_workspace is None and self._workspace:
            # Paths that should go to user's workspace (outputs)
            workspace_paths = ("productions/", "productions\\", "intermediates/", "intermediates\\", "output/", "output\\")
            if path.startswith(workspace_paths) or any(p in path for p in workspace_paths):
                to_workspace = True
                logger.info(f"Auto-redirecting to workspace: {path}")
        
        # Check if we should write to workspace
        if to_workspace and self._workspace:
            try:
                # Determine category and strip prefix from path
                write_path = path
                write_category = category
                
                # Map path prefixes to categories and strip them
                prefix_to_category = {
                    "productions/": "productions",
                    "productions\\": "productions",
                    "intermediates/": "productions",  # intermediates go under productions
                    "intermediates\\": "productions",
                    "output/": "productions",
                    "output\\": "productions",
                    "inputs/": "inputs",
                    "inputs\\": "inputs",
                    "provisions/": "provisions",
                    "provisions\\": "provisions",
                }
                
                for prefix, cat in prefix_to_category.items():
                    if path.startswith(prefix):
                        write_path = path[len(prefix):]
                        write_category = cat
                        break
                
                logger.info(f"Workspace write: path='{write_path}', category='{write_category}'")
                file_info = self._workspace.write_file(write_path, content, category=write_category)
                
                self._log("file:write", {
                    "path": file_info.path,
                    "status": "completed",
                    "workspace": self._workspace.workspace_id,
                })
                
                # Emit file event
                self._emit_file_event(
                    "created" if file_info else "modified",
                    file_info.path,
                    file_info.absolute_path,
                    file_info.size,
                    workspace_id=self._workspace.workspace_id,
                )
                
                return {
                    "status": "success",
                    "location": file_info.absolute_path,
                    "workspace_path": file_info.path,
                    "workspace_id": self._workspace.workspace_id,
                    "message": f"Successfully wrote to workspace: {file_info.path}",
                }
            except Exception as e:
                logger.error(f"Workspace write failed: {e}")
                return {"status": "error", "message": str(e)}
        
        # Standard write to base_dir
        resolved = self._resolve_path(path)
        
        self._log("file:write", {
            "path": str(resolved),
            "status": "started",
            "size": len(content),
        })
        
        try:
            # Create parent directories if needed
            is_new = not resolved.exists()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            
            self._log("file:write", {
                "path": str(resolved),
                "status": "completed",
            })
            
            # Emit file event
            self._emit_file_event(
                "created" if is_new else "modified",
                path,
                str(resolved),
                len(content),
            )
            
            return {
                "status": "success",
                "location": str(resolved),
                "message": f"Successfully wrote to {path}",
            }
            
        except Exception as e:
            self._log("file:write", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {
                "status": "error",
                "message": str(e),
            }
    
    def save(self, content, path: str = None, location: str = None) -> Dict[str, Any]:
        """
        Save content to a file (alias for write with swapped args).
        
        Args:
            content: Content to save (str, list, dict, or None)
                     Lists and dicts are automatically converted to JSON.
            path: Path to file
            location: Alias for path (for compatibility with infra FileSystemTool)
            
        Returns:
            Result dict
        """
        # Accept either 'path' or 'location' for compatibility
        file_path = path or location
        if not file_path:
            return {"status": "error", "message": "Either 'path' or 'location' must be provided"}
        
        if content is None:
            return {"status": "error", "message": f"Content cannot be None. Failed to save to {file_path}."}
        
        # Convert list/dict to JSON string (matching infra FileSystemTool behavior)
        if isinstance(content, (list, dict)):
            content_str = json.dumps(content, indent=2, ensure_ascii=False)
        else:
            content_str = content
        
        return self.write(file_path, content_str)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            path: Path to file
            
        Returns:
            Result dict
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        try:
            if resolved.exists():
                resolved.unlink()
                self._log("file:delete", {
                    "path": str(resolved),
                    "status": "completed",
                })
                return {"status": "success", "message": f"Deleted {path}"}
            else:
                return {"status": "error", "message": f"File not found: {path}"}
                
        except Exception as e:
            self._log("file:delete", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {"status": "error", "message": str(e)}
    
    def exists(self, path: str) -> bool:
        """Check if a file exists."""
        resolved = self._resolve_path(path)
        return resolved.exists()
    
    def list_dir(self, path: str = ".") -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            path: Path to directory
            
        Returns:
            List of file/directory info dicts
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        if not resolved.is_dir():
            return []
        
        items = []
        try:
            for entry in resolved.iterdir():
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
        
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    def mkdir(self, path: str) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            path: Path to directory
            
        Returns:
            Result dict
        """
        resolved = self._resolve_path(path)
        
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "message": f"Created directory {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        stats = {
            "base_dir": self.base_dir,
            "operation_count": self._operation_count,
        }
        
        if self._workspace:
            stats["workspace_id"] = self._workspace.workspace_id
            stats["workspace_outputs"] = str(self._workspace.outputs_dir)
        
        return stats
    
    # =========================================================================
    # Workspace Convenience Methods
    # =========================================================================
    
    def write_output(self, path: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Write a file to the workspace outputs directory.
        
        This is the primary method for plans to save output files that
        clients can access. Falls back to base_dir if no workspace.
        
        Args:
            path: Relative path within outputs
            content: File content
            metadata: Optional metadata for the file event
            
        Returns:
            Result dict with status and location
        """
        if self._workspace:
            try:
                file_info = self._workspace.write_file(path, content, category="outputs", metadata=metadata)
                
                self._emit_file_event(
                    "created",
                    file_info.path,
                    file_info.absolute_path,
                    file_info.size,
                    workspace_id=self._workspace.workspace_id,
                    metadata=metadata,
                )
                
                return {
                    "status": "success",
                    "location": file_info.absolute_path,
                    "workspace_path": file_info.path,
                    "workspace_id": self._workspace.workspace_id,
                    "url": f"/files/{self._workspace.workspace_id}/{file_info.path}",
                }
            except Exception as e:
                logger.error(f"Workspace output write failed: {e}")
                return {"status": "error", "message": str(e)}
        
        # Fallback: write to base_dir/outputs
        outputs_dir = Path(self.base_dir) / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        return self.write(f"outputs/{path}", content)
    
    def write_output_binary(self, path: str, content: bytes, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Write binary content to the workspace outputs directory.
        
        Args:
            path: Relative path within outputs
            content: Binary content
            metadata: Optional metadata
            
        Returns:
            Result dict
        """
        if self._workspace:
            try:
                file_info = self._workspace.write_binary(path, content, category="outputs", metadata=metadata)
                
                self._emit_file_event(
                    "created",
                    file_info.path,
                    file_info.absolute_path,
                    file_info.size,
                    workspace_id=self._workspace.workspace_id,
                )
                
                return {
                    "status": "success",
                    "location": file_info.absolute_path,
                    "workspace_path": file_info.path,
                    "workspace_id": self._workspace.workspace_id,
                    "url": f"/files/{self._workspace.workspace_id}/{file_info.path}",
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        # Fallback
        outputs_dir = Path(self.base_dir) / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        resolved = outputs_dir / path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        with open(resolved, "wb") as f:
            f.write(content)
        
        return {"status": "success", "location": str(resolved)}
    
    def list_outputs(self, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        List all output files in the workspace.
        
        Returns:
            List of file info dicts
        """
        if self._workspace:
            files = self._workspace.list_files(category="outputs", recursive=recursive)
            return [f.to_dict() for f in files]
        
        # Fallback: list from base_dir/outputs
        outputs_dir = Path(self.base_dir) / "outputs"
        return self.list_dir(str(outputs_dir))
    
    def get_output_url(self, path: str) -> Optional[str]:
        """
        Get the URL for accessing an output file.
        
        Args:
            path: Relative path within outputs
            
        Returns:
            URL path for the file or None
        """
        if self._workspace:
            return f"/files/{self._workspace.workspace_id}/outputs/{path}"
        return None

