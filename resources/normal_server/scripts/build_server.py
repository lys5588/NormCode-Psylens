#!/usr/bin/env python3
"""
NormCode Server Packager

Creates a standalone, deployable server package that can be run on any machine
without needing the full normCode repository.

Usage:
    python scripts/build_server.py                    # Create package for both platforms
    python scripts/build_server.py --linux            # Create package for Linux only
    python scripts/build_server.py --win              # Create package for Windows only
    python scripts/build_server.py -o ~/deploy        # Custom output directory
    python scripts/build_server.py --with-plans       # Include plans from data/plans/
    python scripts/build_server.py --zip              # Also create a .zip archive
"""

import sys
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Calculate paths
SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SERVER_DIR.parent.parent  # normCode root

# Import version info
sys.path.insert(0, str(SERVER_DIR))
from version import __version__

# Directories to copy from server
SERVER_COMPONENTS = [
    "version.py",
    "server.py",
    "launch.py",
    "requirements.txt",
    "routes",
    "service",
    "tools",
    "static",
    "mock_users",
    "resources",
    "scripts",
]

# Directories from infra/ that are needed (the whole infra folder)
INFRA_COMPONENTS = [
    "infra",
]

# Files/dirs to exclude
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".DS_Store",
    "*.log",
    "node_modules",
    "inspector",
    "settings.yaml",
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded."""
    name = path.name
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    return False


def copy_tree_filtered(src: Path, dst: Path, verbose: bool = False):
    """Copy directory tree, excluding unwanted files."""
    if not src.exists():
        return 0
    
    copied = 0
    dst.mkdir(parents=True, exist_ok=True)
    
    for item in src.iterdir():
        if should_exclude(item):
            continue
        
        dst_item = dst / item.name
        
        if item.is_dir():
            copied += copy_tree_filtered(item, dst_item, verbose)
        else:
            shutil.copy2(item, dst_item)
            if verbose:
                print(f"  + {dst_item.relative_to(dst.parent.parent)}")
            copied += 1
    
    return copied


def build_server_package(
    output_dir: Path,
    include_plans: bool = False,
    include_config: bool = False,
    create_zip: bool = False,
    verbose: bool = True,
    target_platform: str = "both"
) -> Path:
    """
    Build a standalone server package.
    
    Args:
        output_dir: Where to create the package
        include_plans: Include plans from data/plans/
        include_config: Include config from data/config/
        create_zip: Also create a .zip archive
        verbose: Print progress
        target_platform: Target platform - "linux", "win", or "both"
    
    Returns:
        Path to created package
    """
    # Determine package name based on platform
    if target_platform == "linux":
        package_name = "normcode-server-linux"
    elif target_platform == "win":
        package_name = "normcode-server-win"
    else:
        package_name = "normcode-server"
    
    package_dir = output_dir / package_name
    
    # Clean existing
    if package_dir.exists():
        if verbose:
            print(f"Removing existing: {package_dir}")
        shutil.rmtree(package_dir)
    
    package_dir.mkdir(parents=True)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Building NormCode Server Package")
        print(f"{'='*60}")
        print(f"Source: {SERVER_DIR}")
        print(f"Output: {package_dir}")
        print(f"Target Platform: {target_platform}")
        print(f"{'='*60}\n")
    
    total_files = 0
    
    # 0. Build inspector React bundle (run-inspector.js/css → static/dist/)
    inspector_dir = SERVER_DIR / "inspector"
    if inspector_dir.exists() and (inspector_dir / "package.json").exists():
        if verbose:
            print("[0/6] Building inspector React bundle...")
        
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        
        # Install deps if node_modules missing
        if not (inspector_dir / "node_modules").exists():
            if verbose:
                print("  Installing npm dependencies...")
            subprocess.run(
                [npm_cmd, "install"],
                cwd=str(inspector_dir),
                check=True,
                capture_output=not verbose,
            )
        
        # Build
        result = subprocess.run(
            [npm_cmd, "run", "build"],
            cwd=str(inspector_dir),
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            if verbose:
                print("  + static/dist/run-inspector.js")
                print("  + static/dist/run-inspector.css")
        else:
            print(f"  WARNING: Inspector build failed (exit {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().splitlines()[-5:]:
                    print(f"    {line}")
            print("  The packaged server will fall back to vanilla JS inspector.")
    else:
        if verbose:
            print("[0/6] Inspector source not found — skipping React build")
    
    # 1. Copy server components
    if verbose:
        print("\n[1/6] Copying server components...")
    
    for component in SERVER_COMPONENTS:
        src = SERVER_DIR / component
        if not src.exists():
            if verbose:
                print(f"  - Skipping (not found): {component}")
            continue
        
        dst = package_dir / component
        
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            total_files += 1
            if verbose:
                print(f"  + {component}")
        else:
            copied = copy_tree_filtered(src, dst, verbose=False)
            total_files += copied
            if verbose:
                print(f"  + {component}/ ({copied} files)")
    
    # 1b. Create tools/settings.yaml.example (real settings.yaml is excluded)
    tools_settings_example = """\
