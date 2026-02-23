#!/usr/bin/env python3
"""
NormCode Server Watchdog — Process Guardian with Auto-Restart

Monitors the NormCode server process and automatically restarts it on crash.
Cross-platform: works on Windows, Linux, and macOS.

Features:
  - Starts server as a managed subprocess
  - Health checks via HTTP every N seconds
  - Auto-restart on crash with configurable delay and backoff
  - Crash logging with system diagnostics (memory, disk, uptime)
  - Crash reports saved to data/crashes/ as JSON
  - Graceful shutdown on Ctrl+C / SIGTERM

Usage:
    python watchdog.py                          # Start with defaults (port 8080)
    python watchdog.py --port 9000              # Specific port
    python watchdog.py --check-interval 5       # Health check every 5s
    python watchdog.py --max-restarts 10        # Stop after 10 restarts
    python watchdog.py --restart-delay 5        # Wait 5s before restart
"""

import sys
import os
import io
import subprocess
import time
import json
import signal
import logging
import argparse
import platform
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================================
# Paths
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent           # scripts/
SERVER_DIR = SCRIPT_DIR.parent                         # normal_server/
DATA_DIR = SERVER_DIR / "data"
CRASHES_DIR = DATA_DIR / "crashes"
WATCHDOG_LOG = DATA_DIR / "watchdog.log"
SERVER_LOG = DATA_DIR / "server.log"

# ============================================================================
# Logging
# ============================================================================

