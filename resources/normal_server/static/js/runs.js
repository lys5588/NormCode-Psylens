/**
 * NormCode Server UI - Runs Management & Results
 */

let currentResultData = null;

async function fetchRuns() {
    try {
        const resp = await fetch(`${API}/runs`);
        const data = await resp.json();
        renderRuns(data);
    } catch (e) {
        console.error('Fetch runs error:', e);
    }
}

function renderRuns(list) {
    const tbody = document.getElementById('runsTable');
    if (!list.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No runs</td></tr>';
        return;
    }
    
    tbody.innerHTML = list.map(r => {
        const plan = plans[r.plan_id];
        const planName = plan?.name || r.plan_id?.slice(0, 8) || '?';
        const prog = r.progress || {};
        const pct = prog.total_count ? Math.round(prog.completed_count / prog.total_count * 100) : 0;
        const started = r.started_at ? formatTimeAgo(r.started_at) : '—';
        const runMode = r.run_mode || 'slow';
        const modeIcon = runMode === 'fast' ? '⚡' : '🐢';
        
        let actions = [];
        actions.push(`<button class="run-action-btn" onclick="browseRunFiles('${r.user_id || r.run_id}')" title="Browse files">📁</button>`);
        actions.push(`<button class="run-action-btn" onclick="inspectRun('${r.run_id}')" title="Inspect database">🔍</button>`);
        if (r.status === 'completed') actions.push(`<button class="run-action-btn" onclick="viewResult('${r.run_id}')" title="View result">📊</button>`);
        if (['running', 'paused'].includes(r.status)) actions.push(`<button class="run-action-btn danger" onclick="stopRun('${r.run_id}')" title="Stop run">⏹</button>`);
        
        return `<tr>
            <td>
                <div class="run-id-cell">
                    <span class="mono text-cyan">${r.run_id.slice(0, 7)}</span>
                    <span class="run-mode-icon" title="${runMode} mode">${modeIcon}</span>
                </div>
            </td>
            <td class="run-plan-cell">${planName}</td>
            <td><span class="badge badge-${r.status}">${r.status}</span></td>
            <td>
                <div class="progress-cell">
                    <div class="progress-bar"><div class="progress-fill progress-fill-${r.status}" style="width:${pct}%"></div></div>
                    <span class="progress-text">${prog.completed_count||0}/${prog.total_count||0}</span>
                </div>
            </td>
            <td class="text-dim">${started}</td>
            <td><div class="run-actions">${actions.join('')}</div></td>
        </tr>`;
    }).join('');
}

