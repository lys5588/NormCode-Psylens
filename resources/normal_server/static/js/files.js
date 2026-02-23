/**
 * NormCode Server UI - UserBench Files Browser
 */

let currentUserBenchId = null;
let currentFilesCategory = 'all';
let currentFilePath = '';
let userBenchStructure = null;
let fileEventSource = null;
let directoryStack = [];

function showFilesCategory(category) {
    currentFilesCategory = category;
    
    document.querySelectorAll('.files-nav-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === category);
    });
    
    const categoryNames = {
        'all': 'All Files',
        'productions': 'Productions (Outputs)',
        'provisions': 'Provisions (Prompts, Scripts)',
        'root': 'Plan Files',
        'logs': 'Logs'
    };
    document.getElementById('currentCategory').textContent = categoryNames[category] || category;
    
    renderFilesForCategory(category);
}

async function selectUserBench(userbenchId) {
    if (!userbenchId) {
        currentUserBenchId = null;
        document.getElementById('filesPlaceholder').classList.remove('hidden');
        document.getElementById('filesTree').classList.add('hidden');
        document.getElementById('filePreview').classList.add('hidden');
        disconnectFileEvents();
        return;
    }
    
    currentUserBenchId = userbenchId;
    document.getElementById('filesRunId').textContent = userbenchId.slice(0, 12) + '...';
    
    await loadUserBenchStructure(userbenchId);
    connectFileEvents(userbenchId);
}

function selectWorkspace(id) { return selectUserBench(id); }

async function loadUserBenchStructure(userbenchId) {
    try {
        const resp = await fetch(`${API}/userbenches/${userbenchId}/structure`);
        if (!resp.ok) throw new Error('Failed to load userbench');
        
        userBenchStructure = await resp.json();
        
        const structure = userBenchStructure.structure || {};
        document.getElementById('productionsCount').textContent = countFiles(structure.productions);
        document.getElementById('provisionsCount').textContent = countFiles(structure.provisions);
        document.getElementById('rootCount').textContent = (structure.root_files || []).length;
        document.getElementById('logsCount').textContent = countFiles(structure.logs);
        
        document.getElementById('filesPlaceholder').classList.add('hidden');
        document.getElementById('filesTree').classList.remove('hidden');
        
        renderFilesForCategory(currentFilesCategory);
        
    } catch (e) {
        console.error('Error loading userbench:', e);
        showToast('Failed to load userbench: ' + e.message, 'error');
    }
}

function countFiles(items) {
    if (!items) return 0;
    let count = 0;
    items.forEach(item => {
        if (item.type === 'file') count++;
        else if (item.children) count += countFiles(item.children);
    });
    return count;
}

function renderFilesForCategory(category) {
    if (!userBenchStructure) return;
    
    const structure = userBenchStructure.structure || {};
    let items = [];
    
    if (category === 'all') {
        items = [
            { name: 'productions', type: 'directory', children: structure.productions || [], icon: '📦' },
            { name: 'provisions', type: 'directory', children: structure.provisions || [], icon: '📋' },
            { name: 'logs', type: 'directory', children: structure.logs || [], icon: '📝' },
            ...(structure.root_files || []).map(f => ({ ...f, icon: getFileIcon(f.name) }))
        ];
    } else if (category === 'root') {
        items = (structure.root_files || []).map(f => ({ ...f, icon: getFileIcon(f.name) }));
    } else {
        items = structure[category] || [];
    }
    
    renderFileList(items);
}

