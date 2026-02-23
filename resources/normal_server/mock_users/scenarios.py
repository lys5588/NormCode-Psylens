#!/usr/bin/env python3
"""
NormCode Test Scenarios

Automated test scenarios for the deployment server.
Useful for testing, demos, and load testing.

Usage:
    python scenarios.py list                    # List available scenarios
    python scenarios.py run <scenario>          # Run a specific scenario
    python scenarios.py run all                 # Run all scenarios
    python scenarios.py demo                    # Interactive demo mode
"""

import sys
import io
import json
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# Import the client
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from client import NormCodeClient


class ScenarioRunner:
    """
    Runs test scenarios against the deployment server.
    """
    
    def __init__(self, server_url: str = "http://localhost:8080", verbose: bool = True):
        self.client = NormCodeClient(server_url)
        self.server_url = server_url
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
    
    def log(self, msg: str, level: str = "info"):
        """Log a message."""
        if not self.verbose:
            return
        
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "info": "\033[0m",
            "success": "\033[92m",
            "warning": "\033[93m",
            "error": "\033[91m",
        }
        color = colors.get(level, colors["info"])
        print(f"[{ts}] {color}{msg}\033[0m")
    
    def check_server(self) -> bool:
        """Check if server is reachable."""
        try:
            health = self.client.health()
            self.log(f"Server health: {health.get('status', 'unknown')}", "success")
            return True
        except Exception as e:
            self.log(f"Server unreachable: {e}", "error")
            return False
    
    def record_result(self, scenario: str, passed: bool, duration: float, details: str = ""):
        """Record a test result."""
        self.results.append({
            "scenario": scenario,
            "passed": passed,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
    
    # =========================================================================
    # Scenarios
    # =========================================================================
    
    def scenario_server_health(self) -> bool:
        """Test basic server health endpoint."""
        start = time.time()
        try:
            health = self.client.health()
            info = self.client.info()
            
            self.log(f"  Health: {health}", "info")
            self.log(f"  Plans: {info.get('plans_count', 0)}", "info")
            
            self.record_result("server_health", True, time.time() - start)
            return True
        except Exception as e:
            self.record_result("server_health", False, time.time() - start, str(e))
            return False
    
    def scenario_list_plans(self) -> bool:
        """Test listing available plans."""
        start = time.time()
        try:
            plans = self.client.list_plans()
            
            self.log(f"  Found {len(plans)} plans", "info")
            for plan in plans[:5]:
                self.log(f"    - {plan.get('id', '?')[:8]}: {plan.get('name', 'Unnamed')}", "info")
            
            self.record_result("list_plans", True, time.time() - start, f"{len(plans)} plans")
            return True
        except Exception as e:
            self.record_result("list_plans", False, time.time() - start, str(e))
            return False
    
    def scenario_run_demo(self) -> bool:
        """Test running a plan with demo/mock LLM."""
        start = time.time()
        try:
            plans = self.client.list_plans()
            if not plans:
                self.log("  No plans available", "warning")
                self.record_result("run_demo", False, time.time() - start, "No plans")
                return False
            
            plan = plans[0]
            plan_id = plan.get("id")
            self.log(f"  Starting plan: {plan.get('name', plan_id)}", "info")
            
            # Start run with demo LLM
            result = self.client.start_run(plan_id, llm_model="demo", max_cycles=3)
            run_id = result.get("run_id")
            
            self.log(f"  Run started: {run_id[:8]}", "info")
            
            # Poll for completion (with timeout)
            timeout = 60
            poll_start = time.time()
            final_status = None
            
            while time.time() - poll_start < timeout:
                status = self.client.get_run(run_id)
                final_status = status.get("status")
                
                if final_status in ("completed", "failed", "stopped"):
                    break
                
                prog = status.get("progress", {})
                self.log(f"  Progress: {prog.get('completed_count', 0)}/{prog.get('total_count', 0)}", "info")
                time.sleep(2)
            
            if final_status == "completed":
                self.log(f"  Run completed!", "success")
                self.record_result("run_demo", True, time.time() - start)
                return True
            else:
                self.log(f"  Run ended with status: {final_status}", "warning")
                self.record_result("run_demo", False, time.time() - start, f"Status: {final_status}")
                return False
            
        except Exception as e:
            self.record_result("run_demo", False, time.time() - start, str(e))
            return False
    
    def scenario_pause_resume(self) -> bool:
        """Test pause/resume functionality."""
        start = time.time()
        try:
            plans = self.client.list_plans()
            if not plans:
                self.record_result("pause_resume", False, time.time() - start, "No plans")
                return False
            
            plan_id = plans[0].get("id")
            
            # Start run
            result = self.client.start_run(plan_id, llm_model="demo")
            run_id = result.get("run_id")
            self.log(f"  Run started: {run_id[:8]}", "info")
            
            # Wait a moment then pause
            time.sleep(1)
            
            resp = requests.post(f"{self.server_url}/api/runs/{run_id}/pause")
            if resp.ok:
                self.log("  Paused", "info")
            
            time.sleep(1)
            
            # Check status
            status = self.client.get_run(run_id)
            if status.get("status") != "paused":
                self.log(f"  Expected paused, got: {status.get('status')}", "warning")
            
            # Resume
            resp = requests.post(f"{self.server_url}/api/runs/{run_id}/continue")
            if resp.ok:
                self.log("  Resumed", "info")
            
            # Stop
            time.sleep(1)
            self.client.stop_run(run_id)
            self.log("  Stopped", "info")
            
            self.record_result("pause_resume", True, time.time() - start)
            return True
            
        except Exception as e:
            self.record_result("pause_resume", False, time.time() - start, str(e))
            return False
    
    def scenario_concurrent_runs(self) -> bool:
        """Test running multiple plans concurrently."""
        start = time.time()
        try:
            plans = self.client.list_plans()
            if not plans:
                self.record_result("concurrent_runs", False, time.time() - start, "No plans")
                return False
            
            plan_id = plans[0].get("id")
            run_ids = []
            
            # Start multiple runs
            num_runs = min(3, len(plans))
            for i in range(num_runs):
                result = self.client.start_run(plan_id, llm_model="demo", max_cycles=2)
                run_ids.append(result.get("run_id"))
                self.log(f"  Started run {i+1}: {result.get('run_id', '?')[:8]}", "info")
            
            # Wait a bit then check all are running
            time.sleep(2)
            
            runs = self.client.list_runs()
            active = [r for r in runs if r.get("status") in ("running", "pending")]
            self.log(f"  Active runs: {len(active)}", "info")
            
            # Stop all
            for run_id in run_ids:
                try:
                    self.client.stop_run(run_id)
                except:
                    pass
            
            self.record_result("concurrent_runs", True, time.time() - start, f"{num_runs} runs")
            return True
            
        except Exception as e:
            self.record_result("concurrent_runs", False, time.time() - start, str(e))
            return False
    
    def scenario_monitor_stream(self) -> bool:
        """Test the server monitor stream endpoint."""
        start = time.time()
        try:
            # Connect to monitor stream
            url = f"{self.server_url}/api/monitor/stream"
            
            with requests.get(url, stream=True, timeout=10) as resp:
                resp.raise_for_status()
                
                # Read first event
                buffer = ""
                for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                    buffer += chunk
                    
                    if "\n\n" in buffer:
                        message = buffer.split("\n\n")[0]
                        
                        if message.startswith("data: "):
                            data = json.loads(message[6:])
                            event = data.get("event")
                            
                            if event == "monitor:connected":
                                self.log(f"  Monitor connected", "success")
                                self.log(f"  Stats: {data.get('stats', {})}", "info")
                                self.record_result("monitor_stream", True, time.time() - start)
                                return True
                        break
            
            self.record_result("monitor_stream", False, time.time() - start, "No connection event")
            return False
            
        except Exception as e:
            self.record_result("monitor_stream", False, time.time() - start, str(e))
            return False
    
    # =========================================================================
    # Runner
    # =========================================================================
    
    def get_scenarios(self) -> Dict[str, callable]:
        """Get all available scenarios."""
        return {
            "server_health": self.scenario_server_health,
            "list_plans": self.scenario_list_plans,
            "run_demo": self.scenario_run_demo,
            "pause_resume": self.scenario_pause_resume,
            "concurrent_runs": self.scenario_concurrent_runs,
            "monitor_stream": self.scenario_monitor_stream,
        }
    
    def run_scenario(self, name: str) -> bool:
        """Run a single scenario."""
        scenarios = self.get_scenarios()
        
        if name not in scenarios:
            self.log(f"Unknown scenario: {name}", "error")
            return False
        
        self.log(f"\n▶ Running: {name}", "info")
        
        try:
            result = scenarios[name]()
            if result:
                self.log(f"✓ {name} passed", "success")
            else:
                self.log(f"✗ {name} failed", "error")
            return result
        except Exception as e:
            self.log(f"✗ {name} error: {e}", "error")
            return False
    
    def run_all(self) -> Dict[str, bool]:
        """Run all scenarios."""
        if not self.check_server():
            return {}
        
        results = {}
        for name in self.get_scenarios():
            results[name] = self.run_scenario(name)
        
        # Summary
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        self.log(f"\n{'='*40}", "info")
        self.log(f"Results: {passed}/{total} passed", "success" if passed == total else "warning")
        
        return results
    
    def print_summary(self):
        """Print test summary."""
        if not self.results:
            return
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        
        for r in self.results:
            status = "✓ PASS" if r["passed"] else "✗ FAIL"
            print(f"{status}  {r['scenario']:20}  {r['duration']:.2f}s  {r['details']}")
        
        passed = sum(1 for r in self.results if r["passed"])
        print("="*60)
        print(f"Total: {passed}/{len(self.results)} passed")


def main():
    parser = argparse.ArgumentParser(description="NormCode Test Scenarios")
    parser.add_argument("command", choices=["list", "run", "demo"], help="Command to execute")
    parser.add_argument("scenario", nargs="?", default="all", help="Scenario name or 'all'")
    parser.add_argument("--server", "-s", default="http://localhost:8080", help="Server URL")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less verbose output")
    
    args = parser.parse_args()
    
    runner = ScenarioRunner(args.server, verbose=not args.quiet)
    
    if args.command == "list":
        print("Available scenarios:")
        for name, func in runner.get_scenarios().items():
            doc = func.__doc__ or "No description"
            print(f"  {name:20} - {doc.strip().split(chr(10))[0]}")
        return
    
    if args.command == "demo":
        print("Demo mode - running basic scenarios...\n")
        if not runner.check_server():
            sys.exit(1)
        
        runner.run_scenario("server_health")
        runner.run_scenario("list_plans")
        runner.print_summary()
        return
    
    if args.command == "run":
        if args.scenario == "all":
            runner.run_all()
        else:
            if not runner.check_server():
                sys.exit(1)
            runner.run_scenario(args.scenario)
        
        runner.print_summary()
        
        # Exit with error code if any failed
        if any(not r["passed"] for r in runner.results):
            sys.exit(1)


if __name__ == "__main__":
    main()

