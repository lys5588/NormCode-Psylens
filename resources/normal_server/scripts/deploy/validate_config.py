#!/usr/bin/env python3
"""
NormCode Server Configuration Validator

Validates all configuration and prerequisites before deployment.
Catches issues before they become runtime errors.

Usage:
    python validate_config.py                             # Basic validation
    python validate_config.py --install-dir /path/to/srv  # Validate specific install
    python validate_config.py --port 8080                 # Check port availability
    python validate_config.py --fix                       # Auto-fix what's possible
"""

import sys
import os
import socket
import shutil
from pathlib import Path

# ── Colors ────────────────────────────────────────────────────────────────

class C:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    INFO = '\033[96m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    END = '\033[0m'


def ok(msg):   print(f"  {C.OK}✓{C.END} {msg}")
def warn(msg): print(f"  {C.WARN}⚠{C.END} {msg}")
def fail(msg): print(f"  {C.FAIL}✗{C.END} {msg}")
def info(msg): print(f"  {C.INFO}→{C.END} {msg}")


# ── Validators ────────────────────────────────────────────────────────────

class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes_applied = []

    @property
    def passed(self):
        return len(self.errors) == 0


def validate_python(result: ValidationResult):
    """Check Python version and critical modules."""
    print(f"\n{C.BOLD}Python Environment{C.END}")

    # Version check
    v = sys.version_info
    if v.major >= 3 and v.minor >= 8:
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python {v.major}.{v.minor}.{v.micro} - requires 3.8+")
        result.errors.append("Python 3.8+ required")

    # Critical packages
    critical_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'yaml': 'pyyaml',
        'pydantic': 'pydantic',
        'numpy': 'numpy',
    }

    for import_name, pip_name in critical_packages.items():
        try:
            mod = __import__(import_name)
            version = getattr(mod, '__version__', 'unknown')
            ok(f"{pip_name} ({version})")
        except ImportError:
            fail(f"{pip_name} - NOT INSTALLED")
            result.errors.append(f"Missing required package: {pip_name}")

    # Multipart (required for file uploads)
    try:
        import multipart
        ok("python-multipart (required for file uploads)")
    except ImportError:
        fail("python-multipart - NOT INSTALLED (file upload will fail!)")
        result.errors.append("Missing python-multipart - zip deploy will fail")

    # Optional packages
    optional = {
        'openai': 'openai',
        'dashscope': 'dashscope',
        'anthropic': 'anthropic',
    }

    for import_name, pip_name in optional.items():
        try:
            __import__(import_name)
            ok(f"{pip_name} {C.DIM}(optional LLM provider){C.END}")
        except ImportError:
            info(f"{pip_name} - not installed {C.DIM}(optional){C.END}")


def validate_directories(result: ValidationResult, install_dir: Path, auto_fix: bool = False):
    """Check required directories exist and are writable."""
    print(f"\n{C.BOLD}Directory Structure{C.END}")

    required_dirs = [
        ("Server root", install_dir),
        ("Data directory", install_dir / "data"),
        ("Plans directory", install_dir / "data" / "plans"),
        ("Runs directory", install_dir / "data" / "runs"),
        ("Config directory", install_dir / "data" / "config"),
    ]

    required_files = [
        ("launch.py", install_dir / "launch.py"),
        ("server.py", install_dir / "server.py"),
        ("requirements.txt", install_dir / "requirements.txt"),
    ]

    for name, path in required_dirs:
        if path.exists():
            if os.access(str(path), os.W_OK):
                ok(f"{name}: {path}")
            else:
                fail(f"{name}: {path} (NOT WRITABLE)")
                result.errors.append(f"{name} not writable: {path}")
        elif auto_fix:
            path.mkdir(parents=True, exist_ok=True)
            ok(f"{name}: {path} (CREATED)")
            result.fixes_applied.append(f"Created directory: {path}")
        else:
            fail(f"{name}: {path} (NOT FOUND)")
            result.errors.append(f"{name} not found: {path}")

    for name, path in required_files:
        if path.exists():
            ok(f"{name}: {path}")
        else:
            fail(f"{name}: NOT FOUND at {path}")
            result.errors.append(f"Required file missing: {name}")


