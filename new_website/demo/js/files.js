// ============================================================================
// File Upload & Reference Management
// ============================================================================

// ===== Drag & Drop Handlers =====
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e, type) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    addFiles(files, type);
}

function handleFiles(e, type) {
    const files = Array.from(e.target.files);
    addFiles(files, type);
    e.target.value = '';
}

// ===== File Addition =====
function addFiles(files, type) {
    let list = getListByType(type);

    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            let folderPath, fileType;

            if (type === 'content') {
                folderPath = `provisions/inputs/content/${file.name}`;
                fileType = 'content';
            } else if (type === 'template') {
                folderPath = `provisions/inputs/templates/${file.name}`;
                fileType = 'html_template';
            } else {
                folderPath = `provisions/inputs/style/${file.name}`;
                fileType = 'guide';
            }

            list.push({
                name: file.name,
                path: folderPath,
                content: e.target.result,
                type: fileType,
                isDefault: false,
                enabled: true
            });
            renderRefsList(type);
        };
        reader.readAsText(file);
    });
}

// ===== List Helpers =====
function getListByType(type) {
    if (type === 'content') return uploadedContent;
    if (type === 'template') return uploadedTemplate;
    return uploadedStyle;
}

function removeFile(type, index) {
    const list = getListByType(type);
    list.splice(index, 1);
    renderRefsList(type);
}

function removeDefaultRef(type, index) {
    const list = getListByType(type);
    list.splice(index, 1);
    renderRefsList(type);
}

function toggleRef(type, index) {
    const list = getListByType(type);
    list[index].enabled = !list[index].enabled;
    renderRefsList(type);
}

// ===== Default Refs from Plan =====
function renderDefaultRefs(type, refs) {
    if (type === 'style') {
        const templateRefs = [];
        const styleRefs = [];

        refs.forEach(r => {
            const refWithDefaults = { ...r, isDefault: true, enabled: true };
            if (r.path?.endsWith('.html') || r.path?.endsWith('.htm') || r.type === 'html_template') {
                templateRefs.push(refWithDefaults);
            } else {
                styleRefs.push(refWithDefaults);
            }
        });

        const userTemplates = uploadedTemplate.filter(f => !f.isDefault);
        const userStyles = uploadedStyle.filter(f => !f.isDefault);

        uploadedTemplate = [...templateRefs, ...userTemplates];
        uploadedStyle = [...styleRefs, ...userStyles];

        renderRefsList('template');
        renderRefsList('style');
        return;
    }

    const defaultRefs = refs.map(r => ({ ...r, isDefault: true, enabled: true }));
    const currentList = getListByType(type);
    const userUploads = currentList.filter(f => !f.isDefault);
    const mergedList = [...defaultRefs, ...userUploads];

    if (type === 'content') {
        uploadedContent = mergedList;
    } else if (type === 'template') {
        uploadedTemplate = mergedList;
    } else {
        uploadedStyle = mergedList;
    }

    renderRefsList(type);
}

// ===== Render Refs Lists =====
function renderRefsList(type) {
    const list = getListByType(type);
    const container = document.getElementById(type + 'Files');
    const countEl = document.getElementById(type + 'Count');

    const enabledCount = list.filter(f => f.enabled !== false).length;
    if (countEl) {
        countEl.textContent = list.length > 0 ? `(${enabledCount}/${list.length} enabled)` : '';
    }

    if (list.length === 0) {
        const typeLabel = type === 'content' ? '内容' : (type === 'template' ? '模板' : '样式');
        container.innerHTML = `<div style="color: var(--muted); font-size: 0.8rem; padding: 8px; background: var(--bg); border-radius: 6px; text-align: center;">
            暂无${typeLabel}文件。<br>
            <small>拖拽上传文件，或连接服务器加载默认配置</small>
        </div>`;
        return;
    }

    const defaultIndices = [];
    const userIndices = [];
    list.forEach((f, i) => {
        if (f.isDefault) defaultIndices.push(i);
        else userIndices.push(i);
    });

    let html = '';

    if (defaultIndices.length > 0) {
        html += '<div style="font-size: 0.75rem; color: var(--success); margin-bottom: 6px; font-weight: 500;">📋 来自计划 (inputs.json):</div>';
        html += defaultIndices.map(idx => renderRefItem(list[idx], type, idx)).join('');
    }

    if (userIndices.length > 0) {
        if (defaultIndices.length > 0) {
            html += '<div style="font-size: 0.75rem; color: var(--warning); margin-top: 10px; margin-bottom: 6px; font-weight: 500;">📤 您的上传:</div>';
        }
        html += userIndices.map(idx => renderRefItem(list[idx], type, idx)).join('');
    }

    container.innerHTML = html;
}

function renderRefItem(f, type, idx) {
    const checkboxId = `${type}_${idx}`;
    const checked = f.enabled !== false ? 'checked' : '';
    const isHtml = f.name?.endsWith('.html') || f.name?.endsWith('.htm');
    const borderColor = f.isDefault ? 'var(--success)' : 'var(--warning)';
    const icon = isHtml ? '🖼️' : (f.isDefault ? '📎' : '📄');
    const removeAction = f.isDefault
        ? `removeDefaultRef('${type}', ${idx})`
        : `removeFile('${type}', ${idx})`;

    return `
        <div class="uploaded-file file-item" style="${f.enabled === false ? 'opacity: 0.5;' : ''} border-left: 3px solid ${borderColor}; margin-left: 0;">
            <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                <input type="checkbox" id="${checkboxId}" ${checked} onchange="toggleRef('${type}', ${idx})">
                <span class="file-name-clickable" onclick="previewFile('${type}', ${idx})" title="点击预览文件">
                    ${icon} ${f.name}
                </span>
            </div>
            <div style="display: flex; gap: 4px;">
                <button class="btn-preview" onclick="previewFile('${type}', ${idx})" title="预览文件">👁️ 预览</button>
                <span class="remove" onclick="${removeAction}" title="从列表移除">✕</span>
            </div>
        </div>
    `;
}

