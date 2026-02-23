/**
 * NormCode Server UI - Tab Management, Inspector/Tools Mount, Initialization
 */

// ==================================================================
// Tab Management
// ==================================================================

let toolsMounted = false;

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + 'Panel').classList.add('active');

        if (tab.dataset.tab === 'tools' && !toolsMounted) {
            mountToolsPanel();
        }
    });
});

// ==================================================================
// Run Controls Collapse
// ==================================================================

function toggleRunControls() {
    const runControls = document.querySelector('.run-controls');
    runControls.classList.toggle('collapsed');
}

// ==================================================================
// Tools Panel (React-powered)
// ==================================================================

function mountToolsPanel() {
    const container = document.getElementById('reactTools');
    if (!container) return;

    if (window.ToolsPanel && typeof window.ToolsPanel.mount === 'function') {
        window.ToolsPanel.mount(container);
        toolsMounted = true;
    } else {
        container.innerHTML = `<div class="empty-state" style="padding:40px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:16px;">🔧</div>
            <div style="font-size:1.1rem;margin-bottom:8px;">Tools panel not loaded</div>
            <div style="color:var(--text-dim);">tools-panel.js not available. Check browser console for errors.</div>
        </div>`;
    }
}

// ==================================================================
// DB Inspector (React-powered)
// ==================================================================

let currentInspectRunId = null;

function inspectRun(runId) {
    currentInspectRunId = runId;

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="inspect"]').classList.add('active');
    document.getElementById('inspectPanel').classList.add('active');

    const container = document.getElementById('reactInspector');
    if (!container) return;

    if (window.NormCodeInspector && typeof window.NormCodeInspector.mount === 'function') {
        window.NormCodeInspector.mount(container, runId);
    } else {
        console.error('[Inspector] window.NormCodeInspector not found. Checking bundle...');
        const scriptEl = document.querySelector('script[src*="run-inspector"]');
        const detail = scriptEl
            ? 'Script tag found but module did not initialize. Check browser console for errors.'
            : 'Script tag missing from HTML. Add: <script src="/static/dist/run-inspector.js"></script>';
        container.innerHTML = `<div class="empty-state" style="padding:40px;text-align:center;">
            <div style="font-size:2rem;margin-bottom:12px;">⚠️</div>
            <div style="margin-bottom:8px;">Inspector bundle not loaded</div>
            <div style="color:var(--text-dim);font-size:0.85rem;">${detail}</div>
        </div>`;
    }
}

// ==================================================================
// Startup
// ==================================================================

initUploadZone();
fetchPlans();
fetchRuns();
fetchPendingInputs();
connectEventStream();
connectInputEventStream();
updateUserBenchSelector();
setInterval(fetchRuns, 5000);
setInterval(updateUserBenchSelector, 10000);