def validate_settings(result: ValidationResult, install_dir: Path):
    """Check LLM settings file."""
    print(f"\n{C.BOLD}LLM Settings{C.END}")

    settings_file = install_dir / "data" / "config" / "settings.yaml"
    template_file = install_dir / "data" / "config" / "settings.yaml.template"

    if not settings_file.exists():
        if template_file.exists():
            warn(f"Settings file not found - using template")
            warn(f"  Copy and edit: cp {template_file} {settings_file}")
            result.warnings.append("No settings.yaml - only demo mode available")
        else:
            warn(f"No settings file or template found")
            result.warnings.append("No LLM settings - only demo mode available")
        return

    try:
        import yaml
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        if not settings:
            warn("Settings file is empty")
            result.warnings.append("Settings file is empty")
            return

        ok(f"Settings file: {settings_file}")

        # Check each model config
        configured = 0
        for key, value in settings.items():
            if key == 'BASE_URL':
                ok(f"Base URL: {value}")
                continue

            if not isinstance(value, dict):
                continue

            api_key = value.get('api_key', '')
            model = value.get('model', key)
            is_mock = value.get('is_mock', False)

            if is_mock:
                ok(f"  {key}: demo/mock mode")
                configured += 1
            elif api_key and 'your-' not in api_key and 'here' not in api_key:
                ok(f"  {key}: configured (model={model})")
                configured += 1
            else:
                info(f"  {key}: no API key set")

        if configured == 0:
            warn("No LLM models configured - only demo mode available")
            result.warnings.append("No LLM models configured")
        else:
            ok(f"{configured} model(s) configured")

    except ImportError:
        fail("Cannot validate settings - pyyaml not installed")
        result.errors.append("pyyaml required for settings validation")
    except Exception as e:
        fail(f"Error reading settings: {e}")
        result.errors.append(f"Settings file error: {e}")


def validate_port(result: ValidationResult, port: int):
    """Check if the target port is available."""
    print(f"\n{C.BOLD}Network{C.END}")

    # Check if port is in valid range
    if not (1 <= port <= 65535):
        fail(f"Invalid port: {port}")
        result.errors.append(f"Invalid port number: {port}")
        return

    # Try to bind
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('0.0.0.0', port))
            ok(f"Port {port}: available")
    except OSError:
        # Port in use - check if it's our server
        try:
            import urllib.request
            import json
            resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3)
            data = json.loads(resp.read())
            if data.get('status') == 'healthy':
                ok(f"Port {port}: in use by NormCode server (already running)")
            else:
                warn(f"Port {port}: in use by another service")
                result.warnings.append(f"Port {port} already in use")
        except Exception:
            warn(f"Port {port}: in use by another service")
            result.warnings.append(f"Port {port} in use - server may fail to start")


def validate_disk_space(result: ValidationResult, install_dir: Path):
    """Check available disk space."""
    print(f"\n{C.BOLD}Disk Space{C.END}")

    try:
        total, used, free = shutil.disk_usage(str(install_dir))
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        used_pct = (used / total) * 100

        if free_gb > 5:
            ok(f"Free space: {free_gb:.1f} GB ({used_pct:.0f}% used)")
        elif free_gb > 1:
            warn(f"Free space: {free_gb:.1f} GB ({used_pct:.0f}% used) - getting low")
            result.warnings.append(f"Low disk space: {free_gb:.1f} GB free")
        else:
            fail(f"Free space: {free_gb:.1f} GB ({used_pct:.0f}% used) - CRITICAL")
            result.errors.append(f"Critical disk space: {free_gb:.1f} GB free")

        # Check data directory size
        data_dir = install_dir / "data"
        if data_dir.exists():
            data_size = sum(
                f.stat().st_size for f in data_dir.rglob('*') if f.is_file()
            )
            data_mb = data_size / (1024 ** 2)
            ok(f"Data directory size: {data_mb:.1f} MB")
    except Exception as e:
        warn(f"Cannot check disk space: {e}")