def setup_logging(log_file: Path, verbose: bool = False):
    """Configure dual logging: file + console."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handlers = [
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

# ============================================================================
# System diagnostics
# ============================================================================

def get_system_info() -> Dict[str, Any]:
    """Gather current system resource information."""
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "timestamp": datetime.now().isoformat(),
    }

    # Memory
    try:
        import psutil
        vm = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": round(vm.total / 1024 / 1024),
            "available_mb": round(vm.available / 1024 / 1024),
            "used_mb": round(vm.used / 1024 / 1024),
            "percent": vm.percent,
        }
    except ImportError:
        # Fallback: parse from OS commands
        if sys.platform == "win32":
            try:
                out = subprocess.check_output(
                    ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/format:csv"],
                    text=True, timeout=5
                )
                for line in out.strip().splitlines():
                    parts = line.strip().split(",")
                    if len(parts) >= 3 and parts[1].isdigit():
                        free_kb = int(parts[1])
                        total_kb = int(parts[2])
                        info["memory"] = {
                            "total_mb": total_kb // 1024,
                            "available_mb": free_kb // 1024,
                            "used_mb": (total_kb - free_kb) // 1024,
                            "percent": round((total_kb - free_kb) / total_kb * 100, 1),
                        }
            except Exception:
                pass
        else:
            try:
                out = subprocess.check_output(["free", "-m"], text=True, timeout=5)
                for line in out.splitlines():
                    if line.startswith("Mem:"):
                        parts = line.split()
                        info["memory"] = {
                            "total_mb": int(parts[1]),
                            "used_mb": int(parts[2]),
                            "available_mb": int(parts[6]) if len(parts) > 6 else int(parts[3]),
                        }
            except Exception:
                pass

    # Disk
    try:
        usage = shutil.disk_usage(str(SERVER_DIR))
        info["disk"] = {
            "total_gb": round(usage.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(usage.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(usage.free / 1024 / 1024 / 1024, 1),
            "percent": round(usage.used / usage.total * 100, 1),
        }
    except Exception:
        pass

    # Uptime
    try:
        import psutil
        boot = datetime.fromtimestamp(psutil.boot_time())
        info["uptime"] = str(datetime.now() - boot)
    except ImportError:
        if sys.platform != "win32":
            try:
                with open("/proc/uptime") as f:
                    secs = float(f.read().split()[0])
                    info["uptime"] = str(timedelta(seconds=int(secs)))
            except Exception:
                pass

    return info


# ============================================================================
# Watchdog
# ============================================================================

class ServerWatchdog:
    """Process guardian for the NormCode server."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        check_interval: int = 10,
        restart_delay: int = 3,
        max_restarts: int = 0,       # 0 = unlimited
        backoff_factor: float = 1.5,
        max_backoff: int = 120,
        verbose: bool = False,
    ):
        self.host = host
        self.port = port
        self.check_interval = check_interval
        self.restart_delay = restart_delay
        self.max_restarts = max_restarts
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self.verbose = verbose

        # State
        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._restart_count = 0
        self._total_crashes = 0
        self._started_at: Optional[datetime] = None
        self._current_delay = restart_delay
        self._server_log_file = None

        # Ensure directories
        CRASHES_DIR.mkdir(parents=True, exist_ok=True)

    # ── Server process management ──────────────────────────────────────

    def _start_server(self) -> bool:
        """Start the server as a subprocess."""
        try:
            # Close previous log file handle if any
            if self._server_log_file and not self._server_log_file.closed:
                self._server_log_file.close()

            SERVER_LOG.parent.mkdir(parents=True, exist_ok=True)
            self._server_log_file = open(str(SERVER_LOG), "a", encoding="utf-8")

            env = os.environ.copy()
            env["NORMCODE_HOST"] = self.host
            env["NORMCODE_PORT"] = str(self.port)

            cmd = [
                sys.executable, str(SERVER_DIR / "launch.py"),
                "--quick",
                "--host", self.host,
                "--port", str(self.port),
            ]

            # Use CREATE_NEW_PROCESS_GROUP on Windows for clean shutdown
            kwargs: Dict[str, Any] = {
                "cwd": str(SERVER_DIR),
                "env": env,
                "stdout": self._server_log_file,
                "stderr": subprocess.STDOUT,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            self._process = subprocess.Popen(cmd, **kwargs)
            self._started_at = datetime.now()

            logging.info(
                f"Server started (PID {self._process.pid}) on {self.host}:{self.port}"
            )
            return True

        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False

    def _stop_server(self):
        """Stop the server process gracefully."""
        if self._process is None:
            return

        logging.info(f"Stopping server (PID {self._process.pid})...")
        try:
            if sys.platform == "win32":
                # Send CTRL_BREAK on Windows
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._process.send_signal(signal.SIGINT)

            try:
                self._process.wait(timeout=15)
                logging.info("Server stopped gracefully.")
            except subprocess.TimeoutExpired:
                logging.warning("Server did not stop gracefully, killing...")
                self._process.kill()
                self._process.wait(timeout=5)
        except Exception as e:
            logging.warning(f"Error stopping server: {e}")
            try:
                self._process.kill()
            except Exception:
                pass
        finally:
            if self._server_log_file and not self._server_log_file.closed:
                self._server_log_file.close()
            self._process = None

    def _is_process_alive(self) -> bool:
        """Check if the server subprocess is still running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    # ── Health checks ──────────────────────────────────────────────────

    def _check_health(self) -> bool:
        """Check server health via HTTP."""
        check_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        url = f"http://{check_host}:{self.port}/health"

        try:
            import urllib.request
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        return False

    # ── Crash handling ─────────────────────────────────────────────────

    def _record_crash(self, exit_code: Optional[int]):
        """Record crash details to a JSON file."""
        self._total_crashes += 1

        uptime = ""
        if self._started_at:
            uptime = str(datetime.now() - self._started_at)

        crash_report = {
            "crash_number": self._total_crashes,
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "pid": self._process.pid if self._process else None,
            "server_uptime": uptime,
            "restart_count": self._restart_count,
            "system": get_system_info(),
        }

        # Read last N lines of server log for context
        try:
            if SERVER_LOG.exists():
                lines = SERVER_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
                crash_report["last_log_lines"] = lines[-50:]
        except Exception:
            pass

        # Save individual crash report
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = CRASHES_DIR / f"crash_{ts}.json"
        try:
            with open(crash_file, "w", encoding="utf-8") as f:
                json.dump(crash_report, f, indent=2, ensure_ascii=False)
            logging.info(f"Crash report saved: {crash_file.name}")
        except Exception as e:
            logging.error(f"Failed to save crash report: {e}")

        return crash_report

    # ── Main loop ──────────────────────────────────────────────────────

    def run(self):
        """Main watchdog loop."""
        self._running = True
        setup_logging(WATCHDOG_LOG, self.verbose)

        logging.info("=" * 60)
        logging.info("NormCode Server Watchdog starting")
        logging.info(f"  Server:    {self.host}:{self.port}")
        logging.info(f"  Check:     every {self.check_interval}s")
        logging.info(f"  Restart:   delay {self.restart_delay}s, backoff {self.backoff_factor}x")
        logging.info(f"  Max:       {'unlimited' if self.max_restarts == 0 else self.max_restarts} restarts")
        logging.info(f"  Crashes:   {CRASHES_DIR}")
        logging.info(f"  Logs:      {WATCHDOG_LOG}")
        logging.info("=" * 60)

        # Register signal handlers
        def _shutdown(signum, frame):
            logging.info(f"Received signal {signum}, shutting down...")
            self._running = False

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, _shutdown)

        # Start server
        if not self._start_server():
            logging.error("Initial server start failed. Exiting.")
            return

        # Wait for server to become healthy
        logging.info("Waiting for server to become healthy...")
        healthy = False
        for i in range(30):  # Wait up to 30 seconds
            if not self._running:
                break
            if self._check_health():
                healthy = True
                break
            time.sleep(1)

        if healthy:
            logging.info("Server is healthy! Watchdog monitoring active.")
            self._current_delay = self.restart_delay  # Reset backoff
        else:
            logging.warning("Server did not become healthy within 30s, monitoring anyway...")

        # Main monitoring loop
        last_check = time.time()
        consecutive_failures = 0
        FAILURE_THRESHOLD = 3  # Restart after 3 consecutive failed health checks

        while self._running:
            time.sleep(1)

            # Periodic health check
            elapsed = time.time() - last_check
            if elapsed >= self.check_interval:
                last_check = time.time()

                process_alive = self._is_process_alive()
                health_ok = self._check_health() if process_alive else False

                if not process_alive:
                    # Process crashed
                    exit_code = self._process.returncode if self._process else None
                    logging.error(
                        f"SERVER CRASHED! Exit code: {exit_code}"
                    )
                    report = self._record_crash(exit_code)
                    self._handle_restart()
                    consecutive_failures = 0

                elif not health_ok:
                    consecutive_failures += 1
                    logging.warning(
                        f"Health check failed ({consecutive_failures}/{FAILURE_THRESHOLD})"
                    )
                    if consecutive_failures >= FAILURE_THRESHOLD:
                        logging.error(
                            "Server unresponsive for too long, forcing restart..."
                        )
                        self._record_crash(None)
                        self._stop_server()
                        self._handle_restart()
                        consecutive_failures = 0
                else:
                    if consecutive_failures > 0:
                        logging.info("Health check recovered.")
                    consecutive_failures = 0

        # Shutdown
        logging.info("Watchdog shutting down...")
        self._stop_server()
        logging.info("Watchdog stopped.")

    def _handle_restart(self):
        """Handle server restart with backoff."""
        self._restart_count += 1

        if self.max_restarts > 0 and self._restart_count > self.max_restarts:
            logging.error(
                f"Max restarts ({self.max_restarts}) reached. "
                f"Watchdog stopping — manual intervention required."
            )
            self._running = False
            return

        logging.info(
            f"Restarting server in {self._current_delay}s "
            f"(restart #{self._restart_count})..."
        )

        # Wait with interruptibility
        wait_until = time.time() + self._current_delay
        while time.time() < wait_until and self._running:
            time.sleep(0.5)

        if not self._running:
            return

        if self._start_server():
            # Wait for healthy
            logging.info("Waiting for server to become healthy...")
            healthy = False
            for i in range(30):
                if not self._running:
                    return
                if self._check_health():
                    healthy = True
                    break
                time.sleep(1)

            if healthy:
                logging.info(f"Server restarted successfully (restart #{self._restart_count}).")
                self._current_delay = self.restart_delay  # Reset backoff
            else:
                logging.warning("Server restarted but not yet healthy.")
                # Apply backoff
                self._current_delay = min(
                    int(self._current_delay * self.backoff_factor),
                    self.max_backoff,
                )
        else:
            logging.error("Restart failed!")
            self._current_delay = min(
                int(self._current_delay * self.backoff_factor),
                self.max_backoff,
            )

    # ── Status ─────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Get watchdog status."""
        return {
            "watchdog": "running" if self._running else "stopped",
            "server_pid": self._process.pid if self._process else None,
            "server_alive": self._is_process_alive(),
            "server_healthy": self._check_health(),
            "restart_count": self._restart_count,
            "total_crashes": self._total_crashes,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "uptime": str(datetime.now() - self._started_at) if self._started_at else None,
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NormCode Server Watchdog — Process Guardian with Auto-Restart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python watchdog.py                       # Start with defaults
  python watchdog.py --port 9000           # Custom port
  python watchdog.py --check-interval 5    # Check every 5 seconds
  python watchdog.py --max-restarts 10     # Give up after 10 restarts
  python watchdog.py --verbose             # Debug logging

Crash reports are saved to: data/crashes/
Watchdog log:               data/watchdog.log
Server log:                 data/server.log
        """,
    )

    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--check-interval", type=int, default=10, help="Seconds between health checks (default: 10)")
    parser.add_argument("--restart-delay", type=int, default=3, help="Seconds before restart after crash (default: 3)")
    parser.add_argument("--max-restarts", type=int, default=0, help="Max restarts before giving up, 0=unlimited (default: 0)")
    parser.add_argument("--backoff-factor", type=float, default=1.5, help="Restart delay multiplier on repeated failures (default: 1.5)")
    parser.add_argument("--max-backoff", type=int, default=120, help="Maximum restart delay in seconds (default: 120)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    watchdog = ServerWatchdog(
        host=args.host,
        port=args.port,
        check_interval=args.check_interval,
        restart_delay=args.restart_delay,
        max_restarts=args.max_restarts,
        backoff_factor=args.backoff_factor,
        max_backoff=args.max_backoff,
        verbose=args.verbose,
    )

    watchdog.run()


if __name__ == "__main__":
    main()

