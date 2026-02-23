#!/usr/bin/env python3
"""
NormCode Client UI

Web-based client for managing plans and runs.
Opens in a dedicated pywebview window (or browser fallback).

Usage:
    python client_ui.py                     # Default localhost:8080
    python client_ui.py --port 9000         # Custom port
    python client_ui.py --browser           # Force browser instead of window
"""

import sys
import argparse
from pathlib import Path

# Get icon path (go up from mock_users to normal_server/resources)
SCRIPT_DIR = Path(__file__).resolve().parent
ICON_PATH = SCRIPT_DIR.parent / "resources" / "icon.ico"


def set_windows_icon(icon_path: str):
    """Set application icon using Windows API (for taskbar)."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        
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
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NormCode.Client")
            print(f"Windows icon set: {hicon}")
    except Exception as e:
        print(f"Could not set Windows icon: {e}")

# The HTML UI is served by the server, this script just opens the window
CLIENT_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NormCode Client</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%230d1117' width='100' height='100' rx='20'/><path fill='%2358a6ff' d='M25 30h50v10H25zM25 50h35v10H25zM25 70h45v10H25z'/></svg>">
    <style>
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
            --bg-input: #0d1117;
            --border: #30363d;
            --text: #c9d1d9;
            --text-dim: #8b949e;
            --accent-green: #3fb950;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
            --accent-red: #f85149;
            --accent-purple: #a371f7;
            --accent-cyan: #39c5cf;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
        }
        
        /* Layout */
        .app {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 280px;
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Header */
        .header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-red);
        }
        
        .status-dot.connected { background: var(--accent-green); }
        
        /* Plans list */
        .section-header {
            padding: 12px 16px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-dim);
            border-bottom: 1px solid var(--border);
        }
        
        .plans-list {
            flex: 1;
            overflow-y: auto;
        }
        
        .plan-item {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.15s;
        }
        
        .plan-item:hover { background: var(--bg-hover); }
        .plan-item.selected { background: var(--bg-hover); border-left: 3px solid var(--accent-blue); }
        
        .plan-name {
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .plan-id {
            font-size: 0.75rem;
            color: var(--text-dim);
            font-family: 'Consolas', monospace;
        }
        
        /* Run controls */
        .run-controls {
            padding: 16px;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
        }
        
        .form-group {
            margin-bottom: 12px;
        }
        
        .form-group label {
            display: block;
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-bottom: 4px;
        }
        
        select, input {
            width: 100%;
            padding: 8px 12px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 0.9rem;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: var(--accent-blue);
        }
        
        .btn {
            width: 100%;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .btn-primary {
            background: var(--accent-green);
            color: #000;
        }
        
        .btn-primary:hover { background: #4ac65b; }
        .btn-primary:disabled { background: var(--border); color: var(--text-dim); cursor: not-allowed; }
        
        /* Main content */
        .content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .content-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .content-header h2 {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        /* Runs table */
        .runs-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .runs-table th {
            text-align: left;
            padding: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-dim);
            border-bottom: 1px solid var(--border);
        }
        
        .runs-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .runs-table tr:hover { background: var(--bg-hover); }
        
        .run-id-cell {
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            color: var(--accent-cyan);
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-badge.running { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .status-badge.paused { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        .status-badge.completed { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
        .status-badge.failed { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .status-badge.stopped { background: rgba(139, 148, 158, 0.2); color: var(--text-dim); }
        .status-badge.pending { background: rgba(139, 148, 158, 0.2); color: var(--text-dim); }
        
        .action-btn {
            padding: 4px 10px;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: transparent;
            color: var(--text);
            font-size: 0.8rem;
            cursor: pointer;
            margin-right: 6px;
        }
        
        .action-btn:hover { background: var(--bg-hover); }
        .action-btn.danger { color: var(--accent-red); border-color: var(--accent-red); }
        
        /* Progress bar */
        .progress-bar {
            width: 100px;
            height: 6px;
            background: var(--bg-dark);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent-green);
            transition: width 0.3s;
        }
        
        /* Result panel */
        .result-panel {
            margin-top: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
        }
        
        .result-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            font-weight: 600;
        }
        
        .result-body {
            padding: 16px;
            max-height: 300px;
            overflow: auto;
        }
        
        .result-body pre {
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-dim);
        }
        
        .empty-state .icon { font-size: 3rem; margin-bottom: 16px; }
        
        /* Toast notifications */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        }
        
        .toast.success { border-color: var(--accent-green); }
        .toast.error { border-color: var(--accent-red); }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <div class="header">
                <h1><span class="status-dot" id="statusDot"></span> NormCode Client</h1>
            </div>
            
            <div class="section-header">Plans</div>
            <div class="plans-list" id="plansList">
                <div class="empty-state">Loading...</div>
            </div>
            
            <div class="run-controls">
                <div class="form-group">
                    <label>LLM Model</label>
                    <select id="llmSelect">
                        <option value="demo">demo (mock)</option>
                        <option value="qwen-plus">qwen-plus</option>
                        <option value="qwen-turbo-latest">qwen-turbo-latest</option>
                        <option value="gpt-4o">gpt-4o</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Max Cycles</label>
                    <input type="number" id="maxCycles" value="100" min="1" max="1000">
                </div>
                <button class="btn btn-primary" id="runBtn" disabled>▶ Run Selected Plan</button>
            </div>
        </aside>
        
        <main class="main">
            <div class="header">
                <h2>Runs</h2>
                <button class="action-btn" onclick="refreshRuns()">↻ Refresh</button>
            </div>
            
            <div class="content">
                <table class="runs-table">
                    <thead>
                        <tr>
                            <th>Run ID</th>
                            <th>Plan</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Started</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="runsTable">
                        <tr><td colspan="6" class="empty-state">No runs yet</td></tr>
                    </tbody>
                </table>
                
                <div class="result-panel" id="resultPanel" style="display: none;">
                    <div class="result-header">Result</div>
                    <div class="result-body">
                        <pre id="resultContent"></pre>
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <script>
        const API_BASE = window.location.origin + '/api';
        let selectedPlanId = null;
        let plans = {};
        let pollingIntervals = {};
        
        // Fetch plans
        async function fetchPlans() {
            try {
                const resp = await fetch(`${API_BASE}/plans`);
                const data = await resp.json();
                plans = {};
                data.forEach(p => plans[p.id] = p);
                renderPlans(data);
                document.getElementById('statusDot').classList.add('connected');
            } catch (e) {
                document.getElementById('plansList').innerHTML = 
                    '<div class="empty-state">Failed to connect</div>';
            }
        }
        
        function renderPlans(plansList) {
            const container = document.getElementById('plansList');
            if (plansList.length === 0) {
                container.innerHTML = '<div class="empty-state">No plans deployed</div>';
                return;
            }
            
            container.innerHTML = plansList.map(p => `
                <div class="plan-item ${p.id === selectedPlanId ? 'selected' : ''}" 
                     onclick="selectPlan('${p.id}')">
                    <div class="plan-name">${p.name || 'Unnamed'}</div>
                    <div class="plan-id">${p.id.slice(0, 12)}...</div>
                </div>
            `).join('');
        }
        
        function selectPlan(planId) {
            selectedPlanId = planId;
            document.getElementById('runBtn').disabled = false;
            renderPlans(Object.values(plans));
        }
        
        // Runs
        async function fetchRuns() {
            try {
                const resp = await fetch(`${API_BASE}/runs`);
                const data = await resp.json();
                renderRuns(data);
            } catch (e) {
                console.error('Failed to fetch runs:', e);
            }
        }
        
        function renderRuns(runsList) {
            const tbody = document.getElementById('runsTable');
            if (runsList.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No runs yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = runsList.map(r => {
                const planName = plans[r.plan_id]?.name || r.plan_id?.slice(0, 8) || '?';
                const progress = r.progress || {};
                const pct = progress.total_count ? 
                    Math.round((progress.completed_count / progress.total_count) * 100) : 0;
                const started = r.started_at ? 
                    new Date(r.started_at).toLocaleTimeString() : '—';
                
                return `
                    <tr>
                        <td class="run-id-cell">${r.run_id.slice(0, 12)}...</td>
                        <td>${planName}</td>
                        <td><span class="status-badge ${r.status}">${r.status}</span></td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${pct}%"></div>
                            </div>
                            <small>${progress.completed_count || 0}/${progress.total_count || 0}</small>
                        </td>
                        <td>${started}</td>
                        <td>
                            ${r.status === 'completed' ? 
                                `<button class="action-btn" onclick="viewResult('${r.run_id}')">View</button>` : ''}
                            ${['running', 'paused'].includes(r.status) ? 
                                `<button class="action-btn danger" onclick="stopRun('${r.run_id}')">Stop</button>` : ''}
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        async function startRun() {
            if (!selectedPlanId) return;
            
            const llm = document.getElementById('llmSelect').value;
            const maxCycles = parseInt(document.getElementById('maxCycles').value) || 100;
            
            try {
                const resp = await fetch(`${API_BASE}/runs`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        plan_id: selectedPlanId,
                        llm_model: llm,
                        max_cycles: maxCycles
                    })
                });
                
                if (resp.ok) {
                    const data = await resp.json();
                    showToast(`Run started: ${data.run_id.slice(0, 8)}`, 'success');
                    startPolling(data.run_id);
                    fetchRuns();
                } else {
                    const err = await resp.json();
                    showToast(`Error: ${err.detail || 'Failed to start'}`, 'error');
                }
            } catch (e) {
                showToast(`Error: ${e.message}`, 'error');
            }
        }
        
        function startPolling(runId) {
            if (pollingIntervals[runId]) return;
            
            pollingIntervals[runId] = setInterval(async () => {
                try {
                    const resp = await fetch(`${API_BASE}/runs/${runId}`);
                    const data = await resp.json();
                    
                    if (['completed', 'failed', 'stopped'].includes(data.status)) {
                        clearInterval(pollingIntervals[runId]);
                        delete pollingIntervals[runId];
                        showToast(`Run ${data.status}: ${runId.slice(0, 8)}`, 
                            data.status === 'completed' ? 'success' : 'error');
                    }
                    
                    fetchRuns();
                } catch (e) {
                    clearInterval(pollingIntervals[runId]);
                    delete pollingIntervals[runId];
                }
            }, 2000);
        }
        
        async function stopRun(runId) {
            try {
                await fetch(`${API_BASE}/runs/${runId}/stop`, { method: 'POST' });
                showToast('Run stopped', 'success');
                fetchRuns();
            } catch (e) {
                showToast(`Error: ${e.message}`, 'error');
            }
        }
        
        async function viewResult(runId) {
            try {
                const resp = await fetch(`${API_BASE}/runs/${runId}/result`);
                const data = await resp.json();
                
                document.getElementById('resultPanel').style.display = 'block';
                document.getElementById('resultContent').textContent = 
                    JSON.stringify(data, null, 2);
            } catch (e) {
                showToast(`Error: ${e.message}`, 'error');
            }
        }
        
        function refreshRuns() {
            fetchRuns();
        }
        
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }
        
        // Init
        document.getElementById('runBtn').addEventListener('click', startRun);
        fetchPlans();
        fetchRuns();
        
        // Refresh runs periodically
        setInterval(fetchRuns, 5000);
    </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="NormCode Client UI")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--browser", "-b", action="store_true", help="Open in browser instead of window")
    
    args = parser.parse_args()
    
    client_url = f"http://{args.host}:{args.port}/client/ui"
    
    if args.browser:
        import webbrowser
        print(f"Opening in browser: {client_url}")
        webbrowser.open(client_url)
        return
    
    # Try pywebview
    try:
        import webview
        print(f"Opening client window: {client_url}")
        
        # Check icon
        icon_path = str(ICON_PATH.resolve()) if ICON_PATH.exists() else None
        if icon_path:
            print(f"Using icon: {icon_path}")
            # Set Windows AppUserModelID for proper taskbar grouping/icon
            set_windows_icon(icon_path)
        
        # Create window
        webview.create_window(
            title="NormCode Client",
            url=client_url,
            width=1100,
            height=700,
            resizable=True,
            min_size=(900, 500),
        )
        
        # Start with icon
        webview.start(icon=icon_path)
    except ImportError:
        import webbrowser
        print("pywebview not installed, opening in browser")
        print("  Tip: pip install pywebview for dedicated window")
        webbrowser.open(client_url)


if __name__ == "__main__":
    main()

