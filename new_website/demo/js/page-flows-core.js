/**
 * Page-Flows Core Application Module
 * Navigation, Server Connection, Model Picker, Tool Diagnostics, Load Defaults
 */

        function escapeHtml(str) {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        function goTo(n) {
            // Can't skip ahead of current furthest step unless connected
            if (n > 0 && !connected) return;
            if (n === 4 && step !== 3) return; // step 4 only via launch

            step = n;
            steps.forEach(s => s.classList.remove('active'));
            steps[step].classList.add('active');

            dots.forEach((d, i) => {
                d.classList.remove('active');
                d.classList.toggle('done', i < step);
            });
            dots[step].classList.add('active');

            btnBack.disabled = false;
            btnNext.style.display = step >= 3 ? 'none' : '';
            btnNext.disabled = step === 0 && !connected;

            if (step === 3) buildReview();
        }

        function nextStep() {
            if (step === 1) {
                const topic = document.getElementById('pfTopic').value.trim();
                if (!topic) { document.getElementById('pfTopic').focus(); return; }
            }
            if (step < 4) goTo(step + 1);
        }

        function prevStep() {
            if (step === 0) { window.location.href = 'plans.html'; return; }
            if (step > 0) goTo(step - 1);
        }

        // ---- Step 0: Connect ----
        async function connectToServer() {
            const connDot = document.getElementById('pfConnDot');
            const connMsg = document.getElementById('pfConnMsg');
            const serverDisplay = serverUrl.replace(/^https?:\/\//, '');
            document.getElementById('pfServer').textContent = serverDisplay;

            // Show plan name
            const plans = JSON.parse(sessionStorage.getItem('normcode_plans') || '[]');
            const plan = plans.find(p => p.id === currentPlanId);
            document.getElementById('pfPlan').textContent = plan ? (plan.name || plan.id) : currentPlanId || '—';

            connMsg.textContent = t('connecting');
            connMsg.className = 'pf-connect-msg';

            try {
                const health = await fetch(`${serverUrl}/health`);
                if (!health.ok) throw new Error('Server not responding');

                // Fetch models
                try {
                    const modelsResp = await fetch(`${serverUrl}/api/models`);
                    availableModels = await modelsResp.json();
                    const preferred = availableModels.find(m => m.id === 'qwen-plus');
                    const nonDemo = availableModels.find(m => !(m.name || m.id).toLowerCase().includes('demo'));
                    const selected = preferred || nonDemo || availableModels[0];
                    if (selected) {
                        selectedModel = selected.id;
                        document.getElementById('pfModel').textContent = selected.name || selected.id;
                    }
                    buildModelDropdown();
                } catch (e) {
                    document.getElementById('pfModel').textContent = 'demo';
                    selectedModel = 'demo';
                    availableModels = [{ id: 'demo', name: 'Demo (Mock)', is_mock: true }];
                    buildModelDropdown();
                }

                // Load plan defaults
                await loadDefaults();

                connDot.className = 'pf-status-dot connected';
                connMsg.textContent = t('connected');
                connected = true;
                btnNext.disabled = false;

                // Run tool diagnostics (non-blocking)
                pfRunToolTests();

            } catch (e) {
                connDot.className = 'pf-status-dot error';
                connMsg.textContent = t('connFailed') + e.message;
                connMsg.className = 'pf-connect-msg error';
            }
        }

        // ---- Model picker ----
        function buildModelDropdown() {
            const dropdown = document.getElementById('pfModelDropdown');
            dropdown.innerHTML = availableModels.map(m => {
                const isActive = m.id === selectedModel;
                const mockBadge = m.is_mock ? `<span class="pf-mock-badge">${t('mock')}</span>` : '';
                return `<div class="pf-model-option${isActive ? ' active' : ''}" onclick="selectModel('${m.id}', event)">
                    ${escapeHtml(m.name || m.id)} ${mockBadge}
                </div>`;
            }).join('');
        }

        function toggleModelDropdown(e) {
            if (e) e.stopPropagation();
            const dropdown = document.getElementById('pfModelDropdown');
            dropdown.classList.toggle('open');
        }

        function selectModel(modelId, e) {
            if (e) e.stopPropagation();
            const model = availableModels.find(m => m.id === modelId);
            if (!model) return;
            selectedModel = model.id;
            document.getElementById('pfModel').textContent = model.name || model.id;
            document.getElementById('pfModelDropdown').classList.remove('open');
            buildModelDropdown();
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const row = document.getElementById('pfModelRow');
            if (row && !row.contains(e.target)) {
                document.getElementById('pfModelDropdown').classList.remove('open');
            }
        });

        // ---- Tool diagnostics ----
        const PF_TOOL_TESTS = {
            llm:                { endpoint: 'llm/test',        payload: () => ({ model: selectedModel || 'demo', prompt: 'Say hello.', max_tokens: 50 }) },
            python_interpreter: { endpoint: 'python/test',     payload: () => ({ code: 'result = 2 + 2' }) },
            file_system:        { endpoint: 'filesystem/test', payload: () => ({ operation: 'list', path: '.' }) },
            gim:                { endpoint: 'gim/test',        payload: () => ({ prompt: 'A blue square', mock_mode: true }) },
        };

        async function pfRunToolTests() {
            const section = document.getElementById('pfToolsSection');
            const grid = document.getElementById('pfToolsGrid');
            const badge = document.getElementById('pfToolsBadge');

            section.style.display = '';
            grid.innerHTML = '';
            badge.textContent = '';
            badge.className = 'pf-tools-badge';

            try {
                const resp = await fetch(`${serverUrl}/api/tools`);
                const data = await resp.json();
                const tools = data.tools || [];

                let passCount = 0;
                let totalTestable = 0;

                // Render rows
                for (const tool of tools) {
                    const row = document.createElement('div');
                    row.className = 'pf-tool-row';
                    const icon = tool.available ? '&#10003;' : '&#10007;';
                    const statusText = tool.available ? t('toolAvail') : t('toolUnavail');
                    const statusClass = tool.available ? 'ok' : 'fail';
                    row.innerHTML = `
                        <span class="pf-tool-icon">${icon}</span>
                        <span class="pf-tool-name">${escapeHtml(tool.name)}</span>
                        <span class="pf-tool-result ${statusClass}" id="pfToolResult-${tool.id}">${statusText}</span>
                    `;
                    grid.appendChild(row);
                    if (tool.available && tool.testable) totalTestable++;
                }

                // Auto-test available testable tools
                for (const tool of tools) {
                    if (!tool.available || !tool.testable) continue;
                    const testDef = PF_TOOL_TESTS[tool.id];
                    if (!testDef) continue;

                    const resultEl = document.getElementById(`pfToolResult-${tool.id}`);
                    if (!resultEl) continue;
                    resultEl.textContent = t('toolTesting');
                    resultEl.className = 'pf-tool-result testing';

                    try {
                        const r = await fetch(`${serverUrl}/api/tools/${testDef.endpoint}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(testDef.payload())
                        });
                        const result = await r.json();
                        if (result.status === 'success') {
                            resultEl.textContent = `${t('toolPass')} (${result.duration_ms}ms)`;
                            resultEl.className = 'pf-tool-result ok';
                            passCount++;
                        } else {
                            resultEl.textContent = `${t('toolFail')}: ${result.error || ''}`;
                            resultEl.className = 'pf-tool-result fail';
                        }
                    } catch (err) {
                        resultEl.textContent = t('toolFail');
                        resultEl.className = 'pf-tool-result fail';
                    }
                }

                // Badge
                badge.textContent = `${passCount}/${totalTestable}`;
                badge.className = 'pf-tools-badge ' + (passCount === totalTestable ? 'pass' : 'warn');

            } catch (e) {
                grid.innerHTML = `<div style="font-size:11px;color:var(--error)">${t('toolFail')}</div>`;
                badge.textContent = '!';
                badge.className = 'pf-tools-badge fail';
            }
        }

        async function loadDefaults() {
            if (!currentPlanId) return;
            try {
                const resp = await fetch(`${serverUrl}/api/plans/${currentPlanId}/files/inputs.json`);
                if (!resp.ok) return;
                const fileResponse = await resp.json();
                const defaults = JSON.parse(fileResponse.content);

                if (defaults['{演示主题}']?.data?.[0]?.[0])
                    document.getElementById('pfTopic').value = defaults['{演示主题}'].data[0][0];
                if (defaults['{目标受众}']?.data?.[0]?.[0])
                    document.getElementById('pfAudience').value = defaults['{目标受众}'].data[0][0];
                if (defaults['{期望长度}']?.data?.[0]?.[0])
                    document.getElementById('pfLength').value = defaults['{期望长度}'].data[0][0];

                // Load default content refs
                if (defaults['[内容参考元数据]']?.data?.[0]) {
                    defaults['[内容参考元数据]'].data[0].forEach(ref => {
                        pfContent.push({ name: ref.name, path: ref.path, type: ref.type, isDefault: true });
                    });
                    renderFileList('content');
                }
                // Load default style refs
                if (defaults['[样式参考元数据]']?.data?.[0]) {
                    defaults['[样式参考元数据]'].data[0].forEach(ref => {
                        const isTemplate = ref.type === 'html_template';
                        (isTemplate ? pfTemplate : pfStyle).push({ name: ref.name, path: ref.path, type: ref.type, isDefault: true });
                    });
                    renderFileList('template');
                    renderFileList('style');
                }
            } catch (e) {
                console.warn('[loadDefaults]', e);
            }
        }

        // ---- Step 2: File uploads ----
