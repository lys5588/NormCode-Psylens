"""
Deployment GIM (Generative Image Model) Tool - Text-to-image generation for server-side NormCode execution.

A standalone image generation tool for deployment that:
- Works without WebSocket/Canvas dependencies
- Saves generated images locally (relative to the file_tool's base_dir)
- Passes around only the **relative path** — images are retrieved ad-hoc
- Supports multiple providers (Dashscope multimodal-generation, etc.)
- Configurable via direct parameters or settings file
- Provides the same interface pattern as DeploymentLLMTool
"""

import os
import json
import yaml
import logging
import time
import uuid
from pathlib import Path
from string import Template
from typing import Optional, Any, Callable, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tools.file_system_tool import DeploymentFileSystemTool

logger = logging.getLogger(__name__)

# Default Dashscope image generation endpoint
DEFAULT_IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DEFAULT_IMAGE_MODEL = "z-image-turbo"
DEFAULT_IMAGE_SIZE = "1024*1024"

# Subdirectory (relative to file_tool base_dir) where generated images are stored
DEFAULT_IMAGE_OUTPUT_DIR = "_generated_images"


class GimGenerationResult:
    """
    Result of a GIM generation call.
    
    The primary output is ``relative_path`` — the path relative to the
    file_tool's base_dir where the image was saved.  This path is what
    flows through the NormCode plan and can be handed to
    ``file_system.read()`` / ``file_system._resolve_path()`` for retrieval.
    """
    
    def __init__(
        self,
        relative_path: str = "",
        absolute_path: str = "",
        image_url: Optional[str] = None,
        prompt: str = "",
        model: str = "",
        size: str = "",
        file_size_bytes: int = 0,
        duration_ms: int = 0,
        is_mock: bool = False,
        raw_response: Optional[Dict] = None,
    ):
        self.relative_path = relative_path
        self.absolute_path = absolute_path
        self.image_url = image_url
        self.prompt = prompt
        self.model = model
        self.size = size
        self.file_size_bytes = file_size_bytes
        self.duration_ms = duration_ms
        self.is_mock = is_mock
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "image_url": self.image_url,
            "prompt": self.prompt[:200] + "..." if len(self.prompt) > 200 else self.prompt,
            "model": self.model,
            "size": self.size,
            "file_size_bytes": self.file_size_bytes,
            "duration_ms": self.duration_ms,
            "is_mock": self.is_mock,
        }
    
    def __str__(self) -> str:
        """Return the relative path — the value that flows through the plan."""
        return self.relative_path
    
    def __repr__(self) -> str:
        return f"GimGenerationResult(relative_path={self.relative_path!r}, model={self.model!r})"


