// ============================================================================
// Tool Diagnostics
// ============================================================================

// Map tool IDs to their test endpoint paths (only testable tools)
const TOOL_TEST_ENDPOINTS = {
    llm:                { endpoint: 'llm/test',        payload: () => ({ model: document.getElementById('llmModel').value || 'demo', prompt: 'Say hello.', max_tokens: 50 }) },
    python_interpreter: { endpoint: 'python/test',     payload: () => ({ code: 'result = 2 + 2' }) },
    file_system:        { endpoint: 'filesystem/test', payload: () => ({ operation: 'list', path: '.' }) },
    gim:                { endpoint: 'gim/test',        payload: () => ({ prompt: 'A blue square', mock_mode: true }) },
};

async function runToolDiagnostics() {
    const grid = document.getElementById('toolsGrid');
    const statusBadge = document.getElementById('toolsStatus');
    grid.innerHTML = '<div class="placeholder" style="font-size:0.8rem">检测中...</div>';
    statusBadge.textContent = '';

    try {
        // 1. Discover tools — response is { tools: [...] }
        const resp = await fetch(`${serverUrl}/api/tools`);
        const data = await resp.json();
        const tools = data.tools || [];

        // 2. Render tool rows (use tool.id for DOM IDs, tool.name for display)
        grid.innerHTML = '';
        let passCount = 0;
        let totalTestable = 0;

        for (const tool of tools) {
            const row = document.createElement('div');
            row.className = 'tool-row';
            row.id = `tool-${tool.id}`;

            const icon = tool.available ? '✅' : '❌';
            const statusClass = tool.available ? 'tool-ok' : 'tool-fail';

            row.innerHTML = `
                <span class="tool-icon">${icon}</span>
                <span class="tool-name">${tool.name}</span>
                <span class="tool-result ${statusClass}" id="toolResult-${tool.id}">
                    ${tool.available ? '可用' : '不可用'}
                </span>
            `;
            grid.appendChild(row);

            if (tool.available && tool.testable) totalTestable++;
        }

        // 3. Auto-test tools that have test endpoints and are available
        for (const tool of tools) {
            if (!tool.available || !tool.testable) continue;

            const testDef = TOOL_TEST_ENDPOINTS[tool.id];
            if (!testDef) continue;

            const resultEl = document.getElementById(`toolResult-${tool.id}`);
            if (!resultEl) continue;

            resultEl.textContent = '测试中...';
            resultEl.className = 'tool-result tool-testing';

            try {
                const r = await fetch(`${serverUrl}/api/tools/${testDef.endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testDef.payload())
                });
                const result = await r.json();
                if (result.status === 'success') {
                    resultEl.textContent = `通过 (${result.duration_ms}ms)`;
                    resultEl.className = 'tool-result tool-ok';
                    passCount++;
                } else {
                    resultEl.textContent = `失败: ${result.error || '未知错误'}`;
                    resultEl.className = 'tool-result tool-fail';
                }
            } catch (e) {
                resultEl.textContent = '测试失败';
                resultEl.className = 'tool-result tool-fail';
            }
        }

        // 4. Summary badge
        statusBadge.textContent = `${passCount}/${totalTestable}`;
        statusBadge.className = 'tools-status ' + (passCount === totalTestable ? 'tools-pass' : 'tools-warn');

    } catch (e) {
        grid.innerHTML = '<div class="placeholder" style="font-size:0.8rem;color:var(--danger)">检测失败</div>';
        statusBadge.textContent = '!';
        statusBadge.className = 'tools-status tools-warn';
    }
}
