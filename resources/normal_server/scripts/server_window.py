#!/usr/bin/env python3
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
