/**
 * Page-Flows Core — PPT Template variant
 * Navigation, server connection, model picker, defaults loader.
 *
 * loadDefaults reads:
 *   [模板元数据]     → pfTemplate  (pptx_file entries)
 *   [风格参考元数据] → pfStyle
 * (Content refs intentionally left empty for each session.)
 */

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ---- Navigation ----
function goTo(n) {
    if (n > 0 && !connected) return;
    if (n === 6 && step !== 5) return;

    step = n;
    steps.forEach(s => s.classList.remove('active'));
    steps[step].classList.add('active');

    dots.forEach((d, i) => {
        d.classList.remove('active');
        d.classList.toggle('done', i < step);
    });
    dots[step].classList.add('active');

    btnBack.disabled = false;
    btnNext.style.display = step >= 5 ? 'none' : '';
    btnNext.disabled = step === 0 && !connected;

    if (step === 5) {
        // Close any running SSE stream so a fresh run can start
        if (pfEvtSource) { pfEvtSource.close(); pfEvtSource = null; }
        if (pfPollTimer)  { clearTimeout(pfPollTimer); pfPollTimer = null; }
        // Re-enable launch button; show "重新启动" if a prior run exists
        const launchBtn = document.getElementById('pfLaunchBtn');
        if (launchBtn) { launchBtn.disabled = false; launchBtn.textContent = currentRunId ? t('relaunch') : t('launch'); }
        buildReview();
    }
}

function nextStep() {
    if (step === 1) {
        const topic = document.getElementById('pfTopic').value.trim();
        if (!topic) { document.getElementById('pfTopic').focus(); return; }
    }
    if (step === 2 && pfTemplate.length === 0) {
        const drop = document.getElementById('pfTemplateDrop');
        if (drop) {
            drop.scrollIntoView({ behavior: 'smooth', block: 'center' });
            drop.style.outline = '2px solid #e55353';
            drop.style.outlineOffset = '2px';
            setTimeout(() => { drop.style.outline = ''; drop.style.outlineOffset = ''; }, 1500);
        }
        const msg = document.getElementById('pfTemplateDropLabel');
        if (msg) {
            const orig = msg.textContent;
            msg.textContent = t('templateRequired');
            msg.style.color = '#e55353';
            setTimeout(() => { msg.textContent = orig; msg.style.color = ''; }, 2500);
        }
        return;
    }
    if (step < 6) goTo(step + 1);
}

function prevStep() {
    if (step === 0) { window.location.href = '../index.html'; return; }
    if (step > 0) goTo(step - 1);
}

