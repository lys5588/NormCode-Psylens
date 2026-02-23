#!/usr/bin/env python3
"""
NormCode Server Launcher

A friendly launcher for the NormCode Deployment Server with:
- Dependency checking
- Interactive configuration
- Quick start options
- Status monitoring

Usage:
    python launch.py                    # Interactive mode
    python launch.py --quick            # Quick start with defaults
    python launch.py --port 9000        # Start on specific port
    python launch.py --check            # Check dependencies only
    python launch.py --setup            # Run setup wizard
"""

import sys
import os
import subprocess
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

SERVER_DIR = Path(__file__).resolve().parent
DATA_DIR = SERVER_DIR / "data"
PLANS_DIR = DATA_DIR / "plans"
RUNS_DIR = DATA_DIR / "runs"
CONFIG_DIR = DATA_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
MAX_PORT_ATTEMPTS = 10  # Try up to 10 ports before giving up


def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding."""
    import socket
    
    # Method 1: Try to connect - if it succeeds, something is listening
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            check_host = "127.0.0.1" if host == "0.0.0.0" else host
            result = sock.connect_ex((check_host, port))
            if result == 0:
                # Connection succeeded - port is in use
                return False
    except Exception:
        pass
    
    # Method 2: Try to bind - more reliable on Windows
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Don't use SO_REUSEADDR for more accurate check on Windows
            sock.bind((host, port))
            return True
    except (OSError, socket.error):
        return False


def find_available_port(host: str, start_port: int, max_attempts: int = MAX_PORT_ATTEMPTS) -> int:
    """Find an available port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        if is_port_available(host, port):
            return port
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts - 1}")


# ANSI colors (Windows compatible via colorama or native)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def supports_color():
    """Check if terminal supports colors."""
    if sys.platform == 'win32':
        # Enable ANSI on Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

USE_COLOR = supports_color()

def c(text, color):
    """Colorize text if supported."""
    if USE_COLOR:
        return f"{color}{text}{Colors.END}"
    return text

def print_banner():
    """Print the startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ███╗   ██╗ ██████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ███████╗   ║
    ║     ████╗  ██║██╔═══██╗██╔══██╗████╗ ████║██╔════╝██╔═══██╗██╔══██║██╔════╝   ║
    ║     ██╔██╗ ██║██║   ██║██████╔╝██╔████╔██║██║     ██║   ██║██║  ██║█████╗     ║
    ║     ██║╚██╗██║██║   ██║██╔══██╗██║╚██╔╝██║██║     ██║   ██║██║  ██║██╔══╝     ║
    ║     ██║ ╚████║╚██████╔╝██║  ██║██║ ╚═╝ ██║╚██████╗╚██████╔╝██████╔╝███████╗   ║
    ║     ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝   ║
    ║                                                               ║
    ║                   Deployment Server Launcher                  ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    # Simplified banner for better compatibility
    simple_banner = f"""
    {c('='*60, Colors.CYAN)}
    {c('  NormCode Deployment Server', Colors.BOLD + Colors.GREEN)}
    {c('='*60, Colors.CYAN)}
    """
    print(simple_banner)


# ============================================================================
# Dependency Checking
# ============================================================================

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("yaml", "pyyaml"),
    ("numpy", "numpy"),
]

OPTIONAL_PACKAGES = [
    ("openai", "openai", "OpenAI GPT models"),
    ("dashscope", "dashscope", "Alibaba Qwen models"),
    ("anthropic", "anthropic", "Anthropic Claude models"),
    ("webview", "pywebview", "Dedicated monitor window"),
]

def check_package(import_name):
    """Check if a package is installed."""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def check_dependencies():
    """Check all dependencies and return status."""
    print(f"\n{c('Checking dependencies...', Colors.BOLD)}\n")
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    print(f"  {c('Required:', Colors.BOLD)}")
    for import_name, pip_name in REQUIRED_PACKAGES:
        if check_package(import_name):
            print(f"    {c('✓', Colors.GREEN)} {pip_name}")
        else:
            print(f"    {c('✗', Colors.RED)} {pip_name} {c('(missing)', Colors.DIM)}")
            missing_required.append(pip_name)
    
    # Check optional packages
    print(f"\n  {c('Optional (LLM providers):', Colors.BOLD)}")
    for import_name, pip_name, desc in OPTIONAL_PACKAGES:
        if check_package(import_name):
            print(f"    {c('✓', Colors.GREEN)} {pip_name} - {c(desc, Colors.DIM)}")
        else:
            print(f"    {c('○', Colors.YELLOW)} {pip_name} - {c(desc, Colors.DIM)}")
            missing_optional.append(pip_name)
    
    print()
    return missing_required, missing_optional

def install_dependencies(packages):
    """Install missing packages."""
    if not packages:
        return True
    
    print(f"\n{c('Installing packages:', Colors.BOLD)} {', '.join(packages)}\n")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--quiet", *packages
        ])
        print(f"\n{c('✓', Colors.GREEN)} Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{c('✗', Colors.RED)} Failed to install packages: {e}")
        return False


# ============================================================================
# Configuration
# ============================================================================

def ensure_directories():
    """Create necessary directories."""
    for dir_path in [DATA_DIR, PLANS_DIR, RUNS_DIR, CONFIG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def check_llm_config():
    """Check if LLM settings are configured."""
    if not SETTINGS_FILE.exists():
        return None
    
    try:
        import yaml
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        
        # Count configured models (excluding BASE_URL)
        models = [k for k in settings.keys() if k not in ('BASE_URL',) and isinstance(settings[k], dict)]
        
        # Check if any have API keys
        configured = []
        for model in models:
            model_config = settings.get(model, {})
            if model_config.get('api_key') and model_config['api_key'] != 'your-api-key-here':
                configured.append(model)
        
        return configured
    except Exception:
        return None

def setup_llm_config():
    """Interactive LLM configuration setup."""
    print(f"\n{c('LLM Configuration Setup', Colors.BOLD)}")
    print(f"{c('-'*40, Colors.DIM)}\n")
    
    ensure_directories()
    
    # Default template
    template = """# NormCode LLM Settings