# NormCode Server – LLM / GIM Settings
# ======================================
# Copy this file to  tools/settings.yaml  and fill in your API keys.
#
#   cp tools/settings.yaml.example tools/settings.yaml
#
# The server loads this file automatically on startup.
# !! DO NOT commit the real settings.yaml – it contains secrets !!

# Base URL used by all models below (unless overridden per-model)
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

# ---- Alibaba DashScope models ----
qwen-plus:
  DASHSCOPE_API_KEY: your-dashscope-api-key-here

qwen-turbo-latest:
  DASHSCOPE_API_KEY: your-dashscope-api-key-here

# Alternative format (also supported):
# qwen-turbo-latest:
#   api_key: your-dashscope-api-key-here

# ---- OpenAI models ----
# gpt-4o:
#   api_key: your-openai-key-here
#   base_url: https://api.openai.com/v1
"""
    tools_example_path = package_dir / "tools" / "settings.yaml.example"
    tools_example_path.parent.mkdir(parents=True, exist_ok=True)
    tools_example_path.write_text(tools_settings_example, encoding='utf-8')
    total_files += 1
    if verbose:
        print(f"\n  ** settings.yaml excluded from package (contains secrets)")
        print(f"  + tools/settings.yaml.example  ← copy to tools/settings.yaml on the server")

    # 2. Copy infra components
    if verbose:
        print("\n[2/6] Copying infra (NormCode runtime)...")
    
    for infra_path in INFRA_COMPONENTS:
        src = PROJECT_ROOT / infra_path
        if not src.exists():
            if verbose:
                print(f"  - Skipping (not found): {infra_path}")
            continue
        
        # Preserve directory structure
        dst = package_dir / infra_path
        copied = copy_tree_filtered(src, dst, verbose=False)
        total_files += copied
        if verbose:
            print(f"  + {infra_path}/ ({copied} files)")
    
    # 3. Create data directories
    if verbose:
        print("\n[3/6] Setting up data directories...")
    
    data_dir = package_dir / "data"
    (data_dir / "plans").mkdir(parents=True, exist_ok=True)
    (data_dir / "runs").mkdir(parents=True, exist_ok=True)
    (data_dir / "config").mkdir(parents=True, exist_ok=True)
    (data_dir / "crashes").mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"  + data/plans/")
        print(f"  + data/runs/")
        print(f"  + data/config/")
        print(f"  + data/crashes/  (watchdog crash reports)")
    
    # Include plans if requested
    if include_plans:
        src_plans = SERVER_DIR / "data" / "plans"
        if src_plans.exists():
            copied = copy_tree_filtered(src_plans, data_dir / "plans", verbose=False)
            total_files += copied
            if verbose:
                print(f"  + Included {copied} plan files")
    
    # Include config if requested
    if include_config:
        src_config = SERVER_DIR / "data" / "config"
        if src_config.exists():
            copied = copy_tree_filtered(src_config, data_dir / "config", verbose=False)
            total_files += copied
            if verbose:
                print(f"  + Included {copied} config files")
    
    # 4. Copy deployment infrastructure (Linux only)
    if target_platform in ("linux", "both"):
        if verbose:
            print("\n[4/6] Copying deployment scripts...")
        
        deploy_src = SERVER_DIR / "scripts" / "deploy"
        deploy_dst = package_dir / "scripts" / "deploy"
        
        if deploy_src.exists():
            copied = copy_tree_filtered(deploy_src, deploy_dst, verbose=False)
            total_files += copied
            if verbose:
                print(f"  + scripts/deploy/ ({copied} files)")
                print(f"    Includes: systemd service, nginx config, deploy script,")
                print(f"              health check, log rotation, config validator")
        else:
            if verbose:
                print(f"  - deploy/ not found (skipped)")
    else:
        if verbose:
            print("\n[4/6] Deployment scripts (SKIPPED - Windows target)")
    
    # 5. Create helper files
    if verbose:
        print("\n[5/6] Creating helper files...")
    
    # Create settings template
    settings_template = """# NormCode LLM Settings
