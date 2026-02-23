/**
 * NormCode Server UI - Global State & Utilities
 */

const API = window.location.origin + '/api';
let plans = {};
let selectedPlanId = null;
let events = [];
let stats = { runs_started: 0, runs_completed: 0, inferences_executed: 0 };
let activeRuns = {};
let eventSource = null;

/**
 * Safely parse JSON from a response. Handles cases where the server
 * (or Nginx reverse proxy) returns HTML instead of JSON.
 * 
 * Common cause: Nginx returning its default error page (e.g. 413, 502)
 * instead of proxying to the FastAPI backend.
 */
async function safeJson(resp, context = '') {
    const contentType = resp.headers.get('content-type') || '';
    
    if (!resp.ok) {
        if (contentType.includes('application/json')) {
            const err = await resp.json();
            showToast(err.detail || err.error || `Request failed (HTTP ${resp.status})`, 'error');
        } else {
            const text = await resp.text();
            if (text.includes('<html') || text.includes('<!DOCTYPE')) {
                let hint = `Server returned HTML instead of JSON (HTTP ${resp.status}).`;
                if (resp.status === 413) {
                    hint += ' File too large — increase Nginx client_max_body_size.';
                } else if (resp.status === 502) {
                    hint += ' Backend server may be down — check systemctl status normcode.';
                } else if (resp.status === 504) {
                    hint += ' Request timed out — increase Nginx proxy_read_timeout.';
                }
                showToast(hint, 'error');
            } else {
                showToast(`Error (HTTP ${resp.status}): ${text.slice(0, 100)}`, 'error');
            }
        }
        return null;
    }
    
    if (contentType.includes('application/json')) {
        return await resp.json();
    }
    
    const text = await resp.text();
    try {
        return JSON.parse(text);
    } catch (e) {
        if (text.includes('<html') || text.includes('<!DOCTYPE')) {
            showToast('Server returned HTML instead of JSON — check Nginx/proxy configuration', 'error');
        } else {
            showToast(`Invalid JSON response: ${text.slice(0, 80)}...`, 'error');
        }
        return null;
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatTimeAgo(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ${diffMin % 60}m ago`;
    
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function renderMarkdown(md) {
    return md
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/\n/g, '<br>');
}
