// ============================================================================
// Output Files & Inspector (File Tree)
// ============================================================================

// ===== Output Files Polling =====
async function pollOutputFiles() {
    if (!currentUserId) return;

    try {
        const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files?category=productions&recursive=true`);
        if (resp.ok) {
            const files = await resp.json();
            renderOutputFiles(files);
        }
    } catch (e) {}
}

function renderOutputFiles(files) {
    const allFiles = files.filter(f => !f.is_dir);
    const finalFiles = allFiles.filter(f => f.path.includes('output/'));
    const intermediates = allFiles.filter(f => !f.path.includes('output/'));

    const finalContainer = document.getElementById('finalOutputs');
    if (finalFiles.length === 0) {
        finalContainer.innerHTML = '<div style="color: var(--muted); text-align: center; padding: 16px; font-size: 0.85rem;">正在生成...</div>';
    } else {
        finalContainer.innerHTML = finalFiles.map(f => renderFileCard(f, true)).join('');
    }

    const intermediateContainer = document.getElementById('intermediateFiles');
    if (intermediates.length === 0) {
        intermediateContainer.innerHTML = '<div style="color: var(--muted); text-align: center; padding: 16px; font-size: 0.85rem;">暂无中间文件</div>';
    } else {
        intermediateContainer.innerHTML = intermediates.map(f => renderFileCard(f, false)).join('');
    }
}

function renderFileCard(f, isFinal) {
    const ext = f.name.split('.').pop().toLowerCase();
    const icons = { html: '🌐', pptx: '📊', json: '📋', pdf: '📄', md: '📝' };
    const icon = icons[ext] || '📄';
    const size = f.size > 1024 ? `${(f.size / 1024).toFixed(1)} KB` : `${f.size} B`;

    return `
        <div class="file-card" style="${isFinal ? 'border-color: var(--success); background: rgba(23, 191, 99, 0.05);' : ''}">
            <span class="file-icon">${icon}</span>
            <div class="file-info">
                <div class="file-name">${f.name}</div>
                <div class="file-meta">${size}</div>
            </div>
            <div class="file-actions">
                <button class="btn btn-outline btn-sm" onclick="openFile('${f.path}')">打开</button>
                <button class="btn btn-outline btn-sm" onclick="downloadFile('${f.path}', '${f.name}')">⬇</button>
            </div>
        </div>
    `;
}

function openFile(path) {
    window.open(`${serverUrl}/api/userbenches/${currentUserId}/files/${path}`, '_blank');
}

function downloadFile(path, name) {
    const a = document.createElement('a');
    a.href = `${serverUrl}/api/userbenches/${currentUserId}/files/${path}`;
    a.download = name;
    a.click();
}

// ===== Inspector / File Tree =====
async function refreshInspector() {
    if (!currentUserId) return;

    try {
        const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/structure`);
        if (resp.ok) {
            const structure = await resp.json();
            renderFileTree(structure);
        }
    } catch (e) {
        document.getElementById('fileTree').innerHTML = '<div style="color: var(--muted);">无法加载文件</div>';
    }

    const inputsViewer = document.getElementById('inputsViewer');
    if (inputsViewer) {
        try {
            const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files/inputs.json`);
            if (resp.ok) {
                const text = await resp.text();
                try {
                    inputsViewer.textContent = JSON.stringify(JSON.parse(text), null, 2);
                } catch (e) {
                    inputsViewer.textContent = text;
                }
            }
        } catch (e) {
            inputsViewer.innerHTML = '<div style="color: var(--muted);">无法加载 inputs.json</div>';
        }
    }
}

function renderFileTree(data) {
    const tree = document.getElementById('fileTree');
    const structure = data.structure;

    if (!structure) {
        tree.innerHTML = `<div style="color: var(--muted); text-align: center; padding: 20px;"><small>无法加载文件结构</small></div>`;
        return;
    }

    function countFilesInTree(items) {
        let count = 0;
        for (const item of items) {
            if (item.type === 'directory' && item.children) {
                count += countFilesInTree(item.children);
            } else if (item.type !== 'directory') {
                count++;
            }
        }
        return count;
    }

    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'html': '🌐', 'htm': '🌐', 'json': '📋', 'md': '📝',
            'css': '🎨', 'txt': '📄', 'pptx': '📊', 'pdf': '📕',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️',
        };
        return icons[ext] || '📄';
    }

    function renderItems(items, depth = 0) {
        if (!items || !Array.isArray(items) || items.length === 0) return '';
        let html = '';
        for (const item of items) {
            const indent = `style="padding-left: ${depth * 12}px"`;
            if (item.type === 'directory') {
                const childrenHtml = item.children ? renderItems(item.children, depth + 1) : '';
                const fileCount = item.children ? countFilesInTree(item.children) : 0;
                html += `
                    <div class="tree-item" onclick="event.stopPropagation(); this.classList.toggle('open')" ${indent}>
                        <span class="tree-folder">📁 ${item.name} <small style="color: var(--muted)">(${fileCount})</small></span>
                        <div class="tree-content">${childrenHtml}</div>
                    </div>
                `;
            } else {
                const size = item.size ? ` <small style="color: var(--muted)">(${formatFileSize(item.size)})</small>` : '';
                const icon = getFileIcon(item.name);
                html += `<div class="tree-file" onclick="event.stopPropagation(); viewFile('${item.path}')" ${indent}>${icon} ${item.name}${size}</div>`;
            }
        }
        return html;
    }

    let html = '';
    let hasAnyFiles = false;

    // Inputs
    let inputItems = null;
    if (structure.provisions && Array.isArray(structure.provisions)) {
        const inputsFolder = structure.provisions.find(item =>
            item.type === 'directory' && (item.name === 'inputs' || item.name === 'input')
        );
        if (inputsFolder?.children) inputItems = inputsFolder.children;
    }
    if (!inputItems && structure.inputs?.length > 0) {
        inputItems = structure.inputs;
    }

    if (inputItems?.length > 0) {
        hasAnyFiles = true;
        const fileCount = countFilesInTree(inputItems);
        html += `
            <div class="tree-item" onclick="event.stopPropagation(); this.classList.toggle('open')">
                <span class="tree-folder" style="color: var(--primary)">📥 输入 <small style="color: var(--muted)">(${fileCount} 文件)</small></span>
                <div class="tree-content">${renderItems(inputItems, 1)}</div>
            </div>
        `;
    }

    // Outputs
    if (structure.productions?.length > 0) {
        hasAnyFiles = true;
        const fileCount = countFilesInTree(structure.productions);
        html += `
            <div class="tree-item" onclick="event.stopPropagation(); this.classList.toggle('open')">
                <span class="tree-folder" style="color: var(--success)">📤 输出 <small style="color: var(--muted)">(${fileCount} 文件)</small></span>
                <div class="tree-content">${renderItems(structure.productions, 1)}</div>
            </div>
        `;
    }

    tree.innerHTML = hasAnyFiles ? html : `<div style="color: var(--muted); text-align: center; padding: 20px; font-size: 0.85rem;">
        <div style="margin-bottom: 8px;">📂 工作空间文件</div>
        <small>保存输入或启动运行后，文件将显示在这里</small>
    </div>`;
}

async function viewFile(path) {
    try {
        window.open(`${serverUrl}/api/userbenches/${currentUserId}/files/${path}`, '_blank');
    } catch (e) {
        alert('无法打开文件');
    }
}

