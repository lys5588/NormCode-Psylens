// ============================================================================
// Server Connection & Plan Loading
// ============================================================================

async function connect(auto) {
    serverUrl = document.getElementById('serverUrl').value.trim();

    // Keep sessionStorage in sync when user reconnects with a different URL
    if (serverUrl) {
        sessionStorage.setItem('normcode_server_url', serverUrl);
    }

    // Mixed content: HTTPS page cannot fetch from HTTP server
    if (window.location.protocol === 'https:' && serverUrl.startsWith('http://')) {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'HTTPS 页面无法连接 HTTP 服务器 (混合内容限制)';
        startBtn.disabled = true;
        return;
    }

    try {
        statusText.textContent = '正在连接...';

        const health = await fetch(`${serverUrl}/health`);
        if (!health.ok) throw new Error('服务器无响应');

        // Use pre-fetched plans from gateway if available, otherwise fetch fresh
        const cachedPlans = sessionStorage.getItem('normcode_plans');
        const cachedPlanId = sessionStorage.getItem('normcode_plan_id');
        let plans;

        if (cachedPlans && auto) {
            plans = JSON.parse(cachedPlans);
            // Clear cache after first use so manual reconnects fetch fresh
            sessionStorage.removeItem('normcode_plans');
        } else {
            const plansResp = await fetch(`${serverUrl}/api/plans`);
            plans = await plansResp.json();
        }

        planSelect.innerHTML = '';
        plans.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name || p.id;
            planSelect.appendChild(opt);
        });

        if (plans.length > 0) {
            if (cachedPlanId && auto) {
                currentPlanId = cachedPlanId;
                sessionStorage.removeItem('normcode_plan_id');
            } else {
                const pptPlan = plans.find(p => p.name === 'ppt生成' || p.id.includes('ppt'));
                currentPlanId = pptPlan ? pptPlan.id : plans[0].id;
            }
            planSelect.value = currentPlanId;
            planSelect.disabled = false;
            await loadPlanDefaults(currentPlanId);
        }

        // Get LLM models
        try {
            const modelsResp = await fetch(`${serverUrl}/api/models`);
            const models = await modelsResp.json();
            const llmSelect = document.getElementById('llmModel');
            llmSelect.innerHTML = '';
            models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name || m.id;
                llmSelect.appendChild(opt);
            });
        } catch (e) {}

        statusDot.className = 'status-dot connected';
        statusText.textContent = `已连接 (${plans.length} 个计划)`;
        startBtn.disabled = false;

    } catch (e) {
        statusDot.className = 'status-dot error';
        statusText.textContent = `失败: ${e.message}`;
        startBtn.disabled = true;
    }
}

// ===== Plan Defaults Loading =====
async function loadPlanDefaults(planId) {
    if (!planId) return;

    console.log('[loadPlanDefaults] Loading for plan:', planId);

    try {
        const url = `${serverUrl}/api/plans/${planId}/files/inputs.json`;
        const resp = await fetch(url);

        if (resp.ok) {
            const fileResponse = await resp.json();
            defaultInputs = JSON.parse(fileResponse.content);

            if (defaultInputs['{演示主题}']?.data?.[0]?.[0]) {
                document.getElementById('topic').value = defaultInputs['{演示主题}'].data[0][0];
            }
            if (defaultInputs['{目标受众}']?.data?.[0]?.[0]) {
                document.getElementById('audience').value = defaultInputs['{目标受众}'].data[0][0];
            }
            if (defaultInputs['{期望长度}']?.data?.[0]?.[0]) {
                document.getElementById('length').value = defaultInputs['{期望长度}'].data[0][0];
            }

            if (defaultInputs['[内容参考元数据]']?.data?.[0]) {
                renderDefaultRefs('content', defaultInputs['[内容参考元数据]'].data[0]);
            } else {
                renderRefsList('content');
            }

            if (defaultInputs['[样式参考元数据]']?.data?.[0]) {
                renderDefaultRefs('style', defaultInputs['[样式参考元数据]'].data[0]);
            } else {
                renderRefsList('template');
                renderRefsList('style');
            }
        } else {
            renderRefsList('content');
            renderRefsList('template');
            renderRefsList('style');
        }
    } catch (e) {
        console.error('[loadPlanDefaults] Error:', e);
        renderRefsList('content');
        renderRefsList('template');
        renderRefsList('style');
    }
}