# Configure your LLM providers here

# Default base URL (for Alibaba DashScope)
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

# Alibaba Qwen
qwen-plus:
  model: qwen-plus
  api_key: your-dashscope-api-key-here

qwen-turbo-latest:
  model: qwen-turbo-latest
  api_key: your-dashscope-api-key-here

# OpenAI GPT
gpt-4o:
  model: gpt-4o
  api_key: your-openai-key-here
  base_url: https://api.openai.com/v1

# Anthropic Claude
claude-3-sonnet:
  model: claude-3-sonnet-20240229
  api_key: your-anthropic-key-here
  base_url: https://api.anthropic.com/v1

# Demo mode (mock responses, no API needed)
demo:
  model: demo
  is_mock: true
"""
    
    settings_file = data_dir / "config" / "settings.yaml.template"
    settings_file.write_text(settings_template, encoding='utf-8')
    total_files += 1
    if verbose:
        print(f"  + data/config/settings.yaml.template")
    
    # Create startup script for Linux (if target is linux or both)
    if target_platform in ("linux", "both"):
        startup_sh = """#!/bin/bash
# NormCode Server Startup Script
# Usage:
#   ./start.sh                  # Start normally
#   ./start.sh --watchdog       # Start with auto-restart watchdog (recommended for production)
#   ./start.sh --port 9000      # Custom port

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Use virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Copy settings template if settings don't exist
if [ ! -f "data/config/settings.yaml" ]; then
    if [ -f "data/config/settings.yaml.template" ]; then
        cp data/config/settings.yaml.template data/config/settings.yaml
        echo "Created settings.yaml from template"
        echo "Edit data/config/settings.yaml to add your API keys"
    fi
fi

# Warn if tools/settings.yaml is missing (LLM/GIM won't work without it)
if [ ! -f "tools/settings.yaml" ]; then
    echo ""
    echo "WARNING: tools/settings.yaml not found!"
    echo "  LLM and image-generation calls will fail without API keys."
    echo "  Create it from the example:"
    echo "    cp tools/settings.yaml.example tools/settings.yaml"
    echo "  Then edit tools/settings.yaml and add your API keys."
    echo ""
fi

# Start server (pass all arguments through, e.g. --watchdog --port 9000)
echo "Starting NormCode Server..."
python3 launch.py --quick "$@"
"""
        
        startup_file = package_dir / "start.sh"
        # Write with Unix line endings (LF) for Linux compatibility
        startup_file.write_bytes(startup_sh.encode('utf-8').replace(b'\r\n', b'\n'))
        total_files += 1
        if verbose:
            print(f"  + start.sh")
    
    # Create startup script for Windows (if target is win or both)
    if target_platform in ("win", "both"):
        startup_bat = """@echo off
REM NormCode Server Startup Script
REM Usage:
REM   start.bat                  Start normally
REM   start.bat --watchdog       Start with auto-restart watchdog (recommended)
REM   start.bat --port 9000      Custom port

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Install dependencies if needed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Copy settings template if settings don't exist
if not exist "data\\config\\settings.yaml" (
    copy "data\\config\\settings.yaml.template" "data\\config\\settings.yaml"
    echo Created settings.yaml from template
    echo Edit data\\config\\settings.yaml to add your API keys
)

