// ============================================================================
// Preview Modals (Input Preview & File Preview)
// ============================================================================

// ===== Input Preview =====
async function previewInputs() {
    const payload = buildInputsPayload();
    const previewContainer = document.getElementById('previewJson');
    const inputs = payload.ground_inputs || {};

    let html = '<div class="input-preview-enhanced">';

    // Basic inputs
    html += '<div class="preview-section">';
    html += '<div class="preview-section-title">📝 基本输入</div>';
    html += `<div class="preview-item"><strong>演示主题:</strong> ${inputs['{演示主题}']?.data?.[0]?.[0] || 'N/A'}</div>`;
    html += `<div class="preview-item"><strong>目标受众:</strong> ${inputs['{目标受众}']?.data?.[0]?.[0] || 'N/A'}</div>`;
    html += `<div class="preview-item"><strong>期望长度:</strong> ${inputs['{期望长度}']?.data?.[0]?.[0] || 'N/A'}</div>`;
    html += `<div class="preview-item"><strong>LLM模型:</strong> ${payload.llm_model || 'N/A'}</div>`;
    html += '</div>';

    // Content references
    const contentRefs = inputs['[内容参考元数据]']?.data?.[0] || [];
    if (contentRefs.length > 0) {
        html += '<div class="preview-section">';
        html += `<div class="preview-section-title">📄 内容参考 (${contentRefs.length})</div>`;
        contentRefs.forEach((ref, idx) => {
            html += renderFilePreviewCard(ref, idx, 'content');
        });
        html += '</div>';
    }

    // Style references
    const allStyleRefs = inputs['[样式参考元数据]']?.data?.[0] || [];
    const templateRefsDisplay = allStyleRefs.filter(r => r.type === 'html_template' || r.path?.includes('/templates/'));
    const styleGuideRefsDisplay = allStyleRefs.filter(r => r.type !== 'html_template' && !r.path?.includes('/templates/'));

    if (templateRefsDisplay.length > 0) {
        html += '<div class="preview-section">';
        html += `<div class="preview-section-title">🖼️ 幻灯片模板 (${templateRefsDisplay.length})</div>`;
        templateRefsDisplay.forEach((ref, idx) => {
            html += renderFilePreviewCard(ref, idx, 'template');
        });
        html += '</div>';
    }

    if (styleGuideRefsDisplay.length > 0) {
        html += '<div class="preview-section">';
        html += `<div class="preview-section-title">🎨 样式指南 (${styleGuideRefsDisplay.length})</div>`;
        styleGuideRefsDisplay.forEach((ref, idx) => {
            html += renderFilePreviewCard(ref, idx, 'style');
        });
        html += '</div>';
    }

    // Raw JSON toggle
    html += '<div class="preview-section">';
    html += '<button class="btn btn-sm btn-outline" style="width: 100%;" onclick="toggleRawJsonView()">📋 显示原始JSON</button>';
    html += '<pre id="rawJsonView" style="display: none; margin-top: 8px; max-height: 300px; overflow: auto;"></pre>';
    html += '</div>';
    html += '</div>';

    previewContainer.innerHTML = html;
    document.getElementById('rawJsonView').textContent = JSON.stringify(payload, null, 2);
    document.getElementById('previewModal').classList.add('open');
}

function renderFilePreviewCard(ref, index, type) {
    const fileName = ref.name || ref.path?.split('/').pop() || 'unknown';
    const isHtml = fileName.endsWith('.html') || fileName.endsWith('.htm');

    return `
        <div class="preview-file-card">
            <div class="preview-file-header" onclick="toggleFileContent('${type}', ${index})">
                <span>
                    ${isHtml ? '🖼️' : '📄'} ${fileName}
                    ${ref.isDefault ? '<span class="badge-default">默认</span>' : '<span class="badge-upload">已上传</span>'}
                </span>
                <span class="preview-toggle" id="toggle-${type}-${index}">▶</span>
            </div>
            <div class="preview-file-content" id="content-${type}-${index}" style="display: none;">
                <div class="preview-file-loading">加载中...</div>
            </div>
        </div>
    `;
}

