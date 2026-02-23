"""
Deployment Python Interpreter Tool - Script execution for NormCode deployment.

A standalone Python interpreter tool that provides:
- Script execution in controlled environment
- Function execution from scripts
- Body injection for tool access
- Package pre-importing for controlled execution environments
- Same interface as infra PythonInterpreterTool

Package Configuration:
The tool can be configured with pre-imported packages that will be available
in the execution scope. Packages can be specified as:
- A list of package names: ["numpy", "pandas", "json"]
- A dict mapping import names to aliases: {"numpy": "np", "pandas": "pd"}
"""

import logging
import inspect
import importlib
from typing import Optional, Any, Callable, Dict, List, Union

logger = logging.getLogger(__name__)

# Type alias for package configuration
PackageConfig = Union[List[str], Dict[str, Optional[str]], None]


class DeploymentPythonInterpreterTool:
    """
    A Python interpreter tool for deployment/server execution.
    
    Executes Python scripts in a controlled environment with optional
    access to Body tools and configurable package pre-importing.
    """
    
    def __init__(
        self,
        body: Any = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
        packages: PackageConfig = None,
        timeout: int = 30,
    ):
        """
        Initialize the Python interpreter tool.
        
        Args:
            body: Optional Body instance for script access to tools
            log_callback: Optional callback for logging events
            packages: Packages to pre-import. Can be:
                - List of package names: ["numpy", "json"]
                - Dict mapping packages to aliases: {"numpy": "np", "pandas": "pd"}
            timeout: Execution timeout in seconds
        """
        self.body = body
        self._log_callback = log_callback
        self._execution_count = 0
        self._packages = packages
        self._timeout = timeout
        self._preloaded_modules: Dict[str, Any] = {}
        
        # Preload configured packages
        self._preload_packages()
    
    def _preload_packages(self):
        """Pre-import configured packages into the modules cache."""
        if not self._packages:
            return
        
        packages_with_aliases = self._normalize_packages(self._packages)
        
        for package_name, alias in packages_with_aliases.items():
            try:
                module = importlib.import_module(package_name)
                # Store with alias if provided, otherwise use package name
                key = alias if alias else package_name
                self._preloaded_modules[key] = module
                logger.debug(f"Pre-loaded package: {package_name}" + (f" as {alias}" if alias else ""))
            except ImportError as e:
                logger.warning(f"Failed to pre-import package '{package_name}': {e}")
            except Exception as e:
                logger.error(f"Error importing package '{package_name}': {e}")
    
    def _normalize_packages(self, packages: PackageConfig) -> Dict[str, Optional[str]]:
        """Normalize package config to a dict mapping names to optional aliases."""
        if packages is None:
            return {}
        if isinstance(packages, list):
            return {pkg: None for pkg in packages}
        if isinstance(packages, dict):
            return packages
        return {}
    
    def set_packages(self, packages: PackageConfig):
        """Update the packages configuration and reload."""
        self._packages = packages
        self._preloaded_modules.clear()
        self._preload_packages()
    
    def get_preloaded_modules(self) -> Dict[str, Any]:
        """Get the dict of preloaded modules for injection into execution scope."""
        return self._preloaded_modules.copy()
    
    @classmethod
    def from_config(
        cls,
        config: Any,  # PythonInterpreterToolConfig
        body: Any = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
    ) -> 'DeploymentPythonInterpreterTool':
        """
        Create a DeploymentPythonInterpreterTool from a PythonInterpreterToolConfig.
        
        Args:
            config: PythonInterpreterToolConfig instance
            body: Optional Body instance
            log_callback: Optional logging callback
            
        Returns:
            Configured DeploymentPythonInterpreterTool instance
        """
        packages = None
        if hasattr(config, 'packages') and config.packages:
            if config.packages == "from_requirements":
                # Caller should handle loading from requirements file
                packages = None
            elif isinstance(config.packages, (list, dict)):
                packages = config.packages
        
        return cls(
            body=body,
            log_callback=log_callback,
            packages=packages,
            timeout=getattr(config, 'timeout', 30),
        )
    
    def set_body(self, body: Any):
        """Set the Body instance for script access."""
        self.body = body
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _get_code_preview(self, code: str, max_lines: int = 10) -> str:
        """Get a preview of the code (first N lines)."""
        lines = code.strip().split('\n')
        if len(lines) <= max_lines:
            return code
        return '\n'.join(lines[:max_lines]) + f'\n... ({len(lines) - max_lines} more lines)'
    
    def _get_result_preview(self, result: Any, max_length: int = 500) -> str:
        """Get a preview string of the result, filtering out binary data."""
        try:
            # Filter out binary fields before preview
            sanitized = self._sanitize_for_preview(result)
            result_str = str(sanitized)
            if len(result_str) > max_length:
                return result_str[:max_length] + "..."
            return result_str
        except Exception:
            return f"<{type(result).__name__}>"
    
    def _sanitize_for_preview(self, data: Any, max_depth: int = 5) -> Any:
        """Sanitize data for preview by removing binary fields."""
        if max_depth <= 0:
            return "[...]"
        
        if data is None:
            return None
        
        if isinstance(data, bytes):
            return f"[binary: {len(data)} bytes]"
        
        if isinstance(data, (str, int, float, bool)):
            return data
        
        binary_fields = {'pptx_bytes', 'bytes', 'binary_data', 'raw_bytes', 'file_bytes', 'image_bytes'}
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key in binary_fields:
                    if isinstance(value, bytes):
                        result[key] = f"[binary: {len(value)} bytes]"
                    elif value is not None:
                        result[key] = "[binary omitted]"
                else:
                    result[key] = self._sanitize_for_preview(value, max_depth - 1)
            return result
        
        if isinstance(data, (list, tuple)):
            return [self._sanitize_for_preview(item, max_depth - 1) for item in data[:10]]  # Limit list preview
        
        return data
    
    def execute(self, script_code: str, inputs: Dict[str, Any]) -> Any:
        """
        Execute a Python script in a controlled environment.
        
        Args:
            script_code: The Python code to execute
            inputs: Dictionary of inputs to inject into the script's global scope
            
        Returns:
            The value of the 'result' variable from the script, or error dict
        """
        self._execution_count += 1
        
        self._log("python:execute", {
            "execution_id": self._execution_count,
            "code_preview": self._get_code_preview(script_code),
            "inputs": list(inputs.keys()),
            "preloaded_packages": list(self._preloaded_modules.keys()),
            "status": "started",
        })
        
        try:
            # Create execution environment
            execution_globals = inputs.copy()
            execution_globals["__builtins__"] = __builtins__
            
            # Inject preloaded modules
            execution_globals.update(self._preloaded_modules)
            
            # Inject body if available
            if self.body:
                execution_globals["body"] = self.body
            
            # Execute the script
            exec(script_code, execution_globals)
            
            # Get result
            if "result" in execution_globals:
                result = execution_globals["result"]
            else:
                result = {"status": "warning", "message": "No 'result' variable found in script."}
            
            self._log("python:execute", {
                "execution_id": self._execution_count,
                "result_type": type(result).__name__,
                "result_preview": self._get_result_preview(result),
                "status": "completed",
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            
            self._log("python:execute", {
                "execution_id": self._execution_count,
                "error": str(e),
                "status": "failed",
            })
            
            return {"status": "error", "message": str(e)}
    
    def function_execute(
        self,
        script_code: str,
        function_name: str,
        function_params: Dict[str, Any]
    ) -> Any:
        """
        Execute a specific function from a Python script.
        
        Args:
            script_code: The Python code containing the function definition
            function_name: Name of the function to execute
            function_params: Keyword arguments to pass to the function
            
        Returns:
            The return value of the function, or error dict
        """
        self._execution_count += 1
        
        self._log("python:function_execute", {
            "execution_id": self._execution_count,
            "function_name": function_name,
            "params": list(function_params.keys()) if function_params else [],
            "preloaded_packages": list(self._preloaded_modules.keys()),
            "status": "started",
        })
        
        try:
            # Create execution environment with preloaded modules
            execution_scope: Dict[str, Any] = {}
            execution_scope["__builtins__"] = __builtins__
            execution_scope.update(self._preloaded_modules)
            
            exec(script_code, execution_scope)
            
            # Find the function
            if function_name not in execution_scope:
                raise NameError(f"Function '{function_name}' not found in script.")
            
            function_to_call = execution_scope[function_name]
            
            if not callable(function_to_call):
                raise TypeError(f"'{function_name}' is not callable.")
            
            params = dict(function_params or {})
            
            # Inject body if function accepts it
            if self.body is not None:
                sig = inspect.signature(function_to_call)
                accepts_body = (
                    "body" in sig.parameters
                    or any(
                        p.kind == inspect.Parameter.VAR_KEYWORD
                        for p in sig.parameters.values()
                    )
                )
                if accepts_body and "body" not in params:
                    params["body"] = self.body
            
            result = function_to_call(**params)
            
            self._log("python:function_execute", {
                "execution_id": self._execution_count,
                "function_name": function_name,
                "result_type": type(result).__name__,
                "status": "completed",
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            
            self._log("python:function_execute", {
                "execution_id": self._execution_count,
                "function_name": function_name,
                "error": str(e),
                "status": "failed",
            })
            
            return {"status": "error", "message": str(e)}
    
    def create_function_executor(
        self,
        script_code: str,
        function_name: str
    ) -> Callable[[Dict[str, Any]], Any]:
        """
        Create a bound function executor for a script function.
        
        Args:
            script_code: The Python code containing the function
            function_name: Name of the function to create executor for
            
        Returns:
            A callable that accepts function_params dict
        """
        def executor_fn(function_params: Dict[str, Any]) -> Any:
            return self.function_execute(script_code, function_name, function_params)
        
        return executor_fn
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "execution_count": self._execution_count,
            "has_body": self.body is not None,
            "preloaded_packages": list(self._preloaded_modules.keys()),
            "timeout": self._timeout,
        }