// ---- Step 0: Connect ----
async function connectToServer() {
    const connDot    = document.getElementById('pfConnDot');
    const connMsg    = document.getElementById('pfConnMsg');
    const serverDisplay = serverUrl.replace(/^https?:\/\//, '');
    document.getElementById('pfServer').textContent = serverDisplay;

    // Plan name: check session cache first, then fall back to the hard-coded ID.
    const plans = JSON.parse(sessionStorage.getItem('normcode_plans') || '[]');
    const plan  = plans.find(p => p.id === currentPlanId);
    document.getElementById('pfPlan').textContent = plan ? (plan.name || plan.id) : currentPlanId;

    connMsg.textContent = t('connecting');
    connMsg.className   = 'pf-connect-msg';

    try {
        const health = await fetch(`${serverUrl}/health`);
        if (!health.ok) throw new Error('Server not responding');

        // Fetch models
        try {
            const modelsResp = await fetch(`${serverUrl}/api/models`);
            availableModels  = await modelsResp.json();
            const preferred  = availableModels.find(m => m.id === 'qwen-plus');
            const nonDemo    = availableModels.find(m => !(m.name || m.id).toLowerCase().includes('demo'));
            const selected   = preferred || nonDemo || availableModels[0];
            if (selected) {
                selectedModel = selected.id;
                document.getElementById('pfModel').textContent = selected.name || selected.id;
            }
            buildModelDropdown();
        } catch {
            document.getElementById('pfModel').textContent = 'demo';
            selectedModel   = 'demo';
            availableModels = [{ id: 'demo', name: 'Demo (Mock)', is_mock: true }];
            buildModelDropdown();
        }

        await loadDefaults();

        connDot.className   = 'pf-status-dot connected';
        connMsg.textContent = t('connected');
        connected           = true;
        btnNext.disabled    = false;

        testCriticalTools();

    } catch (e) {
        connDot.className   = 'pf-status-dot error';
        connMsg.textContent = t('connFailed') + e.message;
        connMsg.className   = 'pf-connect-msg error';
    }
}

// ---- Model picker ----
function buildModelDropdown() {
    const dropdown = document.getElementById('pfModelDropdown');
    dropdown.innerHTML = availableModels.map(m => {
        const isActive   = m.id === selectedModel;
        const mockBadge  = m.is_mock ? `<span class="pf-mock-badge">${t('mock')}</span>` : '';
        return `<div class="pf-model-option${isActive ? ' active' : ''}" onclick="selectModel('${m.id}',event)">
            ${escapeHtml(m.name || m.id)} ${mockBadge}
        </div>`;
    }).join('');
}

function toggleModelDropdown(e) {
    if (e) e.stopPropagation();
    document.getElementById('pfModelDropdown').classList.toggle('open');
}

function selectModel(modelId, e) {
    if (e) e.stopPropagation();
    const model = availableModels.find(m => m.id === modelId);
    if (!model) return;
    selectedModel = model.id;
    document.getElementById('pfModel').textContent = model.name || model.id;
    document.getElementById('pfModelDropdown').classList.remove('open');
    buildModelDropdown();
    if (connected) testCriticalTools();
}

document.addEventListener('click', (e) => {
    const row = document.getElementById('pfModelRow');
    if (row && !row.contains(e.target)) {
        document.getElementById('pfModelDropdown').classList.remove('open');
    }
});

// ---- Critical tool checks ----
async function testCriticalTools() {
    const tests = [
        { id: 'Llm', endpoint: 'llm/test',        payload: { model: selectedModel || 'demo', prompt: 'Say hello.', max_tokens: 50 } },
        { id: 'Fs',  endpoint: 'filesystem/test', payload: { operation: 'list', path: '.' } },
        { id: 'Py',  endpoint: 'python/test',     payload: { code: 'result = 2 + 2' } },
    ];

    for (const test of tests) {
        const row    = document.getElementById(`pf${test.id}Row`);
        const dot    = document.getElementById(`pf${test.id}Dot`);
        const status = document.getElementById(`pf${test.id}Status`);
        row.style.display = '';
        dot.className     = 'pf-status-dot';
        status.textContent = t('testing');

        try {
            const r      = await fetch(`${serverUrl}/api/tools/${test.endpoint}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(test.payload)
            });
            const result = await r.json();
            if (result.status === 'success') {
                dot.className      = 'pf-status-dot connected';
                status.textContent = `${t('testPass')} (${result.duration_ms}ms)`;
            } else {
                dot.className      = 'pf-status-dot error';
                status.textContent = t('testFail');
            }
        } catch {
            dot.className      = 'pf-status-dot error';
            status.textContent = t('testFail');
        }
    }
}

// ---- Load plan defaults ----
async function loadDefaults() {
    if (!currentPlanId) return;
    try {
        const resp = await fetch(`${serverUrl}/api/plans/${currentPlanId}/files/inputs.json`);
        if (!resp.ok) return;
        const fileResponse = await resp.json();
        const defaults     = JSON.parse(fileResponse.content);

        // Load default PPT templates from [模板元数据]
        if (defaults['[模板元数据]']?.data?.[0]) {
            defaults['[模板元数据]'].data[0].forEach(ref => {
                pfTemplate.push({
                    name:      ref.name || (ref.pptx_path || '').split('/').pop() || 'template.pptx',
                    path:      ref.pptx_path || ref.path || '',
                    type:      ref.type || 'pptx_file',
                    isDefault: true
                });
            });
            // Enforce max 1 — keep only the first
            if (pfTemplate.length > 1) pfTemplate.splice(1);
            renderFileList('template');
        }

        // Load default style guides from [风格参考元数据]
        if (defaults['[风格参考元数据]']?.data?.[0]) {
            defaults['[风格参考元数据]'].data[0].forEach(ref => {
                pfStyle.push({ name: ref.name, path: ref.path, type: ref.type, isDefault: true });
            });
            renderFileList('style');
        }
    } catch (e) {
        console.warn('[loadDefaults]', e);
    }
}