async function toggleFileContent(type, index) {
    const contentEl = document.getElementById(`content-${type}-${index}`);
    const toggleEl = document.getElementById(`toggle-${type}-${index}`);

    if (contentEl.style.display === 'block') {
        contentEl.style.display = 'none';
        toggleEl.textContent = '▶';
        return;
    }

    contentEl.style.display = 'block';
    toggleEl.textContent = '▼';

    const list = getListByType(type);
    const file = list[index];

    if (!file) {
        contentEl.innerHTML = '<div class="preview-file-error">文件不存在</div>';
        return;
    }

    let content = '';

    if (file.content) {
        content = file.content;
    } else if (file.isDefault && file.path) {
        try {
            const resp = await fetch(`${serverUrl}/api/plans/${currentPlanId}/files/${file.path}`);
            if (resp.ok) {
                content = (await resp.json()).content;
            } else {
                contentEl.innerHTML = `<div class="preview-file-error">无法加载: ${resp.status}</div>`;
                return;
            }
        } catch (e) {
            contentEl.innerHTML = `<div class="preview-file-error">加载失败: ${e.message}</div>`;
            return;
        }
    } else {
        contentEl.innerHTML = '<div class="preview-file-error">无内容</div>';
        return;
    }

    const fileName = file.path || file.name || '';
    const isHtml = fileName.endsWith('.html') || fileName.endsWith('.htm');
    const isJson = fileName.endsWith('.json');

    let html = '<div class="preview-file-inner">';

    if (isHtml || fileName.endsWith('.md')) {
        html += `
            <div class="preview-file-actions">
                <button class="btn btn-sm btn-outline" onclick="openInputFileInWindow('${type}', ${index})">🖼️ 渲染视图</button>
                <button class="btn btn-sm btn-outline" onclick="copyInputFileContent('${type}', ${index})">📋 复制</button>
            </div>
            <pre class="preview-file-source">${escapeHtml(content)}</pre>
        `;
    } else if (isJson) {
        try {
            html += `<pre class="preview-file-source">${escapeHtml(JSON.stringify(JSON.parse(content), null, 2))}</pre>`;
        } catch (e) {
            html += `<pre class="preview-file-source">${escapeHtml(content)}</pre>`;
        }
    } else {
        html += `<pre class="preview-file-source">${escapeHtml(content)}</pre>`;
    }

    html += '</div>';
    contentEl.innerHTML = html;
    contentEl.dataset.content = content;

    if (isHtml || fileName.endsWith('.md')) {
        openRenderedHtmlWindow(content, fileName);
    }
}

function openInputFileInWindow(type, index) {
    const contentEl = document.getElementById(`content-${type}-${index}`);
    const content = contentEl?.dataset?.content || '';
    if (!content) { alert('无内容可渲染'); return; }

    const list = getListByType(type);
    const file = list[index];
    openRenderedHtmlWindow(content, file?.path || file?.name || 'preview.html');
}

function copyInputFileContent(type, index) {
    const contentEl = document.getElementById(`content-${type}-${index}`);
    const content = contentEl.dataset.content;
    if (content) {
        navigator.clipboard.writeText(content).then(() => alert('已复制文件内容到剪贴板！'));
    }
}

function toggleRawJsonView() {
    const rawView = document.getElementById('rawJsonView');
    const btn = event.target;
    if (rawView.style.display === 'none') {
        rawView.style.display = 'block';
        btn.textContent = '📋 隐藏原始JSON';
    } else {
        rawView.style.display = 'none';
        btn.textContent = '📋 显示原始JSON';
    }
}

function closePreview() {
    document.getElementById('previewModal').classList.remove('open');
}

function copyPreview() {
    const payload = buildInputsPayload();
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).then(() => {
        alert('已复制完整JSON到剪贴板！');
    });
}

// ===== File Preview Modal =====
async function previewFile(type, index) {
    const list = getListByType(type);
    const file = list[index];
    if (!file) { alert('文件不存在'); return; }

    const fileName = file.path || file.name || '';
    const displayName = file.name || fileName.split('/').pop();
    const isHtml = fileName.endsWith('.html') || fileName.endsWith('.htm');

    document.getElementById('filePreviewTitle').textContent = `⏳ 加载中: ${displayName}`;
    document.getElementById('filePreviewContent').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--muted);">加载文件内容...</div>';
    document.getElementById('filePreviewModal').classList.add('open');

    let content = '';

    if (file.content) {
        content = file.content;
    } else if (file.isDefault && file.path) {
        if (!currentPlanId) {
            content = '❌ 错误：请先连接服务器';
        } else {
            try {
                const resp = await fetch(`${serverUrl}/api/plans/${currentPlanId}/files/${file.path}`);
                if (resp.ok) {
                    content = (await resp.json()).content;
                } else {
                    content = `❌ 无法加载文件: ${resp.status} ${resp.statusText}\n\n路径: ${file.path}`;
                }
            } catch (e) {
                content = `❌ 加载失败: ${e.message}\n\n请确保服务器正在运行`;
            }
        }
    } else {
        content = '⚠️ 无可用内容预览\n\n该文件没有本地内容，也没有服务器路径';
    }

    document.getElementById('filePreviewTitle').textContent = `📄 ${displayName}`;
    currentPreviewContent = content;
    currentPreviewFilePath = fileName;
    renderPreviewContent(fileName, content);

    if (isHtml || fileName.endsWith('.md')) {
        openRenderedHtmlWindow(content, fileName);
    }
}

