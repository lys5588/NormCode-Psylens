"""
Client UI Route

Serves the web-based client UI for managing plans and runs.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter()

# Resources directory
RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


@router.get("/favicon.ico")
async def client_favicon():
    """Serve the favicon."""
    icon_path = RESOURCES_DIR / "icon.ico"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/x-icon")
    return HTMLResponse(status_code=204)


@router.get("/logo.png")
async def client_logo():
    """Serve the logo image."""
    logo_path = RESOURCES_DIR / "Psylensai_log_raw.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    return HTMLResponse(status_code=404)

# Import the HTML from the client script (or define inline)
CLIENT_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NormCode Client</title>
    <!-- Favicon - use the app icon -->
    <link rel="icon" type="image/x-icon" href="/client/favicon.ico">
    <link rel="icon" type="image/png" href="/client/logo.png">
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
        
        .logo {
            width: 24px;
            height: 24px;
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
            display: flex;
            justify-content: space-between;
            align-items: center;
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
        
        .btn-secondary {
            background: var(--bg-hover);
            color: var(--text);
            border: 1px solid var(--border);
            margin-top: 8px;
        }
        
        .btn-secondary:hover { border-color: var(--accent-blue); }
        
        /* Main content */
        .content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
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
            vertical-align: middle;
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
        .status-badge.stepping { background: rgba(57, 197, 207, 0.2); color: var(--accent-cyan); }
        .status-badge.completed { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
        .status-badge.failed { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .status-badge.stopped { background: rgba(139, 148, 158, 0.2); color: var(--text-dim); }
        .status-badge.pending { background: rgba(139, 148, 158, 0.2); color: var(--text-dim); }
        .status-badge.historical { background: rgba(163, 113, 247, 0.2); color: var(--accent-purple); }
        
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
        .progress-cell {
            min-width: 120px;
        }
        
        .progress-bar {
            width: 80px;
            height: 6px;
            background: var(--bg-dark);
            border-radius: 3px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
            margin-right: 8px;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent-green);
            transition: width 0.3s;
        }
        
        .progress-text {
            font-size: 0.8rem;
            color: var(--text-dim);
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
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .result-body {
            padding: 16px;
            max-height: 400px;
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
            padding: 40px 20px;
            color: var(--text-dim);
        }
        
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
            z-index: 1000;
        }
        
        .toast.success { border-color: var(--accent-green); }
        .toast.error { border-color: var(--accent-red); }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Links */
        .nav-links {
            padding: 8px 16px;
            border-top: 1px solid var(--border);
            font-size: 0.8rem;
        }
        
        .nav-links a {
            color: var(--accent-blue);
            text-decoration: none;
            margin-right: 16px;
        }
        
        .nav-links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <div class="header">
                <h1><img src="/client/logo.png" alt="" class="logo"><span class="status-dot" id="statusDot"></span> NormCode Client</h1>
            </div>
            
            <div class="section-header">
                Plans
                <button class="action-btn" onclick="fetchPlans()" style="padding: 2px 6px;">↻</button>
            </div>
            <div class="plans-list" id="plansList">
                <div class="empty-state">Loading...</div>
            </div>
            
            <div class="run-controls">
                <div class="form-group">
                    <label>LLM Model</label>
                    <select id="llmSelect">
                        <option value="demo">demo (mock)</option>
                        <option value="qwen-plus" selected>qwen-plus</option>
                        <option value="qwen-turbo-latest">qwen-turbo-latest</option>
                        <option value="gpt-4o">gpt-4o</option>
                        <option value="deepseek-r1-distill-qwen-1.5b">deepseek-r1</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Max Cycles</label>
                    <input type="number" id="maxCycles" value="100" min="1" max="1000">
                </div>
                <button class="btn btn-primary" id="runBtn" disabled>▶ Run Selected Plan</button>
                <button class="btn btn-secondary" onclick="window.open('/monitor/ui', '_blank')">📊 Open Monitor</button>
            </div>
            
            <div class="nav-links">
                <a href="/docs" target="_blank">API Docs</a>
                <a href="/monitor/ui" target="_blank">Monitor</a>
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
                    <div class="result-header">
                        <span>Result</span>
                        <button class="action-btn" onclick="hideResult()">✕ Close</button>
                    </div>
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
                const completed = progress.completed_count || 0;
                const total = progress.total_count || 0;
                const pct = total ? Math.round((completed / total) * 100) : 0;
                const started = r.started_at ? 
                    new Date(r.started_at).toLocaleTimeString() : '—';
                
                const actions = [];
                if (r.status === 'completed') {
                    actions.push(`<button class="action-btn" onclick="viewResult('${r.run_id}')">View</button>`);
                }
                if (['running', 'paused', 'stepping'].includes(r.status)) {
                    actions.push(`<button class="action-btn danger" onclick="stopRun('${r.run_id}')">Stop</button>`);
                }
                if (r.status === 'paused') {
                    actions.push(`<button class="action-btn" onclick="continueRun('${r.run_id}')">Continue</button>`);
                }
                
                return `
                    <tr>
                        <td class="run-id-cell">${r.run_id.slice(0, 12)}...</td>
                        <td>${planName}</td>
                        <td><span class="status-badge ${r.status}">${r.status}</span></td>
                        <td class="progress-cell">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${pct}%"></div>
                            </div>
                            <span class="progress-text">${completed}/${total}</span>
                        </td>
                        <td>${started}</td>
                        <td>${actions.join('') || '—'}</td>
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
        
        async function continueRun(runId) {
            try {
                await fetch(`${API_BASE}/runs/${runId}/continue`, { method: 'POST' });
                showToast('Run resumed', 'success');
                startPolling(runId);
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
        
        function hideResult() {
            document.getElementById('resultPanel').style.display = 'none';
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


@router.get("/ui", response_class=HTMLResponse)
async def client_ui():
    """Serve the web-based client UI."""
    return CLIENT_UI_HTML