# Configure your LLM providers here

# Default base URL (for Alibaba DashScope)
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

# Alibaba Qwen (recommended for Chinese)
qwen-plus:
  model: qwen-plus
  api_key: {qwen_key}

# OpenAI GPT
gpt-4o:
  model: gpt-4o
  api_key: {openai_key}
  base_url: https://api.openai.com/v1

# Anthropic Claude
claude-3-sonnet:
  model: claude-3-sonnet-20240229
  api_key: {anthropic_key}
  base_url: https://api.anthropic.com/v1

# Demo mode (mock responses, no API needed)
demo:
  model: demo
  is_mock: true
"""
    
    print("  Enter your API keys (press Enter to skip):\n")
    
    qwen_key = input(f"  {c('Alibaba DashScope', Colors.CYAN)} API key: ").strip() or "your-api-key-here"
    openai_key = input(f"  {c('OpenAI', Colors.CYAN)} API key: ").strip() or "your-api-key-here"
    anthropic_key = input(f"  {c('Anthropic', Colors.CYAN)} API key: ").strip() or "your-api-key-here"
    
    config_content = template.format(
        qwen_key=qwen_key,
        openai_key=openai_key,
        anthropic_key=anthropic_key
    )
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"\n{c('✓', Colors.GREEN)} Configuration saved to: {SETTINGS_FILE}")
    
    # Summary
    configured = []
    if qwen_key != "your-api-key-here":
        configured.append("qwen-plus")
    if openai_key != "your-api-key-here":
        configured.append("gpt-4o")
    if anthropic_key != "your-api-key-here":
        configured.append("claude-3-sonnet")
    
    if configured:
        print(f"  Configured models: {c(', '.join(configured), Colors.GREEN)}")
    else:
        print(f"  {c('Note:', Colors.YELLOW)} No API keys configured. Only demo mode available.")
    
    return configured


def show_status():
    """Show current server status and configuration."""
    print(f"\n{c('Server Status', Colors.BOLD)}")
    print(f"{c('-'*40, Colors.DIM)}\n")
    
    # Directories
    print(f"  {c('Directories:', Colors.CYAN)}")
    print(f"    Server:  {SERVER_DIR}")
    
    # Count plans (directories only)
    if PLANS_DIR.exists():
        plan_count = len([p for p in PLANS_DIR.iterdir() if p.is_dir()])
        plan_text = f"({plan_count} plan{'s' if plan_count != 1 else ''})"
        print(f"    Plans:   {PLANS_DIR} {c(plan_text, Colors.DIM)}")
    else:
        print(f"    Plans:   {PLANS_DIR} {c('(not created)', Colors.DIM)}")
    
    # Count runs (directories only)
    if RUNS_DIR.exists():
        run_count = len([r for r in RUNS_DIR.iterdir() if r.is_dir()])
        run_text = f"({run_count} run{'s' if run_count != 1 else ''})"
        print(f"    Runs:    {RUNS_DIR} {c(run_text, Colors.DIM)}")
    else:
        print(f"    Runs:    {RUNS_DIR} {c('(not created)', Colors.DIM)}")
    
    # LLM Config
    print(f"\n  {c('LLM Configuration:', Colors.CYAN)}")
    configured = check_llm_config()
    if configured:
        print(f"    {c('✓', Colors.GREEN)} Settings file: {SETTINGS_FILE}")
        print(f"    Configured models: {c(', '.join(configured), Colors.GREEN)}")
    elif SETTINGS_FILE.exists():
        print(f"    {c('○', Colors.YELLOW)} Settings file exists but no API keys configured")
        print(f"    Only demo mode available")
    else:
        print(f"    {c('✗', Colors.RED)} Settings file not found")
        print(f"    Run with --setup to configure")
    
    # Deployed plans
    if PLANS_DIR.exists():
        plans = [p.name for p in PLANS_DIR.iterdir() if p.is_dir()]
        if plans:
            print(f"\n  {c('Deployed Plans:', Colors.CYAN)}")
            for plan in plans[:5]:  # Show first 5
                print(f"    • {plan}")
            if len(plans) > 5:
                print(f"    {c(f'... and {len(plans) - 5} more', Colors.DIM)}")
    
    print()


# ============================================================================
# Server Launch
# ============================================================================

def start_dashboard(host: str, port: int):
    """
    Start the server dashboard in a dedicated window using pywebview.
    Falls back to browser if pywebview is not installed.
    
    Note: pywebview must run on main thread, so we launch it as a separate process.
    """
    import webbrowser
    
    # Use localhost for browser if binding to all interfaces
    display_host = "localhost" if host == "0.0.0.0" else host
    dashboard_url = f"http://{display_host}:{port}/dashboard"
    
    # Check if pywebview is available
    try:
        import webview
        has_webview = True
    except ImportError:
        has_webview = False
    
    if has_webview:
        # Launch as separate process (pywebview needs main thread)
        server_window_script = SERVER_DIR / "scripts" / "server_window.py"
        
        # Create the window script if it doesn't exist
        if not server_window_script.exists():
            script_content = '''#!/usr/bin/env python3
"""Opens NormCode Server dashboard in pywebview window."""
import sys, argparse
try:
    import webview
except ImportError:
    print("pywebview not installed"); sys.exit(1)
parser = argparse.ArgumentParser()
parser.add_argument("--port", "-p", type=int, default=8080)
parser.add_argument("--host", type=str, default="localhost")
args = parser.parse_args()
url = f"http://{args.host}:{args.port}/dashboard"
webview.create_window("NormCode Server", url, width=1200, height=800, resizable=True)
webview.start()
'''
            server_window_script.write_text(script_content)
        
        try:
            subprocess.Popen(
                [sys.executable, str(server_window_script), "--host", display_host, "--port", str(port)],
                cwd=str(SERVER_DIR),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
            )
            print(f"  {c('Dashboard:', Colors.GREEN)} Opening dedicated window...")
            return True
        except Exception as e:
            print(f"  {c('Dashboard:', Colors.YELLOW)} Failed to launch window ({e})")
    else:
        print(f"  {c('Dashboard:', Colors.YELLOW)} pywebview not installed")
        print(f"             {c('Tip:', Colors.DIM)} pip install pywebview  {c('for dedicated window', Colors.DIM)}")
    
    # Fallback to browser
    try:
        webbrowser.open(dashboard_url)
        print(f"  {c('Dashboard:', Colors.GREEN)} Opening in browser: {dashboard_url}")
        return True
    except Exception as e:
        print(f"  {c('Dashboard:', Colors.YELLOW)} Failed to open browser ({e})")
        print(f"             Open manually: {dashboard_url}")
        return False


def ensure_inspector_bundle():
    """Build the React inspector bundle if static/dist/run-inspector.js is missing."""
    dist_js = SERVER_DIR / "static" / "dist" / "run-inspector.js"
    if dist_js.exists():
        return

    inspector_dir = SERVER_DIR / "inspector"
    if not (inspector_dir / "package.json").exists():
        return

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    if not (inspector_dir / "node_modules").exists():
        print(f"  {c('Installing inspector dependencies...', Colors.CYAN)}")
        subprocess.run(
            [npm_cmd, "install"],
            cwd=str(inspector_dir),
            check=True,
            capture_output=True,
        )

    print(f"  {c('Building inspector React bundle...', Colors.CYAN)}")
    result = subprocess.run(
        [npm_cmd, "run", "build"],
        cwd=str(inspector_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  {c('✓', Colors.GREEN)} Inspector bundle built successfully")
    else:
        print(f"  {c('⚠', Colors.YELLOW)} Inspector build failed — tools/inspect tabs will use fallback UI")
        if result.stderr:
            for line in result.stderr.strip().splitlines()[-3:]:
                print(f"    {line}")


def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT, reload=False, with_monitor=False):
    """Start the NormCode server."""
    ensure_directories()
    ensure_inspector_bundle()
    
    # Check if requested port is available, find alternative if not
    original_port = port
    if not is_port_available(host, port):
        print(f"\n{c('Port', Colors.YELLOW)} {c(str(port), Colors.BOLD)} {c('is already in use.', Colors.YELLOW)}")
        try:
            port = find_available_port(host, port + 1)
            print(f"{c('Using port', Colors.GREEN)} {c(str(port), Colors.BOLD)} {c('instead.', Colors.GREEN)}\n")
        except RuntimeError as e:
            print(f"{c('Error:', Colors.RED)} {e}")
            print(f"Please free up port {original_port} or specify a different port with --port")
            sys.exit(1)
    
    # Set environment variables
    os.environ["NORMCODE_HOST"] = host
    os.environ["NORMCODE_PORT"] = str(port)
    os.environ["NORMCODE_PLANS_DIR"] = str(PLANS_DIR)
    os.environ["NORMCODE_RUNS_DIR"] = str(RUNS_DIR)
    
    print(f"\n{c('Starting NormCode Deployment Server...', Colors.BOLD)}\n")
    print(f"  {c('Host:', Colors.CYAN)}    {host}")
    print(f"  {c('Port:', Colors.CYAN)}    {port}" + (f" {c('(was ' + str(original_port) + ')', Colors.DIM)}" if port != original_port else ""))
    print(f"  {c('Plans:', Colors.CYAN)}   {PLANS_DIR}")
    print(f"  {c('Runs:', Colors.CYAN)}    {RUNS_DIR}")
    
    # Show configured models
    configured = check_llm_config()
    if configured:
        print(f"  {c('Models:', Colors.CYAN)}  {', '.join(configured)}")
    else:
        print(f"  {c('Models:', Colors.CYAN)}  demo only {c('(no API keys configured)', Colors.DIM)}")
    
    display_host = "localhost" if host == "0.0.0.0" else host
    print(f"\n  {c('API:', Colors.GREEN)}      http://{display_host}:{port}")
    print(f"  {c('Docs:', Colors.GREEN)}     http://{display_host}:{port}/docs")
    print(f"  {c('Dashboard:', Colors.GREEN)} http://{display_host}:{port}/dashboard")
    
    # Launch dashboard in separate window if requested
    if with_monitor:
        print(f"\n{c('Launching dashboard...', Colors.CYAN)}")
        # Give server a moment to start
        import threading
        def delayed_dashboard():
            import time
            time.sleep(2)  # Wait for server to be ready
            start_dashboard(host, port)
        threading.Thread(target=delayed_dashboard, daemon=True).start()
    
    print(f"\n{c('-'*40, Colors.DIM)}")
    print(f"  Press {c('Ctrl+C', Colors.BOLD)} to stop the server")
    print(f"{c('-'*40, Colors.DIM)}\n")
    
    # Add server directory to path
    if str(SERVER_DIR) not in sys.path:
        sys.path.insert(0, str(SERVER_DIR))
    
    # Start uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print(f"\n\n{c('Server stopped.', Colors.YELLOW)}")
    except Exception as e:
        print(f"\n{c('Error:', Colors.RED)} {e}")
        sys.exit(1)


def interactive_menu():
    """Show interactive menu."""
    while True:
        print(f"\n{c('What would you like to do?', Colors.BOLD)}\n")
        print(f"  {c('[1]', Colors.CYAN)} Start server")
        print(f"  {c('[2]', Colors.CYAN)} Start server + open dashboard")
        print(f"  {c('[3]', Colors.CYAN)} Start server (custom port)")
        print(f"  {c('[4]', Colors.CYAN)} Start with watchdog {c('(auto-restart on crash)', Colors.DIM)}")
        print(f"  {c('[5]', Colors.CYAN)} Open dashboard {c('(pywebview/browser)', Colors.DIM)}")
        print(f"  {c('[6]', Colors.CYAN)} Configure LLM settings")
        print(f"  {c('[7]', Colors.CYAN)} Check dependencies")
        print(f"  {c('[8]', Colors.CYAN)} Show status")
        print(f"  {c('[9]', Colors.CYAN)} Health check / Crash analysis")
        print(f"  {c('[q]', Colors.CYAN)} Quit")
        
        choice = input(f"\n  Enter choice [{c('1', Colors.GREEN)}]: ").strip().lower() or "1"
        
        if choice == "1":
            start_server()
            break
        elif choice == "2":
            start_server(with_monitor=True)
            break
        elif choice == "3":
            port_str = input(f"  Enter port [{c(str(DEFAULT_PORT), Colors.GREEN)}]: ").strip()
            port = int(port_str) if port_str.isdigit() else DEFAULT_PORT
            with_mon = input(f"  Start monitor? [{c('y', Colors.GREEN)}/n]: ").strip().lower() != 'n'
            start_server(port=port, with_monitor=with_mon)
            break
        elif choice == "4":
            # Start with watchdog
            port_str = input(f"  Enter port [{c(str(DEFAULT_PORT), Colors.GREEN)}]: ").strip()
            port = int(port_str) if port_str.isdigit() else DEFAULT_PORT
            from scripts.watchdog import ServerWatchdog
            watchdog = ServerWatchdog(host=DEFAULT_HOST, port=port)
            watchdog.run()
            break
        elif choice == "5":
            # Open dashboard (pywebview or browser)
            port_str = input(f"  Server port [{c(str(DEFAULT_PORT), Colors.GREEN)}]: ").strip()
            port = int(port_str) if port_str.isdigit() else DEFAULT_PORT
            open_ui_window("server", port)
            continue  # Stay in menu
        elif choice == "6":
            setup_llm_config()
        elif choice == "7":
            missing_req, missing_opt = check_dependencies()
            if missing_req:
                install = input(f"\n  Install missing required packages? [{c('y', Colors.GREEN)}/n]: ").strip().lower()
                if install != 'n':
                    install_dependencies(missing_req)
        elif choice == "8":
            show_status()
        elif choice == "9":
            sub = input(f"  [{c('h', Colors.GREEN)}]ealth check / [{c('c', Colors.GREEN)}]rash analysis: ").strip().lower() or "h"
            if sub.startswith("c"):
                from scripts.analyze_crashes import load_crash_reports, print_summary
                reports = load_crash_reports()
                print_summary(reports, detail=True)
            else:
                from scripts.health_check import run_health_check
                port_str = input(f"  Server port [{c(str(DEFAULT_PORT), Colors.GREEN)}]: ").strip()
                port = int(port_str) if port_str.isdigit() else DEFAULT_PORT
                run_health_check("127.0.0.1", port, verbose=True)
        elif choice == "q":
            print(f"\n{c('Goodbye!', Colors.CYAN)}\n")
            break
        else:
            print(f"\n{c('Invalid choice. Please try again.', Colors.YELLOW)}")


def open_ui_window(ui_type: str, port: int, host: str = "localhost"):
    """
    Open a UI in pywebview window or browser.
    
    Args:
        ui_type: "server" (main dashboard), "monitor", or "client"
        port: Server port
        host: Server host
    """
    configs = {
        "server": {
            "url": f"http://{host}:{port}/dashboard",
            "title": "NormCode Server",
            "width": 1200,
            "height": 800,
        },
        "monitor": {
            "url": f"http://{host}:{port}/monitor/ui",
            "title": "NormCode Monitor",
            "width": 1200,
            "height": 800,
        },
        "client": {
            "url": f"http://{host}:{port}/client/ui",
            "title": "NormCode Client",
            "width": 1100,
            "height": 700,
        },
    }
    
    cfg = configs.get(ui_type, configs["server"])
    url = cfg["url"]
    title = cfg["title"]
    
    # Try pywebview first
    try:
        import webview
        print(f"\n  Opening {title}...")
        webview.create_window(title, url, width=cfg["width"], height=cfg["height"], resizable=True)
        webview.start()
    except ImportError:
        import webbrowser
        print(f"\n  Opening in browser: {url}")
        print(f"  {c('Tip:', Colors.DIM)} pip install pywebview for dedicated window")
        webbrowser.open(url)


def run_monitor_inline(server_url: str):
    """Run the monitor in the current terminal."""
    monitor_script = SERVER_DIR / "scripts" / "monitor.py"
    try:
        subprocess.run([sys.executable, str(monitor_script), "--server", server_url])
    except KeyboardInterrupt:
        print(f"\n{c('Monitor stopped.', Colors.YELLOW)}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NormCode Deployment Server Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py                    Interactive mode
  python launch.py --quick            Quick start with defaults
  python launch.py --quick --monitor  Quick start + open monitor
  python launch.py --port 9000        Start on port 9000
  python launch.py --watchdog         Start with auto-restart watchdog
  python launch.py --health           Run health check on running server
  python launch.py --crashes          Analyze crash reports
  python launch.py --monitor-only     Run monitor only (connect to existing server)
  python launch.py --check            Check dependencies only
  python launch.py --setup            Configure LLM settings
  python launch.py --status           Show server status
        """
    )
    
    parser.add_argument("--quick", "-q", action="store_true",
                        help="Quick start with default settings")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST,
                        help=f"Host to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
                        help=f"Port to bind (default: {DEFAULT_PORT})")
    parser.add_argument("--reload", "-r", action="store_true",
                        help="Enable auto-reload for development")
    parser.add_argument("--monitor", "-m", action="store_true",
                        help="Also open dashboard window")
    parser.add_argument("--monitor-only", action="store_true",
                        help="Open dashboard only (connect to existing server)")
    parser.add_argument("--check", "-c", action="store_true",
                        help="Check dependencies only")
    parser.add_argument("--setup", "-s", action="store_true",
                        help="Run LLM configuration setup")
    parser.add_argument("--status", action="store_true",
                        help="Show server status")
    parser.add_argument("--install", "-i", action="store_true",
                        help="Install missing dependencies")
    parser.add_argument("--watchdog", "-w", action="store_true",
                        help="Run with watchdog (auto-restart on crash)")
    parser.add_argument("--health", action="store_true",
                        help="Run health check against running server")
    parser.add_argument("--crashes", action="store_true",
                        help="Analyze crash reports")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Watchdog mode - start server with process guardian
    if args.watchdog:
        from scripts.watchdog import ServerWatchdog
        watchdog = ServerWatchdog(
            host=args.host,
            port=args.port,
        )
        watchdog.run()
        return
    
    # Health check mode
    if args.health:
        from scripts.health_check import run_health_check
        display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
        ok = run_health_check(display_host, args.port, verbose=True)
        sys.exit(0 if ok else 1)
    
    # Crash analysis mode
    if args.crashes:
        from scripts.analyze_crashes import load_crash_reports, print_summary
        reports = load_crash_reports()
        print_summary(reports, detail=True)
        return
    
    # Dashboard-only mode - pywebview or browser
    if args.monitor_only:
        display_host = "localhost" if args.host == "0.0.0.0" else args.host
        dashboard_url = f"http://{display_host}:{args.port}/dashboard"
        
        try:
            import webview
            print(f"Opening dashboard: {dashboard_url}")
            webview.create_window("NormCode Server", dashboard_url, width=1200, height=800, resizable=True)
            webview.start()
        except ImportError:
            import webbrowser
            print(f"Opening dashboard in browser: {dashboard_url}")
            print(f"  Tip: pip install pywebview for dedicated window")
            webbrowser.open(dashboard_url)
        return
    
    # Check dependencies first
    if args.check or args.install:
        missing_req, missing_opt = check_dependencies()
        if args.install and missing_req:
            install_dependencies(missing_req)
        if not args.quick and not args.setup and not args.status:
            return
    
    # Setup mode
    if args.setup:
        setup_llm_config()
        return
    
    # Status mode
    if args.status:
        show_status()
        return
    
    # Quick start
    if args.quick or args.port != DEFAULT_PORT or args.host != DEFAULT_HOST or args.monitor:
        # Check dependencies silently
        missing_req, _ = check_dependencies()
        if missing_req:
            print(f"\n{c('Error:', Colors.RED)} Missing required packages: {', '.join(missing_req)}")
            print(f"Run: pip install {' '.join(missing_req)}")
            sys.exit(1)
        
        start_server(host=args.host, port=args.port, reload=args.reload, with_monitor=args.monitor)
    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()

