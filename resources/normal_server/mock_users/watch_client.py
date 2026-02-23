#!/usr/bin/env python3
"""
NormCode Watch Client

Rich terminal client for watching run execution with live updates.
More feature-rich than the basic client.py watcher.

Usage:
    python watch_client.py <run_id>
    python watch_client.py <run_id> --server http://host:port
"""

import sys
import io
import json
import argparse
import threading
import time
from datetime import datetime
from collections import deque
from typing import Optional, Dict, Any

# Fix Windows encoding
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
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class RunWatcher:
    """
    Watch a specific run with rich visualization.
    """
    
    def __init__(self, server_url: str, run_id: str):
        self.server_url = server_url.rstrip("/")
        self.run_id = run_id
        self.console = Console() if HAS_RICH else None
        
        # State
        self.status = "connecting"
        self.plan_id = "?"
        self.progress = {"completed": 0, "total": 0, "cycle": 0}
        self.current_inference = None
        self.events: deque = deque(maxlen=30)
        self.node_statuses: Dict[str, str] = {}
        
        # Threading
        self._stop = threading.Event()
        self._lock = threading.Lock()
    
    def fetch_initial(self):
        """Fetch initial run state."""
        try:
            resp = requests.get(f"{self.server_url}/api/runs/{self.run_id}", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            with self._lock:
                self.status = data.get("status", "?")
                self.plan_id = data.get("plan_id", "?")
                prog = data.get("progress", {})
                self.progress = {
                    "completed": prog.get("completed_count", 0),
                    "total": prog.get("total_count", 0),
                    "cycle": prog.get("cycle_count", 0),
                }
                self.current_inference = prog.get("current_inference")
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
    
    def stream_events(self):
        """Stream events via SSE."""
        url = f"{self.server_url}/api/runs/{self.run_id}/stream"
        
        try:
            with requests.get(url, stream=True, timeout=None) as resp:
                resp.raise_for_status()
                
                buffer = ""
                for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                    if self._stop.is_set():
                        break
                    
                    if chunk:
                        buffer += chunk
                        
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            
                            for line in message.split("\n"):
                                if line.startswith("data: "):
                                    try:
                                        data = json.loads(line[6:])
                                        self._handle_event(data)
                                    except json.JSONDecodeError:
                                        pass
        except Exception as e:
            with self._lock:
                self.events.appendleft({
                    "event": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    def _handle_event(self, data: Dict[str, Any]):
        """Handle incoming event."""
        with self._lock:
            event_type = data.get("event", "?")
            self.events.appendleft(data)
            
            # Update state based on event
            if event_type == "connected":
                self.status = data.get("status", self.status)
                self.node_statuses = data.get("node_statuses", {})
                prog = data.get("progress", {})
                self.progress = {
                    "completed": prog.get("completed_count", 0),
                    "total": prog.get("total_count", 0),
                    "cycle": prog.get("cycle_count", 0),
                }
            
            elif event_type == "execution:progress":
                self.progress = {
                    "completed": data.get("completed_count", 0),
                    "total": data.get("total_count", 0),
                    "cycle": data.get("cycle_count", 0),
                }
                self.current_inference = data.get("current_inference")
            
            elif event_type == "node:statuses":
                statuses = data.get("statuses", {})
                self.node_statuses.update(statuses)
            
            elif event_type == "inference:started":
                self.current_inference = data.get("flow_index")
            
            elif event_type == "run:completed":
                self.status = "completed"
            
            elif event_type == "run:failed":
                self.status = "failed"
            
            elif event_type == "execution:stopped":
                self.status = "stopped"
            
            elif event_type == "execution:paused":
                self.status = "paused"
            
            elif event_type == "execution:resumed":
                self.status = "running"
    
    def render_header(self) -> Panel:
        """Render header panel."""
        with self._lock:
            status = self.status
            plan_id = self.plan_id
            run_id = self.run_id
        
        status_style = {
            "running": "green",
            "paused": "yellow",
            "stepping": "cyan",
            "completed": "blue",
            "failed": "red",
            "stopped": "red",
        }.get(status, "white")
        
        text = Text()
        text.append("Run: ", style="dim")
        text.append(run_id[:16], style="cyan bold")
        text.append("  │  Plan: ", style="dim")
        text.append(plan_id[:20], style="white")
        text.append("  │  Status: ", style="dim")
        text.append(status.upper(), style=f"bold {status_style}")
        
        return Panel(text, box=box.MINIMAL)
    
    def render_progress(self) -> Panel:
        """Render progress panel."""
        with self._lock:
            completed = self.progress["completed"]
            total = self.progress["total"]
            cycle = self.progress["cycle"]
            current = self.current_inference
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
        )
        task = progress.add_task("Inferences", completed=completed, total=max(total, 1))
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Cycle", str(cycle))
        table.add_row("Current", current[:30] if current else "—")
        
        return Panel(
            table,
            title=f"[bold]Progress: {completed}/{total}[/]",
            border_style="green"
        )
    
    def render_events(self) -> Panel:
        """Render events panel."""
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Event", style="cyan", width=20)
        table.add_column("Details", overflow="ellipsis")
        
        with self._lock:
            events = list(self.events)[:20]
        
        for event in events:
            ts = event.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts = dt.strftime("%H:%M:%S")
                except:
                    ts = ts[-8:]
            
            event_type = event.get("event", "?")
            
            # Style by type
            if "error" in event_type or "failed" in event_type:
                style = "red"
            elif "completed" in event_type:
                style = "green"
            elif "started" in event_type:
                style = "blue"
            elif "paused" in event_type:
                style = "yellow"
            else:
                style = "white"
            
            # Build details
            details = []
            if fi := event.get("flow_index"):
                details.append(fi[:25])
            if cn := event.get("concept_name"):
                details.append(cn[:20])
            if dur := event.get("duration"):
                details.append(f"{dur:.2f}s")
            if err := event.get("error"):
                details.append(str(err)[:30])
            
            table.add_row(ts, f"[{style}]{event_type}[/]", " ".join(details) or "—")
        
        return Panel(table, title="[bold]Events[/]", border_style="cyan")
    
    def render_nodes(self) -> Panel:
        """Render node statuses panel."""
        with self._lock:
            statuses = dict(self.node_statuses)
        
        completed = sum(1 for s in statuses.values() if s == "completed")
        pending = sum(1 for s in statuses.values() if s == "pending")
        in_progress = sum(1 for s in statuses.values() if s not in ("completed", "pending"))
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="white", justify="right")
        
        table.add_row("[green]● Completed[/]", str(completed))
        table.add_row("[yellow]● In Progress[/]", str(in_progress))
        table.add_row("[dim]○ Pending[/]", str(pending))
        
        return Panel(table, title="[bold]Nodes[/]", border_style="blue")
    
    def render(self) -> Layout:
        """Render full layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )
        
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )
        
        layout["left"].split_column(
            Layout(name="progress", size=8),
            Layout(name="nodes"),
        )
        
        layout["header"].update(self.render_header())
        layout["progress"].update(self.render_progress())
        layout["nodes"].update(self.render_nodes())
        layout["right"].update(self.render_events())
        
        return layout
    
    def run(self):
        """Run the watcher."""
        if not HAS_RICH:
            self.run_simple()
            return
        
        # Fetch initial state
        if not self.fetch_initial():
            return
        
        # Start event streaming
        stream_thread = threading.Thread(target=self.stream_events, daemon=True)
        stream_thread.start()
        
        # Run live display
        try:
            with Live(self.render(), console=self.console, refresh_per_second=4) as live:
                while not self._stop.is_set():
                    live.update(self.render())
                    
                    # Check if run completed
                    with self._lock:
                        if self.status in ("completed", "failed", "stopped"):
                            # Show final state for a moment
                            time.sleep(2)
                            break
                    
                    time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self._stop.set()
            self.console.print(f"\n[yellow]Watcher stopped.[/]")
    
    def run_simple(self):
        """Simple text mode."""
        if not self.fetch_initial():
            return
        
        print(f"Watching run {self.run_id}")
        print(f"Plan: {self.plan_id}, Status: {self.status}")
        print("Press Ctrl+C to stop\n")
        
        url = f"{self.server_url}/api/runs/{self.run_id}/stream"
        
        try:
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
                                        event = data.get("event", "?")
                                        ts = datetime.now().strftime("%H:%M:%S")
                                        print(f"[{ts}] {event}")
                                        
                                        if event in ("run:completed", "run:failed", "execution:stopped"):
                                            print(f"\nRun {event.split(':')[1]}!")
                                            return
                                    except json.JSONDecodeError:
                                        pass
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="Watch a NormCode run execution")
    parser.add_argument("run_id", help="Run ID to watch")
    parser.add_argument("--server", "-s", default="http://localhost:8080", help="Server URL")
    
    args = parser.parse_args()
    
    watcher = RunWatcher(args.server, args.run_id)
    watcher.run()


if __name__ == "__main__":
    main()