class DeploymentGimTool:
    """
    A text-to-image generation tool for deployment/server execution.
    
    Generated images behave like file-system artefacts:
    - Each image is saved into ``{base_dir}/{image_output_dir}/`` on disk.
    - Only the **relative path** (e.g. ``_generated_images/img_abc123.png``)
      is returned and passed through the NormCode plan.
    - Downstream steps retrieve the image via the same path through
      the file_system tool.
    
    This tool provides image generation without Canvas/WebSocket dependencies.
    Supports:
    - Direct configuration (api_key, api_url, model)
    - Settings file configuration
    - Mock mode for testing
    - Integration with DeploymentFileSystemTool for workspace-aware storage
    """
    
    def __init__(
        self,
        model: str = DEFAULT_IMAGE_MODEL,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_IMAGE_API_URL,
        default_size: str = DEFAULT_IMAGE_SIZE,
        prompt_extend: bool = False,
        settings_path: Optional[str] = None,
        mock_mode: bool = False,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
        # --- file-like storage integration ---
        base_dir: Optional[str] = None,
        file_tool: Optional["DeploymentFileSystemTool"] = None,
        image_output_dir: str = DEFAULT_IMAGE_OUTPUT_DIR,
    ):
        """
        Initialize the deployment GIM tool.
        
        Args:
            model: Image generation model name (e.g., "z-image-turbo")
            api_key: Dashscope API key (overrides settings)
            api_url: API endpoint URL
            default_size: Default image size (e.g., "1024*1024", "1120*1440")
            prompt_extend: Whether to let the API extend/enhance the prompt
            settings_path: Path to settings.yaml
            mock_mode: Force mock mode
            log_callback: Optional callback for logging events
            base_dir: Base directory for saving images
            file_tool: DeploymentFileSystemTool whose base_dir is used
            image_output_dir: Subdirectory under base_dir for generated images
        """
        self.model = model
        self.api_url = api_url
        self.default_size = default_size
        self.prompt_extend = prompt_extend
        self._mock_mode = mock_mode
        self._log_callback = log_callback
        self._call_count = 0
        self.api_key = api_key
        self.image_output_dir = image_output_dir
        
        # File-like storage: resolve base_dir
        self._file_tool = file_tool
        if file_tool and hasattr(file_tool, 'base_dir'):
            self._base_dir = file_tool.base_dir
        elif base_dir:
            self._base_dir = base_dir
        else:
            self._base_dir = os.getcwd()
        
        if model == "demo" or mock_mode:
            self._mock_mode = True
            logger.info("GIM tool initialized in demo/mock mode")
            return
        
        # If API key not provided, try to load from settings
        if not api_key:
            self._load_from_settings(settings_path)
        
        logger.info(
            f"GIM tool initialized: model={self.model}, "
            f"base_dir={self._base_dir}, mock={self._mock_mode}"
        )
    
    # =========================================================================
    # Settings / API key loading
    # =========================================================================
    
    def _load_from_settings(self, settings_path: Optional[str]):
        """Load API key from settings file."""
        if settings_path is None:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "settings.yaml"),
                os.path.join(os.path.dirname(__file__), "..", "settings.yaml"),
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    settings_path = p
                    break
        
        if not settings_path or not os.path.exists(settings_path):
            raise RuntimeError(
                "No GIM settings file found. Please provide a settings.yaml with "
                "API key configuration."
            )
        
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
            
            for model_name, config in settings.items():
                if isinstance(config, dict):
                    # Try direct "api_key" field first
                    if config.get("api_key"):
                        self.api_key = config["api_key"]
                        logger.info(f"GIM tool got API key from settings (model: {model_name})")
                        return
                    # Fall back to env-style keys ending with _API_KEY
                    for env_key, env_value in config.items():
                        if env_key.endswith("_API_KEY"):
                            self.api_key = env_value or os.environ.get(env_key)
                            if self.api_key:
                                logger.info(f"GIM tool got API key from settings (model: {model_name})")
                                return
            
            if not self.api_key:
                raise RuntimeError(
                    "No API key found in settings for GIM tool. "
                    "Please configure 'api_key' or a key ending with '_API_KEY' in settings.yaml."
                )
                
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to load GIM tool settings: {e}") from e
    
    # =========================================================================
    # File-like storage helpers
    # =========================================================================
    
    def _get_output_dir(self) -> Path:
        """Get the absolute directory where generated images are saved."""
        out = Path(self._base_dir) / self.image_output_dir
        out.mkdir(parents=True, exist_ok=True)
        return out
    
    def _make_filename(self, ext: str = ".png") -> str:
        """Generate a unique filename for a new image."""
        ts = int(time.time())
        uid = uuid.uuid4().hex[:8]
        return f"img_{ts}_{uid}{ext}"
    
    def _save_image_bytes(self, data: bytes, filename: str) -> tuple:
        """
        Save raw image bytes to disk.
        
        If a file_tool with an active workspace is available, use its
        ``write_output_binary`` for per-client isolation.
        
        Returns:
            (relative_path, absolute_path) tuple
        """
        rel_path = f"{self.image_output_dir}/{filename}"
        
        # Prefer file_tool.write_output_binary when workspace is active
        if self._file_tool and hasattr(self._file_tool, 'write_output_binary'):
            workspace = getattr(self._file_tool, '_workspace', None) or \
                        (self._file_tool.get_workspace() if hasattr(self._file_tool, 'get_workspace') else None)
            if workspace:
                result = self._file_tool.write_output_binary(
                    f"{self.image_output_dir}/{filename}",
                    data,
                    metadata={"type": "generated_image"},
                )
                abs_path = result.get("location", "")
                ws_path = result.get("workspace_path", rel_path)
                return ws_path, abs_path
        
        # Fallback: write directly to base_dir
        out_dir = self._get_output_dir()
        abs_path = out_dir / filename
        with open(abs_path, 'wb') as f:
            f.write(data)
        
        return rel_path, str(abs_path)
    
    def resolve_image(self, relative_path: str) -> str:
        """
        Resolve a relative image path to its absolute filesystem path.
        
        Args:
            relative_path: Path as returned by GimGenerationResult.relative_path
            
        Returns:
            Absolute path string
        """
        if self._file_tool and hasattr(self._file_tool, '_resolve_path'):
            return str(self._file_tool._resolve_path(relative_path))
        
        p = Path(relative_path)
        if p.is_absolute():
            return str(p)
        return str(Path(self._base_dir) / relative_path)
    
    def image_exists(self, relative_path: str) -> bool:
        """Check whether a previously generated image still exists on disk."""
        abs_path = self.resolve_image(relative_path)
        return Path(abs_path).is_file()
    
    def list_images(self, pattern: str = "*.png") -> List[str]:
        """
        List all generated images as relative paths.
        
        Args:
            pattern: Glob pattern (default ``*.png``)
            
        Returns:
            Sorted list of relative paths
        """
        out_dir = self._get_output_dir()
        return sorted(
            f"{self.image_output_dir}/{p.name}"
            for p in out_dir.glob(pattern)
        )
    
    # =========================================================================
    # Logging helper
    # =========================================================================
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    # =========================================================================
    # Core generation
    # =========================================================================
    
    def generate(
        self,
        prompt: str,
        size: Optional[str] = None,
        model: Optional[str] = None,
        prompt_extend: Optional[bool] = None,
    ) -> GimGenerationResult:
        """
        Generate an image from a text prompt and save it locally.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size override (e.g., "1024*1024")
            model: Model override
            prompt_extend: Whether to extend prompt
            
        Returns:
            GimGenerationResult whose ``str()`` is the relative file path
        """
        self._call_count += 1
        start_time = time.time()
        
        effective_size = size or self.default_size
        effective_model = model or self.model
        effective_prompt_extend = prompt_extend if prompt_extend is not None else self.prompt_extend
        
        self._log("gim:call_started", {
            "call_id": self._call_count,
            "model": effective_model,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        })
        
        if self._mock_mode:
            result = self._generate_mock(prompt, effective_size, effective_model)
            result.duration_ms = int((time.time() - start_time) * 1000)
            
            self._log("gim:call_completed", {
                "call_id": self._call_count,
                "relative_path": result.relative_path,
                "duration_ms": result.duration_ms,
                "is_mock": True,
            })
            return result
        
        try:
            result = self._generate_api(
                prompt=prompt,
                size=effective_size,
                model=effective_model,
                prompt_extend=effective_prompt_extend,
            )
            result.duration_ms = int((time.time() - start_time) * 1000)
            
            self._log("gim:call_completed", {
                "call_id": self._call_count,
                "relative_path": result.relative_path,
                "file_size_bytes": result.file_size_bytes,
                "duration_ms": result.duration_ms,
            })
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log("gim:call_failed", {
                "call_id": self._call_count,
                "error": str(e),
                "duration_ms": int(duration * 1000),
            })
            logger.error(f"GIM generation failed: {e}")
            raise
    
    def _generate_mock(
        self,
        prompt: str,
        size: str,
        model: str,
    ) -> GimGenerationResult:
        """Generate a mock result for testing without API credentials."""
        # Tiny placeholder PNG (1x1 transparent pixel)
        placeholder_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        filename = self._make_filename()
        rel_path, abs_path = self._save_image_bytes(placeholder_png, filename)
        
        return GimGenerationResult(
            relative_path=rel_path,
            absolute_path=abs_path,
            image_url=None,
            prompt=prompt,
            model=model,
            size=size,
            file_size_bytes=len(placeholder_png),
            is_mock=True,
            raw_response={"mock": True, "prompt_preview": prompt[:100]},
        )
    
    def _generate_api(
        self,
        prompt: str,
        size: str,
        model: str,
        prompt_extend: bool,
    ) -> GimGenerationResult:
        """
        Call the Dashscope multimodal-generation API, download the result,
        and save it locally.
        """
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "prompt_extend": prompt_extend,
                "size": size,
            }
        }
        
        logger.info(f"Calling GIM API: model={model}, size={size}, prompt_len={len(prompt)}")
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        
        if response.status_code != 200:
            error_detail = response.text[:500]
            raise RuntimeError(
                f"GIM API returned status {response.status_code}: {error_detail}"
            )
        
        response_data = response.json()
        
        # Extract image URL from response
        image_url = self._extract_image_url(response_data)
        if not image_url:
            raise RuntimeError(
                f"No image URL in API response: {json.dumps(response_data, ensure_ascii=False)[:500]}"
            )
        
        # Download and save locally
        image_bytes = self._download_image_bytes(image_url)
        ext = self._guess_extension(image_url)
        filename = self._make_filename(ext)
        rel_path, abs_path = self._save_image_bytes(image_bytes, filename)
        
        logger.info(f"GIM image saved: {rel_path} ({len(image_bytes)} bytes)")
        
        return GimGenerationResult(
            relative_path=rel_path,
            absolute_path=abs_path,
            image_url=image_url,
            prompt=prompt,
            model=model,
            size=size,
            file_size_bytes=len(image_bytes),
            is_mock=False,
            raw_response=response_data,
        )
    
    def _extract_image_url(self, response_data: Dict) -> Optional[str]:
        """Extract image URL from API response."""
        output = response_data.get("output", {})
        
        # Format 1: multimodal-generation choices
        choices = output.get("choices", [])
        if choices:
            for choice in choices:
                message = choice.get("message", {})
                content = message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "image" in item:
                            return item["image"]
                elif isinstance(content, str) and content.startswith("http"):
                    return content
        
        # Format 2: legacy results
        results = output.get("results", [])
        if results:
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    return result["url"]
        
        # Format 3: direct URL
        if "result_url" in output:
            return output["result_url"]
        
        return None
    
    def _download_image_bytes(self, image_url: str) -> bytes:
        """Download image from URL and return raw bytes."""
        import requests
        
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        return response.content
    
    @staticmethod
    def _guess_extension(url: str) -> str:
        """Guess file extension from URL."""
        path_part = url.split('?')[0]
        lower = path_part.lower()
        for ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'):
            if lower.endswith(ext):
                return ext
        return '.png'
    
    # =========================================================================
    # Factory methods for paradigm integration
    # =========================================================================
    
    def create_generation_function(
        self,
        template: str,
        size: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Callable[[Dict[str, Any]], GimGenerationResult]:
        """
        Create a function that fills a template and generates an image.
        
        Args:
            template: Template string with $variable placeholders
            size: Override size
            model: Override model
            
        Returns:
            A callable that takes a variables dict and returns GimGenerationResult
        """
        def generation_fn(variables: Dict[str, Any]) -> GimGenerationResult:
            # Handle positional argument
            if "__positional__" in variables:
                prompt = str(variables["__positional__"])
            else:
                prompt = Template(template).safe_substitute(variables)
            
            return self.generate(prompt, size=size, model=model)
        
        return generation_fn
    
    def create_path_generation_function(
        self,
        template: str,
        size: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Callable[[Dict[str, Any]], str]:
        """
        Create a function that generates an image and returns just the relative path.
        
        Args:
            template: Template string with $variable placeholders
            size: Override size
            model: Override model
            
        Returns:
            A callable that returns a relative path string
        """
        gen_fn = self.create_generation_function(template, size, model)
        
        def path_fn(variables: Dict[str, Any]) -> str:
            result = gen_fn(variables)
            return result.relative_path
        
        return path_fn
    
    # =========================================================================
    # Utility methods
    # =========================================================================
    
    def set_file_tool(self, file_tool: "DeploymentFileSystemTool"):
        """Late-bind a file_system tool (e.g. after Body creation)."""
        self._file_tool = file_tool
        if hasattr(file_tool, 'base_dir'):
            self._base_dir = file_tool.base_dir
            logger.info(f"GIM tool linked to file_tool (base_dir={self._base_dir})")
    
    def set_base_dir(self, base_dir: str):
        """Update the base directory for image storage."""
        self._base_dir = base_dir
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if tool is in mock mode."""
        return self._mock_mode
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "model": self.model,
            "call_count": self._call_count,
            "is_mock": self._mock_mode,
            "base_dir": self._base_dir,
            "image_output_dir": self.image_output_dir,
            "has_file_tool": self._file_tool is not None,
        }