async function startRun() {
    if (!selectedPlanId) return;
    const userId = document.getElementById('userIdInput').value || 'default';
    const llm = document.getElementById('llmSelect').value;
    const runMode = document.getElementById('runModeSelect').value;
    const maxCycles = parseInt(document.getElementById('maxCyclesInput').value) || 200;
    
    try {
        const resp = await fetch(`${API}/runs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                plan_id: selectedPlanId, 
                user_id: userId, 
                llm_model: llm,
                run_mode: runMode,
                max_cycles: maxCycles
            })
        });
        
        if (resp.ok) {
            const data = await resp.json();
            const modeIcon = runMode === 'fast' ? '⚡' : '🐢';
            showToast(`${modeIcon} Run started: ${data.run_id.slice(0, 8)}`, 'success');
            fetchRuns();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Failed', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function stopRun(runId) {
    try {
        await fetch(`${API}/runs/${runId}/stop`, { method: 'POST' });
        showToast('Run stopped', 'success');
        fetchRuns();
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function viewResult(runId) {
    try {
        const resp = await fetch(`${API}/runs/${runId}/result`);
        if (!resp.ok) {
            const err = await resp.json();
            showToast(err.detail || 'Failed to load result', 'error');
            return;
        }
        
        const data = await resp.json();
        currentResultData = data;
        showResultModal(data);
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

function showResultModal(data) {
    const modal = document.getElementById('resultModal');
    const metaEl = document.getElementById('resultMeta');
    const conceptsEl = document.getElementById('resultConcepts');
    
    const modeIcon = data.run_mode === 'fast' ? '⚡' : '🐢';
    const modeLabel = data.run_mode === 'fast' ? 'Fast' : 'Slow';
    
    metaEl.innerHTML = `
        <div class="result-info">
            <div class="info-item">
                <span class="info-label">Run ID</span>
                <span class="info-value mono">${data.run_id || 'N/A'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Plan ID</span>
                <span class="info-value">${data.plan_id || 'N/A'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Mode</span>
                <span class="info-value">${modeIcon} ${modeLabel}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Status</span>
                <span class="badge badge-${data.status}">${data.status || 'N/A'}</span>
            </div>
            ${data.resumed_from ? `
            <div class="info-item">
                <span class="info-label">Resumed From</span>
                <span class="info-value mono">${data.resumed_from.original_run_id?.slice(0,12) || 'N/A'}... (cycle ${data.resumed_from.cycle})</span>
            </div>
            ` : ''}
        </div>
    `;
    
    const concepts = data.final_concepts || [];
    if (!concepts.length) {
        conceptsEl.innerHTML = '<div class="empty-state">No final concepts</div>';
    } else {
        conceptsEl.innerHTML = `
            <h4 class="section-title">Final Concepts (${concepts.length})</h4>
            <div class="concepts-grid">
                ${concepts.map(c => renderConceptCard(c)).join('')}
            </div>
        `;
    }
    
    modal.style.display = 'flex';
}

function renderConceptCard(concept) {
    const hasValue = concept.has_value;
    const shape = concept.shape ? `[${concept.shape.join('×')}]` : '';
    
    let valueDisplay = '';
    if (hasValue && concept.value) {
        let parsed = concept.value;
        try {
            parsed = JSON.parse(concept.value);
        } catch(e) {}
        
        if (typeof parsed === 'string') {
            valueDisplay = `<div class="concept-value concept-value-string">${escapeHtml(parsed)}</div>`;
        } else if (Array.isArray(parsed)) {
            if (parsed.length <= 10) {
                valueDisplay = `<div class="concept-value concept-value-array"><pre>${JSON.stringify(parsed, null, 2)}</pre></div>`;
            } else {
                valueDisplay = `
                    <div class="concept-value concept-value-array">
                        <div class="value-preview">${JSON.stringify(parsed.slice(0, 5))}...</div>
                        <details>
                            <summary>Show all ${parsed.length} items</summary>
                            <pre>${JSON.stringify(parsed, null, 2)}</pre>
                        </details>
                    </div>
                `;
            }
        } else if (typeof parsed === 'object') {
            const keys = Object.keys(parsed);
            if (keys.length <= 5) {
                valueDisplay = `<div class="concept-value concept-value-object"><pre>${JSON.stringify(parsed, null, 2)}</pre></div>`;
            } else {
                valueDisplay = `
                    <div class="concept-value concept-value-object">
                        <div class="value-preview">{${keys.slice(0, 3).join(', ')}... ${keys.length} keys}</div>
                        <details>
                            <summary>Show full object</summary>
                            <pre>${JSON.stringify(parsed, null, 2)}</pre>
                        </details>
                    </div>
                `;
            }
        } else {
            valueDisplay = `<div class="concept-value">${String(parsed)}</div>`;
        }
    } else {
        valueDisplay = `<div class="concept-value concept-value-empty">No value computed</div>`;
    }
    
    return `
        <div class="concept-card ${hasValue ? 'has-value' : 'no-value'}">
            <div class="concept-header">
                <span class="concept-name">${escapeHtml(concept.name)}</span>
                ${shape ? `<span class="concept-shape">${shape}</span>` : ''}
            </div>
            ${valueDisplay}
            <div class="concept-actions">
                <button class="btn btn-xs" onclick="copyConceptValue('${escapeHtml(concept.name)}')">📋 Copy</button>
            </div>
        </div>
    `;
}

function hideResultModal() {
    document.getElementById('resultModal').style.display = 'none';
}

function exportResult() {
    if (!currentResultData) return;
    
    const blob = new Blob([JSON.stringify(currentResultData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `result_${currentResultData.run_id?.slice(0,8) || 'unknown'}_${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Result exported', 'success');
}

function copyResult() {
    if (!currentResultData) return;
    
    navigator.clipboard.writeText(JSON.stringify(currentResultData, null, 2))
        .then(() => showToast('Result copied to clipboard', 'success'))
        .catch(e => showToast('Failed to copy: ' + e.message, 'error'));
}

function copyConceptValue(conceptName) {
    if (!currentResultData?.final_concepts) return;
    
    const concept = currentResultData.final_concepts.find(c => c.name === conceptName);
    if (!concept || !concept.value) {
        showToast('No value to copy', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(concept.value)
        .then(() => showToast(`Copied "${conceptName}"`, 'success'))
        .catch(e => showToast('Failed to copy: ' + e.message, 'error'));
}

async function clearAllRuns() {
    if (!confirm('Clear ALL runs? This cannot be undone.')) return;
    try {
        await fetch(`${API}/runs`, { method: 'DELETE' });
        showToast('All runs cleared', 'success');
        fetchRuns();
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}
