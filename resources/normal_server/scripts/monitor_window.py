#!/usr/bin/env python3
"""
NormCode Monitor Window

Opens the web-based monitor in a dedicated pywebview window.
This is a separate script because pywebview must run on the main thread.

Usage:
    python monitor_window.py                    # Default localhost:8080
    python monitor_window.py --port 9000        # Custom port
    python monitor_window.py --url http://...   # Custom URL
"""

import sys
import argparse
from pathlib import Path

# Get icon path
SCRIPT_DIR = Path(__file__).resolve().parent
ICON_PATH = SCRIPT_DIR / "resources" / "icon.ico"


def set_windows_icon(icon_path: str):
    """Set application icon using Windows API (for taskbar)."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        from ctypes import wintypes
        
        # Load icon
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        
        # Load the icon file
        hicon = ctypes.windll.user32.LoadImageW(
            None, icon_path, IMAGE_ICON, 0, 0, 
            LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        
        if hicon:
            # Set as the app user model icon (for taskbar grouping)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NormCode.Monitor")
            print(f"Windows icon set: {hicon}")
    except Exception as e:
        print(f"Could not set Windows icon: {e}")


def main():
    parser = argparse.ArgumentParser(description="Open NormCode Monitor in dedicated window")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--url", type=str, default=None, help="Full URL (overrides host/port)")
    
    args = parser.parse_args()
    
    # Determine URL
    if args.url:
        monitor_url = args.url
    else:
        monitor_url = f"http://{args.host}:{args.port}/monitor/ui"
    
    # Try to import webview
    try:
        import webview
    except ImportError:
        print("pywebview not installed. Run: pip install pywebview")
        print(f"Or open in browser: {monitor_url}")
        sys.exit(1)
    
    print(f"Opening monitor: {monitor_url}")
    
    # Check icon
    icon_path = str(ICON_PATH.resolve()) if ICON_PATH.exists() else None
    if icon_path:
        print(f"Using icon: {icon_path}")
        # Set Windows AppUserModelID for proper taskbar grouping/icon
        set_windows_icon(icon_path)
    
    # Create window
    window = webview.create_window(
        title="NormCode Monitor",
        url=monitor_url,
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 500),
    )
    
    # Start with icon (pywebview's built-in support)
    webview.start(icon=icon_path)


if __name__ == "__main__":
    main()