REM Warn if tools\settings.yaml is missing (LLM/GIM won't work without it)
if not exist "tools\\settings.yaml" (
    echo.
    echo WARNING: tools\settings.yaml not found!
    echo   LLM and image-generation calls will fail without API keys.
    echo   Create it from the example:
    echo     copy tools\settings.yaml.example tools\settings.yaml
    echo   Then edit tools\settings.yaml and add your API keys.
    echo.
)

REM Start server (pass all arguments through, e.g. --watchdog --port 9000)
echo Starting NormCode Server...
python launch.py --quick %*
"""
        
        startup_bat_file = package_dir / "start.bat"
        # Write with Windows line endings (CRLF) for Windows compatibility
        startup_bat_file.write_bytes(startup_bat.encode('utf-8').replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n'))
        total_files += 1
        if verbose:
            print(f"  + start.bat")
    
    # Create platform-specific README
    platform_label = {
        "linux": "Linux/macOS",
        "win": "Windows",
        "both": "All Platforms"
    }.get(target_platform, "All Platforms")
    
    # Quick start section based on platform
    if target_platform == "linux":
        quick_start = """## Quick Start

```bash
chmod +x start.sh
./start.sh
```

For production (with auto-restart on crash):
```bash
./start.sh --watchdog
```

Or manually:
```bash
pip3 install -r requirements.txt
python3 launch.py --quick          # basic start
python3 launch.py --watchdog       # with crash protection
```"""
        startup_scripts = "├── start.sh            # Linux startup script"
        service_section = """
## Automated Deployment (Recommended)

Use the included deployment script for a complete setup with systemd, Nginx, and monitoring:

```bash
chmod +x scripts/deploy/deploy.sh
./scripts/deploy/deploy.sh
```

This will automatically:
- Set up a Python virtual environment
- Install all dependencies
- Configure systemd service with watchdog (auto-restart on boot + crash)
- Configure Nginx reverse proxy (with proper file upload limits)
- Set up log rotation
- Run health checks

### Manual Service Setup

If you prefer manual setup, create `/etc/systemd/system/normcode.service`:

```ini
[Unit]
Description=NormCode Deployment Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/normcode-server
ExecStart=/path/to/normcode-server/venv/bin/python3 launch.py --watchdog --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable normcode
sudo systemctl start normcode
```

### Health Monitoring

```bash
# Cross-platform health check (Python)
python3 launch.py --health
python3 scripts/health_check.py --verbose

# Bash health check (Linux only)
./scripts/deploy/healthcheck.sh --verbose

# Analyze crash history
python3 launch.py --crashes
python3 scripts/analyze_crashes.py --detail

# Cron job (every 5 minutes, auto-restart on failure)
*/5 * * * * /path/to/normcode-server/scripts/deploy/healthcheck.sh --restart --alert
```

### Configuration Validation

```bash
python3 scripts/deploy/validate_config.py --fix
```
"""
    elif target_platform == "win":
        quick_start = """## Quick Start

```cmd
start.bat
```

For production (with auto-restart on crash):
```cmd
start.bat --watchdog
```

Or manually:
```cmd
pip install -r requirements.txt
python launch.py --quick          &REM basic start
python launch.py --watchdog       &REM with crash protection
```"""
        startup_scripts = "├── start.bat           # Windows startup script"
        service_section = """
## Running as a Windows Service

Use tools like NSSM (Non-Sucking Service Manager) to install as a Windows service:

```cmd
nssm install NormCodeServer "C:\\path\\to\\python.exe" "C:\\path\\to\\normcode-server\\launch.py" "--watchdog"
nssm set NormCodeServer AppDirectory "C:\\path\\to\\normcode-server"
nssm start NormCodeServer
```

### Health Monitoring

```cmd
python launch.py --health
python launch.py --crashes
python scripts\\health_check.py --verbose
python scripts\\analyze_crashes.py --detail
```
"""
    else:
        quick_start = """## Quick Start

### Linux/macOS
```bash
chmod +x start.sh
./start.sh                 # basic start
./start.sh --watchdog      # with crash protection (recommended)
```

### Windows
```cmd
start.bat                  &REM basic start
start.bat --watchdog       &REM with crash protection (recommended)
```

### Manual Start
```bash
pip install -r requirements.txt
python launch.py --quick          # basic start
python launch.py --watchdog       # with crash protection
```"""
        startup_scripts = """├── start.sh            # Linux startup script
├── start.bat           # Windows startup script"""
        service_section = """
## Automated Deployment (Linux - Recommended)

Use the included deployment script for a complete setup:

```bash
chmod +x scripts/deploy/deploy.sh
./scripts/deploy/deploy.sh
```

This handles: venv setup, dependencies, systemd with watchdog, Nginx, log rotation, and health checks.

See `scripts/deploy/` for individual config files (systemd, nginx, logrotate, healthcheck).

### Manual Service Setup

Create `/etc/systemd/system/normcode.service`:

```ini
[Unit]
Description=NormCode Deployment Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/normcode-server
ExecStart=/path/to/normcode-server/venv/bin/python3 launch.py --watchdog --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable normcode
sudo systemctl start normcode
```

### Health Monitoring & Crash Analysis

```bash
python launch.py --health          # quick health check
python launch.py --crashes         # analyze crash history
python scripts/health_check.py -v  # detailed health check
python scripts/analyze_crashes.py  # crash report analysis
```
"""
    
    readme = f"""# NormCode Deployment Server

Standalone server package for executing NormCode plans.

**Target Platform:** {platform_label}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{quick_start}

## Configuration – LLM / GIM API Keys

The server needs a `tools/settings.yaml` file with your API keys to call
LLM and image-generation models.  A ready-made example is included:

```bash
cp tools/settings.yaml.example tools/settings.yaml
# Then edit tools/settings.yaml and fill in your real API keys
```

> **Note:** `settings.yaml` is intentionally excluded from the package to
> avoid leaking secrets.  You must create it on each deployment target.

An older config template is also available at `data/config/settings.yaml.template`.

## Accessing the Server

- **Dashboard**: http://localhost:8080/dashboard
- **API Docs**: http://localhost:8080/docs
- **API Base**: http://localhost:8080

## Deploying Plans

1. Via Web UI: Open dashboard → Deploy → Upload zip
2. Via API: POST /plans/deploy with zip file
3. Via directory: Copy plan folder to data/plans/

## Directory Structure

```
{package_name}/
├── launch.py           # Interactive launcher (--watchdog, --health, --crashes)
├── server.py           # FastAPI server
{startup_scripts}
├── requirements.txt    # Python dependencies
├── infra/              # NormCode runtime
├── routes/             # API endpoints
├── service/            # Business logic
├── static/             # Web dashboard
├── tools/              # Deployment tools
│   └── settings.yaml.example  # ← copy to settings.yaml & add API keys
├── scripts/
│   ├── watchdog.py            # Process guardian with auto-restart
│   ├── health_check.py        # Cross-platform health check (Python)
│   ├── analyze_crashes.py     # Crash report analyzer
│   ├── monitor.py             # Real-time TUI dashboard
│   └── deploy/                # Deployment infrastructure
│       ├── deploy.sh           # Automated deployment script
│       ├── normcode.service    # systemd service template (uses watchdog)
│       ├── normcode-nginx.conf # Nginx config template
│       ├── healthcheck.sh      # Health monitoring script (bash)
│       ├── validate_config.py  # Pre-deploy config checker
│       └── logrotate-normcode  # Log rotation config
└── data/
    ├── config/         # Server settings
    │   └── settings.yaml
    ├── plans/          # Deployed plans
    ├── runs/           # Execution data
    └── crashes/        # Crash reports (auto-generated by watchdog)
```

## Server Watchdog (Crash Protection)

The watchdog monitors the server process and **automatically restarts** it on crash.
Recommended for all production deployments.

```bash
# Start with watchdog protection
python launch.py --watchdog

# Or via startup script
./start.sh --watchdog
```

Features:
- Health checks via HTTP every 10 seconds
- Auto-restart with exponential backoff on repeated failures
- Crash reports saved to `data/crashes/` with system diagnostics
- Works on both Linux and Windows

```bash
# Check server health
python launch.py --health

# Analyze crash history
python launch.py --crashes

# Or run scripts directly
python scripts/health_check.py --verbose
python scripts/analyze_crashes.py --detail
```
{service_section}"""
    
    readme_file = package_dir / "README.md"
    readme_file.write_text(readme, encoding='utf-8')
    total_files += 1
    if verbose:
        print(f"  + README.md")
    
    # Summary
    if verbose:
        print(f"\n{'='*60}")
        print(f"Package created: {package_dir}")
        print(f"Total files: {total_files}")
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024*1024):.1f} MB"
        else:
            size_str = f"{total_size / 1024:.1f} KB"
        print(f"Total size: {size_str}")
        print(f"{'='*60}\n")
    
    # Create zip if requested
    if create_zip:
        # Include version and unique timestamp in zip filename
        # e.g. normcode-server-1.0.1-alpha-20260219-1430.zip
        timestamp_code = datetime.now().strftime('%Y%m%d-%H%M')
        zip_name = f"{package_name}-{__version__}-{timestamp_code}"
        zip_path = output_dir / f"{zip_name}.zip"
        if verbose:
            print(f"Creating zip archive: {zip_path}")
        shutil.make_archive(str(output_dir / zip_name), 'zip', output_dir, package_name)
        if verbose:
            zip_size = zip_path.stat().st_size
            if zip_size > 1024 * 1024:
                zip_size_str = f"{zip_size / (1024*1024):.1f} MB"
            else:
                zip_size_str = f"{zip_size / 1024:.1f} KB"
            print(f"Zip created: {zip_path} ({zip_size_str})")
    
    return package_dir


