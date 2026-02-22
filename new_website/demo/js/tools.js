// ============================================================================
// Tool Diagnostics
// ============================================================================

async function runToolDiagnostics() {
    const grid = document.getElementById('toolsGrid');
    const statusBadge = document.getElementById('toolsStatus');
    grid.innerHTML = '<div class="placeholder" style="font-size:0.8rem">检测中...</div>';
    statusBadge.textContent = '';

    try {
        // 1. Discover tools
        const resp = await fetch(`${serverUrl}/api/tools`);
        const tools = await resp.json();

        // 2. Render tool rows
        grid.innerHTML = '';
        let passCount = 0;
        let totalTestable = 0;

        for (const tool of tools) {
            const row = document.createElement('div');
            row.className = 'tool-row';
            row.id = `tool-${tool.name}`;

            const icon = tool.available ? '✅' : '❌';
            const statusClass = tool.available ? 'tool-ok' : 'tool-fail';

            row.innerHTML = `
                <span class="tool-icon">${icon}</span>
                <span class="tool-name">${tool.name}</span>
                <span class="tool-result ${statusClass}" id="toolResult-${tool.name}">
                    ${tool.available ? '可用' : '不可用'}
                </span>
            `;
            grid.appendChild(row);

            if (!tool.available || !tool.testable) continue;
            totalTestable++;
        }

        // 3. Auto-test LLM and Python (the critical ones)
        const testsToRun = [
            { name: 'llm', payload: { model: document.getElementById('llmModel').value || 'demo', prompt: 'Say hello.', max_tokens: 50 } },
            { name: 'python', payload: { code: 'result = 2 + 2' } }
        ];

        for (const test of testsToRun) {
            const resultEl = document.getElementById(`toolResult-${test.name}`);
            if (!resultEl) continue;
            resultEl.textContent = '测试中...';
            resultEl.className = 'tool-result tool-testing';

            try {
                const r = await fetch(`${serverUrl}/api/tools/${test.name}/test`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(test.payload)
                });
                const data = await r.json();
                if (data.status === 'success') {
                    resultEl.textContent = `通过 (${data.duration_ms}ms)`;
                    resultEl.className = 'tool-result tool-ok';
                    passCount++;
                } else {
                    resultEl.textContent = `失败: ${data.error || '未知错误'}`;
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
