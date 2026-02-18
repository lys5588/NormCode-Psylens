// ============================================================================
// Basic Inputs Management
// ============================================================================

function markInputsModified() {
    inputsModified = true;
    const statusEl = document.getElementById('inputsStatus');
    if (statusEl) {
        statusEl.textContent = '(已修改，未保存)';
        statusEl.style.color = 'var(--warning)';
    }
    const saveBtn = document.getElementById('saveInputsBtn');
    if (saveBtn) {
        saveBtn.style.background = 'var(--warning)';
    }
}

function markInputsSaved() {
    inputsModified = false;
    const statusEl = document.getElementById('inputsStatus');
    if (statusEl) {
        statusEl.textContent = '(已保存 ✓)';
        statusEl.style.color = 'var(--success)';
        setTimeout(() => {
            if (!inputsModified) statusEl.textContent = '';
        }, 3000);
    }
    const saveBtn = document.getElementById('saveInputsBtn');
    if (saveBtn) {
        saveBtn.style.background = '';
    }
}

async function saveInputsToBackend() {
    if (!currentUserId) {
        currentUserId = `gui_${Date.now()}`;
    }

    const topic = document.getElementById('topic').value.trim();
    const audience = document.getElementById('audience').value.trim();
    const length = document.getElementById('length').value.trim();

    if (!topic) {
        alert('请输入主题');
        return;
    }

    const inputsJson = {
        "_comment": "内容优先演示文稿生成器的输入",
        "_flow": "内容 → 样式：先生成内容，再选择模板",
        "_note": "所有路径都是相对于 body.base_dir 的相对路径",

        "{项目目录}": {
            "_description": "输出文件目录（相对于 body.base_dir）",
            "_type": "literal<$% str>",
            "data": [["productions"]],
            "axes": ["_none_axis"]
        },
        "{演示主题}": {
            "_description": "主要主题/内容",
            "_type": "literal<$% str>",
            "data": [[topic]],
            "axes": ["_none_axis"]
        },
        "{目标受众}": {
            "_description": "演示文稿的目标受众",
            "_type": "literal<$% str>",
            "data": [[audience || "一般受众"]],
            "axes": ["_none_axis"]
        },
        "{期望长度}": {
            "_description": "幻灯片数量",
            "_type": "literal<$% str>",
            "data": [[length || "包括标题和问答在内的6张幻灯片"]],
            "axes": ["_none_axis"]
        }
    };

    // Add content references
    const contentRefs = uploadedContent
        .filter(f => f.enabled !== false)
        .map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path || `provisions/inputs/content/${f.name}`,
            type: f.type || 'content',
            ...(f.for ? { for: f.for } : {})
        }));

    if (contentRefs.length > 0) {
        inputsJson['[内容参考元数据]'] = {
            "_description": "提供内容信息的领域/主题材料的元数据",
            "_type": "list[dict]",
            "data": [contentRefs],
            "axes": ["内容参考"]
        };
    }

    // Add style references
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

    const allStyleRefs = [...templateRefs, ...styleGuideRefs];

    if (allStyleRefs.length > 0) {
        inputsJson['[样式参考元数据]'] = {
            "_description": "HTML和PPTX渲染的模板和布局指南的元数据",
            "_type": "list[dict]",
            "data": [allStyleRefs],
            "axes": ["样式参考"]
        };
    }

    const saveBtn = document.getElementById('saveInputsBtn');
    const originalText = saveBtn.textContent;
    saveBtn.textContent = '⏳ 保存中...';
    saveBtn.disabled = true;

    try {
        const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files/inputs.json`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inputsJson, null, 2)
        });

        if (resp.ok) {
            markInputsSaved();
            await uploadFilesToBench();
            addEvent(new Date().toLocaleTimeString('en-US', { hour12: false }), 'completed', `✓ 输入已保存到工作空间`);
            await refreshInspector();
        } else {
            const err = await resp.text();
            alert(`保存失败: ${resp.status} ${err}`);
        }
    } catch (e) {
        alert(`保存错误: ${e.message}`);
    } finally {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    }
}

// ===== Build Inputs Payload (for preview & run) =====
function buildInputsPayload() {
    const topic = document.getElementById('topic').value.trim();
    const audience = document.getElementById('audience').value.trim();
    const length = document.getElementById('length').value.trim();
    const llm = document.getElementById('llmModel').value;

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
        plan_id: planSelect.value || currentPlanId,
        llm_model: llm,
        user_id: `gui_${Date.now()}`,
        ground_inputs: {
            '{演示主题}': { _description: '演示主题', data: [[topic || '未设置']], axes: ['_none_axis'] },
            '{目标受众}': { _description: '目标受众', data: [[audience || '一般受众']], axes: ['_none_axis'] },
            '{期望长度}': { _description: '期望长度', data: [[length || '6张幻灯片']], axes: ['_none_axis'] },
        }
    };

    if (contentRefs.length > 0) {
        payload.ground_inputs['[内容参考元数据]'] = { _description: '内容参考文件', data: [contentRefs], axes: ['内容参考'] };
    }
    if (styleRefs.length > 0) {
        payload.ground_inputs['[样式参考元数据]'] = { _description: '样式/模板参考文件', data: [styleRefs], axes: ['样式参考'] };
    }

    // Add uploaded file previews
    const userContentFiles = uploadedContent.filter(f => !f.isDefault && f.content);
    const userTemplateFiles = uploadedTemplate.filter(f => !f.isDefault && f.content);
    const userStyleFiles = uploadedStyle.filter(f => !f.isDefault && f.content);

    if (userContentFiles.length > 0 || userTemplateFiles.length > 0 || userStyleFiles.length > 0) {
        payload._uploaded_files = {};
        userContentFiles.forEach(f => {
            payload._uploaded_files[`content/${f.name}`] = f.content.substring(0, 200) + (f.content.length > 200 ? '...' : '');
        });
        userTemplateFiles.forEach(f => {
            payload._uploaded_files[`templates/${f.name}`] = f.content.substring(0, 200) + (f.content.length > 200 ? '...' : '');
        });
        userStyleFiles.forEach(f => {
            payload._uploaded_files[`style/${f.name}`] = f.content.substring(0, 200) + (f.content.length > 200 ? '...' : '');
        });
    }

    return payload;
}