def validate_permissions(result: ValidationResult, install_dir: Path):
    """Check file permissions."""
    print(f"\n{C.BOLD}Permissions{C.END}")

    # Check if running as root (not recommended)
    if os.geteuid() == 0:
        warn("Running as root - consider using a dedicated user")
        result.warnings.append("Running as root is not recommended for production")
    else:
        ok(f"Running as user: {os.getenv('USER', 'unknown')}")

    # Check start.sh is executable
    start_sh = install_dir / "start.sh"
    if start_sh.exists():
        if os.access(str(start_sh), os.X_OK):
            ok("start.sh is executable")
        else:
            warn("start.sh is not executable - run: chmod +x start.sh")
            result.warnings.append("start.sh is not executable")

    # Check data directory ownership
    data_dir = install_dir / "data"
    if data_dir.exists():
        stat = data_dir.stat()
        if stat.st_uid == os.getuid():
            ok(f"Data directory owned by current user")
        else:
            warn(f"Data directory owned by UID {stat.st_uid}, not current user")
            result.warnings.append("Data directory ownership mismatch")


def validate_infra(result: ValidationResult, install_dir: Path):
    """Check NormCode infra module."""
    print(f"\n{C.BOLD}NormCode Runtime{C.END}")

    infra_dir = install_dir / "infra"
    if infra_dir.exists():
        ok(f"infra/ directory found (built package)")

        # Check key components
        components = [
            ("_core", infra_dir / "_core"),
            ("_agent", infra_dir / "_agent"),
            ("_orchest", infra_dir / "_orchest"),
            ("_states", infra_dir / "_states"),
        ]

        for name, path in components:
            if path.exists():
                ok(f"  {name}/")
            else:
                fail(f"  {name}/ - MISSING")
                result.errors.append(f"Missing infra component: {name}")
    else:
        # Running from source - check if project root has infra
        project_root = install_dir.parent.parent
        if (project_root / "infra").exists():
            ok(f"infra/ found at project root: {project_root}")
        else:
            fail("infra/ not found - NormCode runtime missing!")
            result.errors.append("NormCode runtime (infra/) not found")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate NormCode server configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--install-dir', '-d',
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help='Installation directory to validate'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port to check (default: 8080)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Auto-fix issues where possible (create directories, etc.)'
    )

    args = parser.parse_args()
    install_dir = args.install_dir.resolve()

    print(f"\n{C.BOLD}{'='*56}{C.END}")
    print(f"{C.BOLD}  NormCode Server Configuration Validator{C.END}")
    print(f"{C.BOLD}{'='*56}{C.END}")
    print(f"\n  Checking: {install_dir}\n")

    result = ValidationResult()

    # Run all validations
    validate_python(result)
    validate_directories(result, install_dir, auto_fix=args.fix)
    validate_settings(result, install_dir)
    validate_infra(result, install_dir)
    validate_port(result, args.port)
    validate_disk_space(result, install_dir)

    # Only check permissions on Linux
    if sys.platform != 'win32':
        validate_permissions(result, install_dir)

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{C.BOLD}{'='*56}{C.END}")

    if result.fixes_applied:
        print(f"\n{C.OK}Fixes Applied:{C.END}")
        for fix in result.fixes_applied:
            print(f"  {C.OK}✓{C.END} {fix}")

    if result.warnings:
        print(f"\n{C.WARN}Warnings ({len(result.warnings)}):{C.END}")
        for w in result.warnings:
            print(f"  {C.WARN}⚠{C.END} {w}")

    if result.errors:
        print(f"\n{C.FAIL}Errors ({len(result.errors)}):{C.END}")
        for e in result.errors:
            print(f"  {C.FAIL}✗{C.END} {e}")
        print(f"\n{C.FAIL}VALIDATION FAILED{C.END} - fix errors before deploying\n")
        sys.exit(1)
    else:
        print(f"\n{C.OK}VALIDATION PASSED{C.END} ✓\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

