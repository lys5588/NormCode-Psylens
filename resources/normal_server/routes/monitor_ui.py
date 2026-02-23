"""
Web-Based Monitor UI

Serves a simple HTML dashboard that connects to the monitor SSE stream.
No dependencies required - just open in browser!
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter()

# Resources directory
RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


@router.get("/favicon.ico")
async def monitor_favicon():
    """Serve the favicon."""
    icon_path = RESOURCES_DIR / "icon.ico"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/x-icon")
    # Fallback - return 204 No Content
    return HTMLResponse(status_code=204)


@router.get("/logo.png")
async def monitor_logo():
    """Serve the logo image."""
    logo_path = RESOURCES_DIR / "Psylensai_log_raw.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    return HTMLResponse(status_code=404)

MONITOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NormCode Server Monitor</title>
    <!-- Favicon - use the app icon -->
    <link rel="icon" type="image/x-icon" href="/monitor/favicon.ico">
    <link rel="icon" type="image/png" href="/monitor/logo.png">
    <style>
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
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
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        
        h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo {
            width: 28px;
            height: 28px;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-connected { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .status-disconnected { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .status-connecting { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        
        .grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }
        
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .card-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            font-weight: 600;
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-body {
            padding: 16px;
        }
        
        .sidebar .card {
            margin-bottom: 20px;
        }
        
        /* Stats */
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .stat-item {
            text-align: center;
            padding: 12px;
            background: var(--bg-dark);
            border-radius: 6px;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-blue);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-dim);
            text-transform: uppercase;
            margin-top: 4px;
        }
        
        /* Runs */
        .run-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .run-item:last-child { border-bottom: none; }
        
        .run-id {
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            color: var(--accent-cyan);
        }
        
        .run-status {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .run-status.running { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .run-status.paused { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        .run-status.completed { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
        .run-status.failed { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        
        .no-runs {
            color: var(--text-dim);
            text-align: center;
            padding: 20px;
            font-size: 0.9rem;
        }
        
        /* Events */
        .events-container {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .event-item {
            display: grid;
            grid-template-columns: 70px 180px 1fr;
            gap: 12px;
            padding: 8px 12px;
            border-bottom: 1px solid var(--border);
            font-size: 0.85rem;
            transition: background 0.15s;
        }
        
        .event-item:hover {
            background: var(--bg-hover);
        }
        
        .event-item.new {
            animation: flash 0.5s ease-out;
        }
        
        @keyframes flash {
            from { background: rgba(88, 166, 255, 0.2); }
            to { background: transparent; }
        }
        
        .event-time {
            color: var(--text-dim);
            font-family: 'Consolas', monospace;
        }
        
        .event-type {
            font-weight: 500;
        }
        
        .event-type.run { color: var(--accent-green); }
        .event-type.inference { color: var(--accent-blue); }
        .event-type.cycle { color: var(--accent-purple); }
        .event-type.error { color: var(--accent-red); }
        .event-type.llm { color: var(--accent-yellow); }
        .event-type.other { color: var(--text-dim); }
        
        .event-details {
            color: var(--text-dim);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .event-details code {
            background: var(--bg-dark);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8rem;
        }
        
        /* Controls */
        .controls {
            display: flex;
            gap: 10px;
        }
        
        button {
            padding: 6px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg-card);
            color: var(--text);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.15s;
        }
        
        button:hover {
            background: var(--bg-hover);
            border-color: var(--accent-blue);
        }
        
        .clear-btn { color: var(--accent-red); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <img src="/monitor/logo.png" alt="" class="logo"> NormCode Monitor
            </h1>
            <div class="controls">
                <span id="status" class="status-badge status-connecting">Connecting...</span>
                <button onclick="clearEvents()" class="clear-btn">Clear Events</button>
            </div>
        </header>
        
        <div class="grid">
            <div class="sidebar">
                <div class="card">
                    <div class="card-header">Statistics</div>
                    <div class="card-body">
                        <div class="stat-grid">
                            <div class="stat-item">
                                <div class="stat-value" id="stat-runs">0</div>
                                <div class="stat-label">Runs Started</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="stat-completed">0</div>
                                <div class="stat-label">Completed</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="stat-inferences">0</div>
                                <div class="stat-label">Inferences</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="stat-llm">0</div>
                                <div class="stat-label">LLM Calls</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        Active Runs
                        <span id="run-count" style="color: var(--text-dim)">0</span>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div id="runs-list">
                            <div class="no-runs">No active runs</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="main">
                <div class="card">
                    <div class="card-header">
                        Event Stream
                        <span id="event-count" style="color: var(--text-dim)">0 events</span>
                    </div>
                    <div class="events-container" id="events">
                        <!-- Events will be inserted here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let eventSource = null;
        let events = [];
        let activeRuns = {};
        let stats = {};
        const MAX_EVENTS = 200;
        
        function connect() {
            const statusEl = document.getElementById('status');
            statusEl.className = 'status-badge status-connecting';
            statusEl.textContent = 'Connecting...';
            
            eventSource = new EventSource('/api/monitor/stream');
            
            eventSource.onopen = () => {
                statusEl.className = 'status-badge status-connected';
                statusEl.textContent = '● Connected';
            };
            
            eventSource.onerror = () => {
                statusEl.className = 'status-badge status-disconnected';
                statusEl.textContent = '● Disconnected';
                eventSource.close();
                // Reconnect after 3 seconds
                setTimeout(connect, 3000);
            };
            
            eventSource.onmessage = (e) => {
                try {
                    const data = JSON.parse(e.data);
                    handleEvent(data);
                } catch (err) {
                    console.error('Parse error:', err);
                }
            };
        }
        
        function handleEvent(data) {
            const eventType = data.event || 'unknown';
            
            // Handle initial connection
            if (eventType === 'monitor:connected') {
                stats = data.stats || {};
                updateStats();
                
                // Initialize active runs
                activeRuns = {};
                (data.active_runs || []).forEach(run => {
                    activeRuns[run.run_id] = run;
                });
                updateRuns();
                return;
            }
            
            // Track active runs
            if (eventType === 'run:started') {
                activeRuns[data.run_id] = {
                    run_id: data.run_id,
                    plan_id: data.plan_id,
                    status: 'running'
                };
                stats.runs_started = (stats.runs_started || 0) + 1;
            } else if (eventType === 'run:completed') {
                delete activeRuns[data.run_id];
                stats.runs_completed = (stats.runs_completed || 0) + 1;
            } else if (eventType === 'run:failed' || eventType === 'execution:stopped') {
                delete activeRuns[data.run_id];
            } else if (eventType === 'inference:completed') {
                stats.inferences_executed = (stats.inferences_executed || 0) + 1;
            } else if (eventType === 'llm:call') {
                stats.llm_calls = (stats.llm_calls || 0) + 1;
            } else if (eventType === 'execution:paused' && data.run_id && activeRuns[data.run_id]) {
                activeRuns[data.run_id].status = 'paused';
            } else if (eventType === 'execution:resumed' && data.run_id && activeRuns[data.run_id]) {
                activeRuns[data.run_id].status = 'running';
            }
            
            // Add to events list
            events.unshift(data);
            if (events.length > MAX_EVENTS) {
                events = events.slice(0, MAX_EVENTS);
            }
            
            updateStats();
            updateRuns();
            updateEvents(data);
        }
        
        function updateStats() {
            document.getElementById('stat-runs').textContent = stats.runs_started || 0;
            document.getElementById('stat-completed').textContent = stats.runs_completed || 0;
            document.getElementById('stat-inferences').textContent = stats.inferences_executed || 0;
            document.getElementById('stat-llm').textContent = stats.llm_calls || 0;
        }
        
        function updateRuns() {
            const container = document.getElementById('runs-list');
            const runIds = Object.keys(activeRuns);
            document.getElementById('run-count').textContent = runIds.length;
            
            if (runIds.length === 0) {
                container.innerHTML = '<div class="no-runs">No active runs</div>';
                return;
            }
            
            container.innerHTML = runIds.map(runId => {
                const run = activeRuns[runId];
                return `
                    <div class="run-item">
                        <span class="run-id">${runId.slice(0, 8)}...</span>
                        <span class="run-status ${run.status || 'running'}">${run.status || 'running'}</span>
                    </div>
                `;
            }).join('');
        }
        
        function updateEvents(newEvent) {
            const container = document.getElementById('events');
            document.getElementById('event-count').textContent = `${events.length} events`;
            
            // Create new event element
            const eventEl = document.createElement('div');
            eventEl.className = 'event-item new';
            
            const eventType = newEvent.event || 'unknown';
            let typeClass = 'other';
            if (eventType.startsWith('run:')) typeClass = 'run';
            else if (eventType.startsWith('inference:')) typeClass = 'inference';
            else if (eventType.startsWith('cycle:')) typeClass = 'cycle';
            else if (eventType.startsWith('llm:')) typeClass = 'llm';
            else if (eventType.includes('error') || eventType.includes('failed')) typeClass = 'error';
            
            const time = newEvent.timestamp ? 
                new Date(newEvent.timestamp).toLocaleTimeString() : 
                new Date().toLocaleTimeString();
            
            let details = [];
            if (newEvent.run_id) details.push(`<code>${newEvent.run_id.slice(0, 8)}</code>`);
            if (newEvent.flow_index) details.push(`@${newEvent.flow_index}`);
            if (newEvent.concept_name) details.push(newEvent.concept_name);
            if (newEvent.duration) details.push(`${newEvent.duration.toFixed(2)}s`);
            if (newEvent.error) details.push(`<span style="color:var(--accent-red)">${newEvent.error}</span>`);
            
            eventEl.innerHTML = `
                <span class="event-time">${time}</span>
                <span class="event-type ${typeClass}">${eventType}</span>
                <span class="event-details">${details.join(' · ') || '—'}</span>
            `;
            
            // Insert at top
            container.insertBefore(eventEl, container.firstChild);
            
            // Remove animation class after it plays
            setTimeout(() => eventEl.classList.remove('new'), 500);
            
            // Limit displayed events
            while (container.children.length > 100) {
                container.removeChild(container.lastChild);
            }
        }
        
        function clearEvents() {
            events = [];
            document.getElementById('events').innerHTML = '';
            document.getElementById('event-count').textContent = '0 events';
        }
        
        // Start connection
        connect();
    </script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
async def monitor_ui():
    """Serve the web-based monitor UI."""
    return MONITOR_HTML