def main():
    parser = argparse.ArgumentParser(
        description="Build NormCode Server deployment package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build_server.py                    # Build for both platforms
  python scripts/build_server.py --linux            # Build for Linux only
  python scripts/build_server.py --win              # Build for Windows only
  python scripts/build_server.py -o ~/deploy        # Custom output directory
  python scripts/build_server.py --with-plans       # Include deployed plans
  python scripts/build_server.py --zip              # Also create .zip archive
  python scripts/build_server.py --linux --zip      # Linux package with zip
        """
    )
    
    # Platform selection (mutually exclusive group)
    platform_group = parser.add_mutually_exclusive_group()
    platform_group.add_argument(
        '--linux',
        action='store_true',
        help='Build package for Linux/macOS only'
    )
    platform_group.add_argument(
        '--win',
        action='store_true',
        help='Build package for Windows only'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=SERVER_DIR / "dist",
        help='Output directory (default: ./dist/)'
    )
    parser.add_argument(
        '--with-plans',
        action='store_true',
        help='Include plans from data/plans/'
    )
    parser.add_argument(
        '--with-config',
        action='store_true',
        help='Include config from data/config/ (including API keys!)'
    )
    parser.add_argument(
        '--zip',
        action='store_true',
        help='Also create a .zip archive'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    # Determine target platform
    if args.linux:
        target_platform = "linux"
    elif args.win:
        target_platform = "win"
    else:
        target_platform = "both"
    
    try:
        result = build_server_package(
            output_dir=args.output.resolve(),
            include_plans=args.with_plans,
            include_config=args.with_config,
            create_zip=args.zip,
            verbose=not args.quiet,
            target_platform=target_platform
        )
        
        if not args.quiet:
            print(f"\nTo deploy:")
            print(f"  1. Copy {result.name}/ to your server")
            if target_platform == "linux":
                print(f"  2a. Quick:      chmod +x start.sh && ./start.sh")
                print(f"  2b. Production: chmod +x start.sh && ./start.sh --watchdog")
                print(f"  2c. Full:       chmod +x scripts/deploy/deploy.sh && ./scripts/deploy/deploy.sh")
                print(f"      (sets up venv, systemd+watchdog, nginx, health checks)")
            elif target_platform == "win":
                print(f"  2a. Quick:      start.bat")
                print(f"  2b. Production: start.bat --watchdog")
            else:
                print(f"  2. Run: ./start.sh (Linux) or start.bat (Windows)")
                print(f"     For production: add --watchdog for crash protection")
                print(f"     For full Linux setup: ./scripts/deploy/deploy.sh")
            print(f"  3. Open: http://your-server-ip:8080/dashboard")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

