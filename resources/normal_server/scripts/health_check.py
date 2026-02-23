#!/usr/bin/env python3
"""
NormCode Server Health Check — Cross-Platform (Python)

Quick health check for the NormCode server.
Works on Windows, Linux, and macOS (replaces bash-only healthcheck.sh).

Usage:
    python health_check.py                     # Check localhost:8080
    python health_check.py --port 9000         # Check specific port
    python health_check.py --host 10.0.0.5     # Check remote host
    python health_check.py --verbose           # Show detailed output
    python health_check.py --json              # Output as JSON
"""

import sys
import io
import json
import argparse
import platform
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================================
# Colors
# ============================================================================

class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    END = "\033[0m"

def _enable_win_ansi():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7
            )
            return True
        except Exception:
            return False
    return True

USE_COLOR = _enable_win_ansi()

def col(text: str, color: str) -> str:
    return f"{color}{text}{C.END}" if USE_COLOR else text


# ============================================================================
# Checks
# ============================================================================

def check_http(url: str, label: str, timeout: int = 5) -> Dict[str, Any]:
    """Check an HTTP endpoint."""
    import urllib.request
    import urllib.error

    result = {"check": label, "url": url}
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = "ok"
            result["http_code"] = resp.status
            try:
                result["body"] = json.loads(resp.read().decode())
            except Exception:
                pass
    except urllib.error.HTTPError as e:
        result["status"] = "warn" if e.code < 500 else "fail"
        result["http_code"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["status"] = "fail"
        result["http_code"] = 0
        result["error"] = str(e)

    return result


def check_disk() -> Dict[str, Any]:
    """Check disk space."""
    try:
        usage = shutil.disk_usage(".")
        pct = round(usage.used / usage.total * 100, 1)
        return {
            "check": "disk",
            "status": "fail" if pct > 95 else ("warn" if pct > 90 else "ok"),
            "percent": pct,
            "free_gb": round(usage.free / 1024 / 1024 / 1024, 1),
        }
    except Exception as e:
        return {"check": "disk", "status": "unknown", "error": str(e)}


def check_memory() -> Dict[str, Any]:
    """Check available memory."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        avail_mb = round(vm.available / 1024 / 1024)
        return {
            "check": "memory",
            "status": "fail" if avail_mb < 128 else ("warn" if avail_mb < 256 else "ok"),
            "available_mb": avail_mb,
            "percent_used": vm.percent,
        }
    except ImportError:
        return {"check": "memory", "status": "unknown", "error": "psutil not installed"}


def check_crash_dir() -> Dict[str, Any]:
    """Check for recent crash reports."""
    crashes_dir = Path(__file__).resolve().parent.parent / "data" / "crashes"
    if not crashes_dir.exists():
        return {"check": "crashes", "status": "ok", "count": 0, "message": "No crash directory"}

    crash_files = sorted(crashes_dir.glob("crash_*.json"), reverse=True)
    recent = []
    for cf in crash_files[:5]:
        try:
            data = json.loads(cf.read_text(encoding="utf-8"))
            recent.append({
                "file": cf.name,
                "timestamp": data.get("timestamp"),
                "exit_code": data.get("exit_code"),
            })
        except Exception:
            pass

    return {
        "check": "crashes",
        "status": "warn" if len(crash_files) > 0 else "ok",
        "count": len(crash_files),
        "recent": recent,
    }


# ============================================================================
# Main
# ============================================================================

def run_health_check(host: str, port: int, verbose: bool = False, as_json: bool = False):
    """Run all health checks and report."""
    base = f"http://{host}:{port}"
    results: List[Dict[str, Any]] = []

    # HTTP checks
    results.append(check_http(f"{base}/health", "health_endpoint"))
    results.append(check_http(f"{base}/info", "info_endpoint"))
    results.append(check_http(f"{base}/api/plans", "plans_api"))

    # System checks
    results.append(check_disk())
    results.append(check_memory())
    results.append(check_crash_dir())

    # JSON output
    if as_json:
        overall = "healthy" if all(r["status"] == "ok" for r in results) else "unhealthy"
        print(json.dumps({"status": overall, "checks": results, "timestamp": datetime.now().isoformat()}, indent=2))
        return all(r["status"] != "fail" for r in results)

    # Pretty output
    print(f"\n{col('NormCode Server Health Check', C.BOLD)}")
    print(f"{col('-' * 45, C.DIM)}")
    print(f"  Target: {col(base, C.CYAN)}")
    print(f"  Time:   {col(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), C.DIM)}")
    print()

    all_ok = True
    for r in results:
        status = r["status"]
        name = r["check"]

        if status == "ok":
            icon = col("✓", C.GREEN)
        elif status == "warn":
            icon = col("⚠", C.YELLOW)
            all_ok = False
        elif status == "fail":
            icon = col("✗", C.RED)
            all_ok = False
        else:
            icon = col("?", C.DIM)

        detail = ""
        if "http_code" in r:
            detail = f"HTTP {r['http_code']}"
        elif "percent" in r:
            detail = f"{r['percent']}% used"
        elif "available_mb" in r:
            detail = f"{r['available_mb']}MB available"
        elif "count" in r:
            detail = f"{r['count']} crash report(s)"

        if status == "fail" and "error" in r:
            detail += f" — {r['error']}"

        print(f"  {icon} {name:20s} {detail}")

        # Verbose: show response body
        if verbose and "body" in r:
            body = r["body"]
            if isinstance(body, dict):
                for k, v in body.items():
                    print(f"      {col(k, C.DIM)}: {v}")

    print()
    if all_ok:
        print(f"  {col('Overall: HEALTHY', C.GREEN + C.BOLD)}")
    else:
        print(f"  {col('Overall: ISSUES DETECTED', C.RED + C.BOLD)}")

    print()
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="NormCode Server Health Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    ok = run_health_check(args.host, args.port, verbose=args.verbose, as_json=args.json)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

