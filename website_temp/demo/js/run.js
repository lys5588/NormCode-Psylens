// ============================================================================
// Run Execution & File Uploads
// ============================================================================

async function startRun() {
    const topic = document.getElementById('topic').value.trim();
    const audience = document.getElementById('audience').value.trim();
    const length = document.getElementById('length').value.trim();
    const llm = document.getElementById('llmModel').value;
    currentPlanId = planSelect.value;

    if (!topic) {
        alert('请输入主题');
        return;
    }

    currentUserId = `gui_${Date.now()}`;

    // Clear UI
    eventsLog.innerHTML = '';
    document.getElementById('finalOutputs').innerHTML = '<div style="color: var(--muted); text-align: center; padding: 16px; font-size: 0.85rem;">正在生成...</div>';
    document.getElementById('intermediateFiles').innerHTML = '<div style="color: var(--muted); text-align: center; padding: 16px; font-size: 0.85rem;">等待中...</div>';
    progressFill.style.width = '0%';
    progressText.textContent = '0 / 0 次推理';

    // Reset loop progress
    loopProgress.currentLoop = null;
    loopProgress.iteration = 0;
    loopProgress.totalIterations = null;
    loopProgress.completedInferences = 0;
    loopProgress.totalInferences = 0;

    // Build refs
    const contentRefs = uploadedContent
        .filter(f => f.enabled !== false)
        .map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path || `provisions/inputs/content/${f.name}`,
            type: f.type || 'content',
            ...(f.for ? { for: f.for } : {})
        }));

    const templateRefs = uploadedTemplate
        .filter(f => f.enabled !== false)
        .map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path || `provisions/inputs/templates/${f.name}`,
            type: f.type || 'html_template',
            ...(f.for ? { for: f.for } : {})
        }));

    const styleGuideRefs = uploadedStyle
        .filter(f => f.enabled !== false)
        .map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path || `provisions/inputs/style/${f.name}`,
            type: f.type || 'guide',
            ...(f.for ? { for: f.for } : {})
        }));

    const styleRefs = [...templateRefs, ...styleGuideRefs];

    const payload = {
        plan_id: currentPlanId,
        llm_model: llm,
        user_id: currentUserId,
        ground_inputs: {
            '{演示主题}': { data: [[topic]], axes: ['_none_axis'] },
            '{目标受众}': { data: [[audience || '一般受众']], axes: ['_none_axis'] },
            '{期望长度}': { data: [[length || '6张幻灯片']], axes: ['_none_axis'] },
        }
    };

    if (contentRefs.length > 0) {
        payload.ground_inputs['[内容参考元数据]'] = { data: [contentRefs], axes: ['内容参考'] };
    }
    if (styleRefs.length > 0) {
        payload.ground_inputs['[样式参考元数据]'] = { data: [styleRefs], axes: ['样式参考'] };
    }

    try {
        startBtn.disabled = true;
        startBtn.textContent = '⏳ 上传文件中...';

        const uploadCount = await uploadFilesToBench();
        if (uploadCount > 0) {
            console.log(`[startRun] Uploaded ${uploadCount} files to userbench`);
        }

        startBtn.textContent = '⏳ 启动运行...';

        const resp = await fetch(`${serverUrl}/api/runs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || '启动失败');
        }

        const data = await resp.json();
        currentRunId = data.run_id;
        runIdEl.textContent = `运行: ${currentRunId.substring(0, 8)}`;

        statusDot.className = 'status-dot running';
        statusText.textContent = '运行中...';
        startBtn.textContent = '⏹️ 运行中...';

        startEventStream();
        pollOutputFiles();
        setTimeout(refreshInspector, 1000);

    } catch (e) {
        alert('启动失败: ' + e.message);
        startBtn.disabled = false;
        startBtn.textContent = '🚀 开始生成';
    }
}

// ===== Upload Files to Userbench =====
async function uploadFilesToBench() {
    let uploadCount = 0;
    const uploadPromises = [];

    const uploadFile = (f, category) => {
        const uploadPath = f.path || `provisions/inputs/${category}/${f.name}`;
        return fetch(`${serverUrl}/api/userbenches/${currentUserId}/files/${uploadPath}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
            body: f.content
        }).then(resp => {
            if (resp.ok) {
                console.log(`[upload] ${category} file uploaded: ${uploadPath}`);
                uploadCount++;
            } else {
                console.warn(`[upload] Failed to upload ${f.name}: ${resp.status}`);
            }
        }).catch(e => {
            console.warn(`[upload] Error uploading ${f.name}:`, e);
        });
    };

    for (const f of uploadedContent) {
        if (!f.isDefault && f.content && f.enabled !== false) {
            uploadPromises.push(uploadFile(f, 'content'));
        }
    }
    for (const f of uploadedTemplate) {
        if (!f.isDefault && f.content && f.enabled !== false) {
            uploadPromises.push(uploadFile(f, 'templates'));
        }
    }
    for (const f of uploadedStyle) {
        if (!f.isDefault && f.content && f.enabled !== false) {
            uploadPromises.push(uploadFile(f, 'style'));
        }
    }

    await Promise.all(uploadPromises);
    return uploadCount;
}