function renderFileList(items, path = '') {
    const container = document.getElementById('fileList');
    document.getElementById('currentPath').textContent = path || '/';
    
    if (!items.length) {
        container.innerHTML = '<div class="empty-state">No files</div>';
        return;
    }
    
    items.sort((a, b) => {
        if (a.type === 'directory' && b.type !== 'directory') return -1;
        if (a.type !== 'directory' && b.type === 'directory') return 1;
        return a.name.localeCompare(b.name);
    });
    
    container.innerHTML = items.map(item => {
        const icon = item.icon || (item.type === 'directory' ? '📁' : getFileIcon(item.name));
        const sizeStr = item.size ? formatSize(item.size) : '';
        const isDir = item.type === 'directory';
        
        return `
            <div class="file-item ${isDir ? 'directory' : 'file'}" 
                 onclick="${isDir ? `openDirectory('${item.name}', ${JSON.stringify(item.children || []).replace(/"/g, '&quot;')})` : `previewFile('${item.path || item.name}', '${item.name}')`}">
                <span class="file-icon">${icon}</span>
                <span class="file-name">${item.name}</span>
                <span class="file-meta">${sizeStr}</span>
                ${!isDir && item.url ? `<a class="file-download" href="${item.url}" download onclick="event.stopPropagation()">⬇</a>` : ''}
            </div>
        `;
    }).join('');
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'json': '📊', 'html': '🌐', 'md': '📝', 'py': '🐍',
        'ncd': '📜', 'ncds': '📜', 'txt': '📄', 'js': '💛',
        'css': '🎨', 'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️',
        'gif': '🖼️', 'svg': '🎨', 'log': '📋',
    };
    return icons[ext] || '📄';
}

function openDirectory(name, children) {
    directoryStack.push({ name, items: children });
    currentFilePath = directoryStack.map(d => d.name).join('/');
    renderFileList(children, currentFilePath);
}

function goBack() {
    if (directoryStack.length > 0) {
        directoryStack.pop();
        if (directoryStack.length > 0) {
            const current = directoryStack[directoryStack.length - 1];
            currentFilePath = directoryStack.map(d => d.name).join('/');
            renderFileList(current.items, currentFilePath);
        } else {
            currentFilePath = '';
            renderFilesForCategory(currentFilesCategory);
        }
    }
}

async function previewFile(path, filename) {
    if (!currentUserBenchId) return;
    
    document.getElementById('previewFilename').textContent = filename;
    document.getElementById('filePreview').classList.remove('hidden');
    document.getElementById('previewContent').innerHTML = '<div class="loading">Loading...</div>';
    
    const ext = filename.split('.').pop().toLowerCase();
    const isImage = ['png', 'jpg', 'jpeg', 'gif', 'svg'].includes(ext);
    const isHtml = ext === 'html';
    
    try {
        const url = `${API}/userbenches/${currentUserBenchId}/files/${path}`;
        
        if (isImage) {
            document.getElementById('previewContent').innerHTML = `<img src="${url}" alt="${filename}" class="preview-image">`;
        } else if (isHtml) {
            document.getElementById('previewContent').innerHTML = `
                <iframe src="${url}" class="preview-iframe"></iframe>
                <div class="preview-note">HTML preview - <a href="${url}" target="_blank">Open in new tab</a></div>
            `;
        } else {
            const resp = await fetch(`${url}/content`);
            if (!resp.ok) throw new Error('Failed to load file');
            const data = await resp.json();
            
            const content = data.content || '';
            if (['json', 'ncd', 'ncds'].includes(ext)) {
                try {
                    const formatted = JSON.stringify(JSON.parse(content), null, 2);
                    document.getElementById('previewContent').innerHTML = `<pre class="preview-code json">${escapeHtml(formatted)}</pre>`;
                } catch {
                    document.getElementById('previewContent').innerHTML = `<pre class="preview-code">${escapeHtml(content)}</pre>`;
                }
            } else if (['py', 'js', 'css'].includes(ext)) {
                document.getElementById('previewContent').innerHTML = `<pre class="preview-code ${ext}">${escapeHtml(content)}</pre>`;
            } else if (ext === 'md') {
                document.getElementById('previewContent').innerHTML = `<div class="preview-markdown">${renderMarkdown(content)}</div>`;
            } else {
                document.getElementById('previewContent').innerHTML = `<pre class="preview-code">${escapeHtml(content)}</pre>`;
            }
        }
    } catch (e) {
        document.getElementById('previewContent').innerHTML = `<div class="error">Error loading file: ${e.message}</div>`;
    }
}

function closePreview() {
    document.getElementById('filePreview').classList.add('hidden');
}

function downloadFile() {
    const filename = document.getElementById('previewFilename').textContent;
    const path = currentFilePath ? `${currentFilePath}/${filename}` : filename;
    const url = `${API}/userbenches/${currentUserBenchId}/files/${path}`;
    window.open(url, '_blank');
}

async function refreshUserBenchFiles() {
    if (currentUserBenchId) {
        await loadUserBenchStructure(currentUserBenchId);
        showToast('Files refreshed', 'success');
    }
}

function refreshWorkspaceFiles() { return refreshUserBenchFiles(); }

function connectFileEvents(userbenchId) {
    disconnectFileEvents();
    
    fileEventSource = new EventSource(`${API}/userbenches/${userbenchId}/events/stream`);
    
    fileEventSource.addEventListener('connected', () => {
        document.getElementById('fileEventStatus').textContent = 'Connected';
        document.getElementById('fileEventStatus').classList.add('connected');
    });
    
    fileEventSource.addEventListener('file', (e) => {
        const event = JSON.parse(e.data);
        addFileEvent(event);
        loadUserBenchStructure(userbenchId);
    });
    
    fileEventSource.addEventListener('keepalive', () => {});
    
    fileEventSource.onerror = () => {
        document.getElementById('fileEventStatus').textContent = 'Disconnected';
        document.getElementById('fileEventStatus').classList.remove('connected');
    };
}

function disconnectFileEvents() {
    if (fileEventSource) {
        fileEventSource.close();
        fileEventSource = null;
    }
    document.getElementById('fileEventStatus').textContent = 'Disconnected';
    document.getElementById('fileEventStatus').classList.remove('connected');
}

function addFileEvent(event) {
    const container = document.getElementById('recentFileEvents');
    const el = document.createElement('span');
    el.className = 'file-event-item';
    el.textContent = `${event.event_type}: ${event.path.split('/').pop()}`;
    el.title = event.path;
    
    container.insertBefore(el, container.firstChild);
    while (container.children.length > 5) {
        container.removeChild(container.lastChild);
    }
}

function browseRunFiles(runId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="files"]').classList.add('active');
    document.getElementById('filesPanel').classList.add('active');
    
    document.getElementById('userbenchSelect').value = runId;
    selectUserBench(runId);
}

async function updateUserBenchSelector() {
    try {
        const resp = await fetch(`${API}/userbenches`);
        const benches = await resp.json();
        
        const select = document.getElementById('userbenchSelect');
        const currentValue = select.value;
        
        select.innerHTML = '<option value="">Select a run...</option>' + 
            benches.map(b => `
                <option value="${b.userbench_id || b.workspace_id}" ${(b.userbench_id || b.workspace_id) === currentValue ? 'selected' : ''}>
                    ${b.plan_id || 'Unknown'} - ${(b.userbench_id || b.workspace_id).slice(0, 8)}... 
                    (${b.file_count} files)
                </option>
            `).join('');
    } catch (e) {
        console.error('Failed to load userbenches:', e);
    }
}

function updateWorkspaceSelector() { return updateUserBenchSelector(); }
