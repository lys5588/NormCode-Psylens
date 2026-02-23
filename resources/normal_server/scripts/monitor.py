#!/usr/bin/env python3
"""
NormCode Server Monitor

Real-time TUI dashboard for monitoring server activity.

Usage:
    python monitor.py                        # Connect to localhost:8080
    python monitor.py --server http://host:port
    python monitor.py --compact              # Compact mode for smaller terminals
"""

import sys
import io
import json
import argparse
import threading
import time
from datetime import datetime
from collections import deque
from typing import Optional, Dict, Any, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.style import Style
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("rich not installed. Run: pip install rich", file=sys.stderr)
    print("Falling back to simple text mode...\n")


class ServerMonitor:
    """
    Real-time server monitor with Rich TUI.
    """
    
    def __init__(self, server_url: str = "http://localhost:8080", compact: bool = False):
        self.server_url = server_url.rstrip("/")
        self.compact = compact
        self.console = Console() if HAS_RICH else None
        
        # State
        self.connected = False
        self.stats: Dict[str, Any] = {}
        self.active_runs: Dict[str, Dict] = {}
        self.events: deque = deque(maxlen=50)
        self.llm_calls: deque = deque(maxlen=20)
        self.errors: deque = deque(maxlen=10)
        
        # Threading
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """Test server connection."""
        try:
            resp = requests.get(f"{self.server_url}/health", timeout=5)
            resp.raise_for_status()
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def fetch_initial_state(self):
        """Fetch initial state from server."""
        try:
            # Get stats
            resp = requests.get(f"{self.server_url}/api/monitor/stats", timeout=5)
            if resp.ok:
                data = resp.json()
                with self._lock:
                    self.stats = data.get("stats", {})
                    self.active_runs = data.get("active_runs", {})
        except Exception as e:
            self._add_error(f"Failed to fetch initial state: {e}")
    
    def _add_event(self, event: Dict):
        """Add event to history."""
        with self._lock:
            self.events.appendleft(event)
            
            # Track specific events
            event_type = event.get("event", "")
            
            if event_type == "llm:call":
                self.llm_calls.appendleft(event)
            
            if event_type.endswith(":error") or event_type.endswith(":failed"):
                self.errors.appendleft(event)
            
            # Update active runs
            if event_type == "run:started":
                run_id = event.get("run_id")
                if run_id:
                    self.active_runs[run_id] = {
                        "plan_id": event.get("plan_id", "?"),
                        "status": "running",
                        "started_at": event.get("timestamp"),
                    }
            elif event_type in ("run:completed", "run:failed", "execution:stopped"):
                run_id = event.get("run_id")
                if run_id and run_id in self.active_runs:
                    del self.active_runs[run_id]
    
    def _add_error(self, message: str):
        """Add error to history."""
        with self._lock:
            self.errors.appendleft({
                "event": "monitor:error",
                "message": message,
                "timestamp": datetime.now().isoformat(),
            })
    
    def stream_events(self):
        """Stream events from server via SSE."""
        url = f"{self.server_url}/api/monitor/stream"
        
        try:
            with requests.get(url, stream=True, timeout=None) as resp:
                resp.raise_for_status()
                
                buffer = ""
                for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                    if self._stop_event.is_set():
                        break
                    
                    if chunk:
                        buffer += chunk
                        
                        # Process complete SSE messages
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            
                            for line in message.split("\n"):
                                if line.startswith("data: "):
                                    try:
                                        data = json.loads(line[6:])
                                        self._add_event(data)
                                        
                                        # Handle initial connection
                                        if data.get("event") == "monitor:connected":
                                            with self._lock:
                                                self.stats = data.get("stats", {})
                                                for run in data.get("active_runs", []):
                                                    self.active_runs[run["run_id"]] = run
                                    except json.JSONDecodeError:
                                        pass
                                elif line.startswith(":"):
                                    # Keepalive comment
                                    pass
                                    
        except Exception as e:
            self._add_error(f"Stream disconnected: {e}")
            self.connected = False
    
    def build_layout(self) -> Layout:
        """Build the Rich layout."""
        layout = Layout()
        
        if self.compact:
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
            )
            layout["main"].split_row(
                Layout(name="runs", ratio=1),
                Layout(name="events", ratio=2),
            )
        else:
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3),
            )
            layout["body"].split_row(
                Layout(name="left", ratio=1),
                Layout(name="right", ratio=2),
            )
            layout["left"].split_column(
                Layout(name="stats", ratio=1),
                Layout(name="runs", ratio=2),
            )
            layout["right"].split_column(
                Layout(name="events", ratio=2),
                Layout(name="llm", ratio=1),
            )
        
        return layout
    
    def render_header(self) -> Panel:
        """Render the header panel."""
        status = "[bold green]● CONNECTED[/]" if self.connected else "[bold red]● DISCONNECTED[/]"
        
        with self._lock:
            active_count = len(self.active_runs)
            total_events = self.stats.get("total_events", 0)
        
        text = Text()
        text.append("NormCode Server Monitor", style="bold cyan")
        text.append(f"  {status}")
        text.append(f"  │  Server: {self.server_url}", style="dim")
        text.append(f"  │  Runs: {active_count}", style="yellow")
        text.append(f"  │  Events: {total_events}", style="blue")
        
        return Panel(text, box=box.MINIMAL)
    
    def render_stats(self) -> Panel:
        """Render statistics panel."""
        with self._lock:
            stats = self.stats.copy()
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Runs Started", str(stats.get("runs_started", 0)))
        table.add_row("Runs Completed", str(stats.get("runs_completed", 0)))
        table.add_row("Runs Failed", str(stats.get("runs_failed", 0)))
        table.add_row("Inferences", str(stats.get("inferences_executed", 0)))
        table.add_row("LLM Calls", str(stats.get("llm_calls", 0)))
        
        tokens_in = stats.get("llm_tokens_in", 0)
        tokens_out = stats.get("llm_tokens_out", 0)
        if tokens_in or tokens_out:
            table.add_row("Tokens In", f"{tokens_in:,}")
            table.add_row("Tokens Out", f"{tokens_out:,}")
        
        return Panel(table, title="[bold]Statistics[/]", border_style="blue")
    
    def render_runs(self) -> Panel:
        """Render active runs panel."""
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
        table.add_column("Run ID", style="cyan", max_width=12)
        table.add_column("Plan", style="white", max_width=20)
        table.add_column("Status", style="yellow")
        
        with self._lock:
            runs = list(self.active_runs.items())
        
        if not runs:
            table.add_row("—", "[dim]No active runs[/]", "")
        else:
            for run_id, run in runs[:10]:
                status = run.get("status", "?")
                status_style = {
                    "running": "green",
                    "paused": "yellow",
                    "stepping": "cyan",
                }.get(status, "white")
                
                table.add_row(
                    run_id[:10] + "…" if len(run_id) > 10 else run_id,
                    run.get("plan_id", "?")[:18],
                    f"[{status_style}]{status}[/]"
                )
        
        return Panel(table, title="[bold]Active Runs[/]", border_style="green")
    
    def render_events(self) -> Panel:
        """Render recent events panel."""
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Event", style="cyan", max_width=25)
        table.add_column("Details", style="white", overflow="ellipsis")
        
        with self._lock:
            events = list(self.events)[:15]
        
        if not events:
            table.add_row("—", "[dim]No events yet[/]", "")
        else:
            for event in events:
                ts = event.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        ts = dt.strftime("%H:%M:%S")
                    except:
                        ts = ts[-8:]
                
                event_type = event.get("event", "?")
                
                # Colorize event types
                if event_type.startswith("run:"):
                    style = "green"
                elif event_type.startswith("inference:"):
                    style = "blue"
                elif event_type.startswith("llm:"):
                    style = "magenta"
                elif "error" in event_type or "failed" in event_type:
                    style = "red"
                else:
                    style = "white"
                
                # Build details
                details = []
                if run_id := event.get("run_id"):
                    details.append(f"run:{run_id[:8]}")
                if flow_idx := event.get("flow_index"):
                    details.append(f"@{flow_idx}")
                if concept := event.get("concept_name"):
                    details.append(concept[:20])
                
                table.add_row(
                    ts,
                    f"[{style}]{event_type}[/]",
                    " ".join(details) or "—"
                )
        
        return Panel(table, title="[bold]Events[/]", border_style="cyan")
    
    def render_llm_calls(self) -> Panel:
        """Render LLM calls panel."""
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Model", style="magenta", max_width=15)
        table.add_column("In", style="yellow", justify="right", width=6)
        table.add_column("Out", style="green", justify="right", width=6)
        table.add_column("ms", style="cyan", justify="right", width=6)
        
        with self._lock:
            calls = list(self.llm_calls)[:8]
        
        if not calls:
            table.add_row("—", "[dim]No LLM calls yet[/]", "", "", "")
        else:
            for call in calls:
                ts = call.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        ts = dt.strftime("%H:%M:%S")
                    except:
                        ts = ts[-8:]
                
                table.add_row(
                    ts,
                    call.get("model", "?")[:13],
                    str(call.get("tokens_in", "?")),
                    str(call.get("tokens_out", "?")),
                    str(call.get("latency_ms", "?")),
                )
        
        return Panel(table, title="[bold]LLM Calls[/]", border_style="magenta")
    
    def render_footer(self) -> Panel:
        """Render footer with help."""
        text = Text()
        text.append(" q", style="bold cyan")
        text.append(" quit  ", style="dim")
        text.append(" r", style="bold cyan")
        text.append(" refresh  ", style="dim")
        text.append(" c", style="bold cyan")
        text.append(" clear stats  ", style="dim")
        
        with self._lock:
            if self.errors:
                latest_error = self.errors[0]
                text.append("  │  ", style="dim")
                text.append(f"Last error: {latest_error.get('message', '?')[:50]}", style="red")
        
        return Panel(text, box=box.MINIMAL)
    
    def render(self) -> Layout:
        """Render the full layout."""
        layout = self.build_layout()
        
        layout["header"].update(self.render_header())
        
        if self.compact:
            layout["runs"].update(self.render_runs())
            layout["events"].update(self.render_events())
        else:
            layout["stats"].update(self.render_stats())
            layout["runs"].update(self.render_runs())
            layout["events"].update(self.render_events())
            layout["llm"].update(self.render_llm_calls())
            layout["footer"].update(self.render_footer())
        
        return layout
    
    def run(self):
        """Run the monitor."""
        if not HAS_RICH:
            self.run_simple()
            return
        
        # Connect
        self.console.print(f"[cyan]Connecting to {self.server_url}...[/]")
        if not self.connect():
            self.console.print(f"[red]Failed to connect to {self.server_url}[/]")
            self.console.print("Is the server running?")
            return
        
        self.console.print("[green]Connected![/]")
        self.fetch_initial_state()
        
        # Start streaming thread
        stream_thread = threading.Thread(target=self.stream_events, daemon=True)
        stream_thread.start()
        
        # Run live display
        try:
            with Live(self.render(), console=self.console, refresh_per_second=2) as live:
                while not self._stop_event.is_set():
                    live.update(self.render())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self._stop_event.set()
            self.console.print("\n[yellow]Monitor stopped.[/]")
    
    def run_simple(self):
        """Run in simple text mode (no Rich)."""
        print(f"Connecting to {self.server_url}...")
        
        if not self.connect():
            print(f"Failed to connect to {self.server_url}")
            return
        
        print("Connected! Streaming events (Ctrl+C to stop)...\n")
        
        # Start streaming in main thread
        try:
            self.stream_events_simple()
        except KeyboardInterrupt:
            print("\nStopped.")
    
    def stream_events_simple(self):
        """Stream events in simple text mode."""
        url = f"{self.server_url}/api/monitor/stream"
        
        with requests.get(url, stream=True, timeout=None) as resp:
            resp.raise_for_status()
            
            buffer = ""
            for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    buffer += chunk
                    
                    while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)
                        
                        for line in message.split("\n"):
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    event_type = data.get("event", "?")
                                    ts = data.get("timestamp", "")[-8:]
                                    run_id = data.get("run_id", "")[:8]
                                    
                                    print(f"[{ts}] {event_type:30} {run_id}")
                                except json.JSONDecodeError:
                                    pass


def main():
    parser = argparse.ArgumentParser(
        description="NormCode Server Monitor - Real-time TUI dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor.py                           # Monitor localhost:8080
  python monitor.py --server http://host:9000 # Monitor specific server
  python monitor.py --compact                 # Compact mode for small terminals
        """
    )
    
    parser.add_argument(
        "--server", "-s",
        type=str,
        default="http://localhost:8080",
        help="Server URL (default: http://localhost:8080)"
    )
    
    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Use compact layout for smaller terminals"
    )
    
    args = parser.parse_args()
    
    monitor = ServerMonitor(server_url=args.server, compact=args.compact)
    monitor.run()


if __name__ == "__main__":
    main()

