#!/usr/bin/env python3
"""
NormCode Crash Report Analyzer

Reads crash reports from data/crashes/ and produces a summary.
Useful for identifying patterns, recurring issues, and resource trends.

Usage:
    python analyze_crashes.py                  # Summary of all crashes
    python analyze_crashes.py --last 5         # Last 5 crashes
    python analyze_crashes.py --json           # Output as JSON
    python analyze_crashes.py --detail         # Show full crash details
"""

import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================================
# Paths
# ============================================================================

CRASHES_DIR = Path(__file__).resolve().parent.parent / "data" / "crashes"

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
# Analysis
# ============================================================================

def load_crash_reports(limit: int = 0) -> List[Dict[str, Any]]:
    """Load crash reports from disk, newest first."""
    if not CRASHES_DIR.exists():
        return []

    files = sorted(CRASHES_DIR.glob("crash_*.json"), reverse=True)
    if limit > 0:
        files = files[:limit]

    reports = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            reports.append(data)
        except Exception as e:
            print(f"Warning: Failed to read {f.name}: {e}", file=sys.stderr)

    return reports


def analyze(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a list of crash reports and produce summary statistics."""
    if not reports:
        return {"total_crashes": 0}

    exit_codes = Counter()
    memory_at_crash = []
    disk_at_crash = []
    uptimes = []
    timestamps = []

    for r in reports:
        # Exit codes
        ec = r.get("exit_code")
        exit_codes[str(ec)] += 1

        # Timestamps
        ts = r.get("timestamp")
        if ts:
            timestamps.append(ts)

        # Server uptime before crash
        up = r.get("server_uptime")
        if up:
            uptimes.append(up)

        # System info
        sys_info = r.get("system", {})
        mem = sys_info.get("memory", {})
        if "available_mb" in mem:
            memory_at_crash.append(mem["available_mb"])
        disk = sys_info.get("disk", {})
        if "percent" in disk:
            disk_at_crash.append(disk["percent"])

    summary = {
        "total_crashes": len(reports),
        "exit_codes": dict(exit_codes),
        "time_range": {
            "first": timestamps[-1] if timestamps else None,
            "last": timestamps[0] if timestamps else None,
        },
        "memory_at_crash_mb": {
            "min": min(memory_at_crash) if memory_at_crash else None,
            "max": max(memory_at_crash) if memory_at_crash else None,
            "avg": round(sum(memory_at_crash) / len(memory_at_crash)) if memory_at_crash else None,
        },
        "disk_at_crash_pct": {
            "min": min(disk_at_crash) if disk_at_crash else None,
            "max": max(disk_at_crash) if disk_at_crash else None,
            "avg": round(sum(disk_at_crash) / len(disk_at_crash), 1) if disk_at_crash else None,
        },
        "server_uptimes": uptimes[:10],
    }

    return summary


def print_summary(reports: List[Dict[str, Any]], detail: bool = False):
    """Print a human-friendly summary."""
    if not reports:
        print(f"\n  {col('No crash reports found.', C.GREEN)}")
        print(f"  Crash directory: {CRASHES_DIR}\n")
        return

    summary = analyze(reports)

    print(f"\n{col('NormCode Crash Report Analysis', C.BOLD)}")
    print(f"{col('=' * 50, C.DIM)}")

    # Overview
    total = summary["total_crashes"]
    print(f"\n  {col('Total crashes:', C.CYAN)}  {col(str(total), C.RED + C.BOLD)}")

    tr = summary.get("time_range", {})
    if tr.get("first"):
        print(f"  {col('First crash:', C.CYAN)}   {tr['first']}")
    if tr.get("last"):
        print(f"  {col('Last crash:', C.CYAN)}    {tr['last']}")

    # Exit codes
    ec = summary.get("exit_codes", {})
    if ec:
        print(f"\n  {col('Exit Codes:', C.BOLD)}")
        for code, count in sorted(ec.items(), key=lambda x: -x[1]):
            bar = col("█" * min(count, 30), C.RED)
            label = _exit_code_label(code)
            print(f"    {code:>6s}  {bar} {count}  {col(label, C.DIM)}")

    # Memory
    mem = summary.get("memory_at_crash_mb", {})
    if mem.get("avg") is not None:
        print(f"\n  {col('Memory at Crash:', C.BOLD)}")
        print(f"    Min: {mem['min']}MB  |  Avg: {mem['avg']}MB  |  Max: {mem['max']}MB")
        if mem["min"] is not None and mem["min"] < 256:
            print(f"    {col('⚠ Low memory detected at some crashes!', C.YELLOW)}")

    # Disk
    disk = summary.get("disk_at_crash_pct", {})
    if disk.get("avg") is not None:
        print(f"\n  {col('Disk Usage at Crash:', C.BOLD)}")
        print(f"    Min: {disk['min']}%  |  Avg: {disk['avg']}%  |  Max: {disk['max']}%")
        if disk["max"] is not None and disk["max"] > 90:
            print(f"    {col('⚠ High disk usage detected at some crashes!', C.YELLOW)}")

    # Uptime before crash
    uptimes = summary.get("server_uptimes", [])
    if uptimes:
        print(f"\n  {col('Server Uptime Before Crash (recent):', C.BOLD)}")
        for u in uptimes[:5]:
            print(f"    • {u}")

    # Detailed view
    if detail:
        print(f"\n{col('Detailed Crash Reports', C.BOLD)}")
        print(f"{col('-' * 50, C.DIM)}")
        for i, r in enumerate(reports):
            print(f"\n  {col(f'Crash #{i+1}', C.BOLD + C.RED)}  {col(r.get('_file', ''), C.DIM)}")
            print(f"    Time:      {r.get('timestamp', '?')}")
            print(f"    Exit Code: {r.get('exit_code', '?')}")
            print(f"    PID:       {r.get('pid', '?')}")
            print(f"    Uptime:    {r.get('server_uptime', '?')}")

            sys_info = r.get("system", {})
            if sys_info.get("memory"):
                m = sys_info["memory"]
                print(f"    Memory:    {m.get('used_mb', '?')}MB used / {m.get('available_mb', '?')}MB free")
            if sys_info.get("disk"):
                d = sys_info["disk"]
                print(f"    Disk:      {d.get('percent', '?')}% used ({d.get('free_gb', '?')}GB free)")

            # Last log lines
            log_lines = r.get("last_log_lines", [])
            if log_lines:
                print(f"    {col('Last log lines:', C.DIM)}")
                for line in log_lines[-5:]:
                    print(f"      {col(line.rstrip(), C.DIM)}")

    # Recommendations
    print(f"\n{col('Recommendations:', C.BOLD)}")
    if total == 1:
        print(f"  • Single crash — likely a one-time event. Monitor for recurrence.")
    elif total <= 3:
        print(f"  • {total} crashes — check exit codes and log files for patterns.")
    else:
        print(f"  • {col(f'{total} crashes — recurring issue!', C.RED)} Investigate root cause urgently.")

    if mem.get("min") is not None and mem["min"] < 256:
        print(f"  • {col('Low memory detected', C.YELLOW)} — consider increasing RAM or reducing load.")

    if disk.get("max") is not None and disk["max"] > 90:
        print(f"  • {col('High disk usage', C.YELLOW)} — free disk space or add storage.")

    print(f"\n  Crash reports: {CRASHES_DIR}")
    print(f"  Server log:    {CRASHES_DIR.parent / 'server.log'}")
    print(f"  Watchdog log:  {CRASHES_DIR.parent / 'watchdog.log'}")
    print()


def _exit_code_label(code: str) -> str:
    """Human-readable label for common exit codes."""
    labels = {
        "None": "process not found / health timeout",
        "0": "clean exit",
        "1": "general error",
        "2": "misuse of shell command",
        "-9": "killed (SIGKILL / OOM)",
        "-11": "segfault (SIGSEGV)",
        "-15": "terminated (SIGTERM)",
        "137": "killed (OOM / SIGKILL)",
        "139": "segfault",
        "143": "terminated (SIGTERM)",
        "3221225477": "access violation (Windows)",
        "3221225725": "stack overflow (Windows)",
        "-1073741819": "access violation (Windows)",
        "-1073741571": "stack overflow (Windows)",
    }
    return labels.get(code, "")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NormCode Crash Report Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--last", "-n", type=int, default=0, help="Analyze last N crashes (default: all)")
    parser.add_argument("--detail", "-d", action="store_true", help="Show full crash details")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    reports = load_crash_reports(limit=args.last)

    if args.json:
        summary = analyze(reports)
        print(json.dumps(summary, indent=2))
    else:
        print_summary(reports, detail=args.detail)


if __name__ == "__main__":
    main()