function renderPreviewContent(fileName, content) {
    const previewEl = document.getElementById('filePreviewContent');
    const isJson = fileName.endsWith('.json');
    const isError = content.startsWith('❌') || content.startsWith('⚠️');

    if (isError) {
        previewEl.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--warning);">
            <pre style="white-space: pre-wrap; text-align: left; background: rgba(255, 173, 31, 0.1); padding: 16px; border-radius: 8px;">${escapeHtml(content)}</pre>
        </div>`;
        return;
    }

    if (isJson) {
        try {
            previewEl.innerHTML = `<pre>${escapeHtml(JSON.stringify(JSON.parse(content), null, 2))}</pre>`;
        } catch (e) {
            previewEl.innerHTML = `<pre>${escapeHtml(content)}</pre>`;
        }
    } else {
        previewEl.innerHTML = `<pre>${escapeHtml(content)}</pre>`;
    }
}

function togglePreviewMode() {
    const isHtml = currentPreviewFilePath.endsWith('.html') || currentPreviewFilePath.endsWith('.htm');
    const isMd = currentPreviewFilePath.endsWith('.md');
    if (!isHtml && !isMd) { alert('只有 HTML 和 Markdown 文件支持渲染'); return; }
    openRenderedHtmlWindow(currentPreviewContent, currentPreviewFilePath);
}

function closeFilePreview() {
    document.getElementById('filePreviewModal').classList.remove('open');
    currentPreviewContent = '';
    currentPreviewFilePath = '';
}

function copyFilePreview() {
    const previewEl = document.getElementById('filePreviewContent');
    if (previewEl.querySelector('iframe')) {
        navigator.clipboard.writeText(currentPreviewContent).then(() => alert('已复制源代码到剪贴板！'));
    } else {
        navigator.clipboard.writeText(previewEl.textContent).then(() => alert('已复制到剪贴板！'));
    }
}

// ===== Rendered Window (HTML / Markdown) =====
function openRenderedHtmlWindow(content, filePath) {
    const isHtml = filePath.endsWith('.html') || filePath.endsWith('.htm');
    const isMd = filePath.endsWith('.md');

    let previewContent;
    if (isHtml) {
        previewContent = replaceTemplatePlaceholders(content);
    } else if (isMd) {
        previewContent = renderMarkdownToHtml(content);
    } else {
        previewContent = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:monospace;padding:20px;white-space:pre-wrap;}</style></head><body>${escapeHtml(content)}</body></html>`;
    }

    const blob = new Blob([previewContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const fileName = filePath.split('/').pop() || 'preview.html';

    const width = 1100, height = 700;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    const newWindow = window.open(url, `preview_${Date.now()}`,
        `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no`);

    if (newWindow) {
        newWindow.document.title = `预览: ${fileName}`;
        newWindow.onload = () => URL.revokeObjectURL(url);
    } else {
        alert('无法打开新窗口，请检查浏览器是否阻止了弹出窗口');
        URL.revokeObjectURL(url);
    }
}

// ===== Template Placeholders =====
function replaceTemplatePlaceholders(content) {
    const sampleData = {
        'title': '示例标题 - Sample Title',
        'presentation_title': '演示文稿标题',
        'subtitle': '副标题内容',
        'presenter': '演讲者姓名',
        'date': new Date().toLocaleDateString('zh-CN'),
        'slide_number': '1',
        'visual_description': '[图表/图像描述区域]',
        'caption': '图片说明文字',
        'speaker_notes': '演讲者备注：这里是演讲提示内容...',
        'content': '• 要点一\\n• 要点二\\n• 要点三',
        'bullet_points': '• 第一点内容\\n• 第二点内容\\n• 第三点内容',
        'key_message': '核心信息内容',
        'quote': '"这是一段引用文字"',
        'author': '作者名称'
    };
    return content.replace(/\{\{(\w+)\}\}/g, (match, key) => {
        return sampleData[key.toLowerCase()] || `[${key}]`;
    });
}

// ===== Markdown Renderer =====
function renderMarkdownToHtml(markdown) {
    let html = markdown
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
    body { font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #fff; }
    h1, h2, h3 { color: #0078D4; margin-top: 1.5em; }
    h1 { font-size: 1.8em; border-bottom: 2px solid #0078D4; padding-bottom: 0.3em; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; }
    pre { background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }
    pre code { background: none; padding: 0; }
    ul, ol { padding-left: 24px; }
    li { margin: 8px 0; }
    strong { color: #0078D4; }
    hr { border: none; border-top: 1px solid #e1e8ed; margin: 24px 0; }
    p { margin: 12px 0; }
</style>
</head><body><p>${html}</p></body></html>`;
}

