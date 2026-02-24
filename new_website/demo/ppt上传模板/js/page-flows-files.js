/**
 * Page-Flows Files — PPT Template variant
 *
 * Template category:
 *   - Accepts .pptx only, read as ArrayBuffer (binary), max 1 file.
 *   - Uploading a second .pptx replaces the first.
 *   - No text conversion; shows file icon + name, no preview.
 *
 * Content / Style categories:
 *   - Same behaviour as the original demo (text + conversion pipeline).
 */

// ---- Category helpers ----
function getFileArray(category) {
    if (category === 'content') return pfContent;
    if (category === 'template') return pfTemplate;
    return pfStyle;
}

function renderFileList(category) {
    const arr    = getFileArray(category);
    const listId = category === 'content'  ? 'pfContentList'
                 : category === 'template' ? 'pfTemplateList'
                 : 'pfStyleList';
    const el = document.getElementById(listId);
    if (!el) return;

    if (arr.length === 0) { el.innerHTML = ''; return; }

    if (category === 'template') {
        // Template: single entry, no click-to-preview (binary PPTX)
        el.innerHTML = arr.map((f, i) => {
            const prefix = f.isDefault ? '📌 ' : '📄 ';
            return `
            <div class="pf-file-item">
                <span>${prefix}${escapeHtml(f.name)}</span>
                <button class="pf-file-remove" onclick="removeFile('template',${i})">&times;</button>
            </div>`;
        }).join('');

        // Update drop zone label to hint that uploading will replace
        const dropLabel = document.getElementById('pfTemplateDropLabel');
        if (dropLabel) dropLabel.setAttribute('data-i18n', 'pf.templateReplace');
        if (dropLabel) dropLabel.textContent = t('templateReplace');
    } else {
        el.innerHTML = arr.map((f, i) => {
            const prefix = f.isDefault ? '📌 ' : f.convertedFrom ? '🔄 ' : '';
            const suffix = f.convertedFrom
                ? ` <span class="pf-converted-badge">(.${f.convertedFrom.split('.').pop()})</span>`
                : '';
            return `
            <div class="pf-file-item" onclick="previewFile('${category}',${i})">
                <span>${prefix}${escapeHtml(f.name)}${suffix}</span>
                <button class="pf-file-remove" onclick="event.stopPropagation();removeFile('${category}',${i})">&times;</button>
            </div>`;
        }).join('');
    }
}

function removeFile(category, idx) {
    getFileArray(category).splice(idx, 1);
    renderFileList(category);

    // If template list is now empty, restore the drop label
    if (category === 'template') {
        const dropLabel = document.getElementById('pfTemplateDropLabel');
        if (dropLabel) dropLabel.textContent = t('dropTemplate');
    }
}

// ---- File input / drop handlers ----
async function pfFiles(event, category) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    event.target.value = '';
    try {
        await pfProcessFiles(list, category);
    } catch (e) {
        console.error('[pfFiles]', e);
        alert('File processing error: ' + e.message);
    }
}

async function pfDrop(event, category) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    const files = event.dataTransfer.files;
    if (!files || files.length === 0) return;
    try {
        await pfProcessFiles(Array.from(files), category);
    } catch (e) {
        console.error('[pfDrop]', e);
        alert('File drop error: ' + e.message);
    }
}

function pfDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function pfDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

// ---- Core processing ----
async function pfProcessFiles(files, category) {
    // ---- TEMPLATE: binary path, single-file enforcement ----
    if (category === 'template') {
        const pptxFiles = files.filter(f => /\.pptx$/i.test(f.name));
        const others    = files.filter(f => !/\.pptx$/i.test(f.name));

        if (others.length > 0) {
            alert('Only .pptx files are accepted as templates.');
        }
        if (pptxFiles.length === 0) return;

        // Use only the first .pptx if multiple dropped
        const file = pptxFiles[0];
        let buffer;
        try {
            buffer = await file.arrayBuffer();
        } catch (e) {
            alert('Could not read file: ' + e.message);
            return;
        }

        // Replace existing template (enforce max 1)
        pfTemplate.length = 0;
        pfTemplate.push({
            name:      file.name,
            path:      `provisions/inputs/模板/${file.name}`,
            type:      'pptx_file',
            binary:    buffer,
            isDefault: false
        });
        renderFileList('template');
        return;
    }

    // ---- CONTENT / STYLE: original text + conversion pipeline ----
    const textFiles   = [];
    const convertibles = [];
    const legacy      = [];

    files.forEach(file => {
        if (LEGACY_BINARY_EXTS.test(file.name))  { legacy.push(file); }
        else if (isConvertible(file.name))        { convertibles.push(file); }
        else                                       { textFiles.push(file); }
    });

    textFiles.forEach(f => pfReadTextFile(f, category));

    if (legacy.length > 0) alert(t('legacyFormat'));

    if (convertibles.length === 0) return;

    const proceed = await showConvertWarning(convertibles.map(f => f.name));
    if (!proceed) return;

    const dropId   = category === 'content' ? 'pfContentDrop' : 'pfStyleDrop';
    const dropSpan = document.getElementById(dropId)?.querySelector('span');
    const origText = dropSpan?.textContent || '';

    for (const file of convertibles) {
        if (dropSpan) dropSpan.textContent = t('converting') + ' ' + file.name + '…';
        try {
            const text    = await convertFileToText(file);
            const txtName = file.name.replace(/\.[^.]+$/, '.txt');
            const catPath = category === 'style' ? 'style' : 'content';
            getFileArray(category).push({
                name:          txtName,
                path:          `provisions/inputs/${catPath}/${txtName}`,
                content:       text,
                isDefault:     false,
                convertedFrom: file.name
            });
            renderFileList(category);
        } catch (e) {
            alert(t('convertFailed') + file.name + ': ' + e.message);
        }
    }

    if (dropSpan) dropSpan.textContent = origText;
}

function pfReadTextFile(file, category) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const catPath = category === 'style' ? 'style' : 'content';
        getFileArray(category).push({
            name:      file.name,
            path:      `provisions/inputs/${catPath}/${file.name}`,
            content:   e.target.result,
            isDefault: false
        });
        renderFileList(category);
    };
    reader.onerror = () => {
        alert('Could not read file: ' + file.name);
    };
    reader.readAsText(file);
}

// ---- File preview (content & style only) ----
const BINARY_EXTS = /\.(pptx|xlsx|docx|pdf|zip|tar|gz|7z|rar|png|jpg|jpeg|gif|bmp|webp|svg|ico|mp3|mp4|wav|avi|mov|woff2?|ttf|eot|exe|dll|so|bin|dat)$/i;

function isPreviewable(name) {
    return !BINARY_EXTS.test(name);
}

function detectRenderMode(name, opts) {
    if (opts?.renderAs) return opts.renderAs;
    if (/\.html?$/i.test(name)) return 'html';
    if (/\.md$/i.test(name))   return 'markdown';
    if (/\.json$/i.test(name)) return 'json';
    return 'text';
}

function renderMarkdownToHtml(markdown) {
    let html = markdown
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
        .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g,     '<em>$1</em>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    return `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>body{font-family:'Segoe UI',system-ui,sans-serif;line-height:1.6;color:#333;max-width:800px;margin:0 auto;padding:20px}
h1,h2,h3{color:#0550ae}code{background:#f5f5f5;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace}
pre{background:#f5f5f5;padding:16px;border-radius:8px;overflow-x:auto}
ul{padding-left:24px}li{margin:8px 0}strong{color:#0550ae}</style>
</head><body><p>${html}</p></body></html>`;
}

function renderPreviewContent(body, name, content, opts) {
    body.innerHTML = '';
    const toggleBtn = document.getElementById('pfPreviewToggle');

    if (!isPreviewable(name) && !(opts?.renderAs || opts?.fileType)) {
        const ext = name.split('.').pop().toUpperCase();
        const div = document.createElement('div');
        div.className = 'pf-preview-placeholder';
        div.innerHTML = `
            <div class="pf-ph-icon">&#128196;</div>
            <div class="pf-ph-name">${escapeHtml(name)}</div>
            <div>${ext} file — preview not available</div>
            ${opts?.downloadUrl ? `<button class="pf-preview-dl" onclick="pfDownload('${opts.downloadUrl}','${escapeHtml(name)}')">${t('download')}</button>` : ''}
        `;
        body.appendChild(div);
        toggleBtn.style.display = 'none';
        return;
    }

    const mode     = detectRenderMode(name, opts);
    const hasToggle = mode === 'html' || mode === 'markdown' || mode === 'json';
    _previewState   = { name, content, rendered: hasToggle, mode };

    if (hasToggle) {
        toggleBtn.style.display = '';
        toggleBtn.textContent   = t('source');
        toggleBtn.classList.remove('active');
    } else {
        toggleBtn.style.display = 'none';
    }

    if (mode === 'markdown') {
        const iframe = document.createElement('iframe');
        iframe.sandbox = 'allow-same-origin allow-scripts';
        body.appendChild(iframe);
        iframe.contentDocument.open();
        iframe.contentDocument.write(renderMarkdownToHtml(content));
        iframe.contentDocument.close();
    } else if (mode === 'json') {
        renderJsonPreview(body, content);
    } else {
        const pre = document.createElement('pre');
        pre.textContent = content;
        body.appendChild(pre);
    }
}

function renderSourceView(body, content) {
    body.innerHTML = '';
    const pre = document.createElement('pre');
    pre.textContent = content;
    body.appendChild(pre);
}

function togglePreviewMode() {
    const body      = document.getElementById('pfPreviewBody');
    const toggleBtn = document.getElementById('pfPreviewToggle');
    const { content, rendered, mode } = _previewState;
    if (rendered) {
        renderSourceView(body, content);
        toggleBtn.textContent = t('rendered');
        toggleBtn.classList.add('active');
        _previewState.rendered = false;
    } else {
        if (mode === 'json') renderJsonPreview(body, content);
        else renderPreviewContent(body, _previewState.name, content, { renderAs: mode });
        toggleBtn.textContent = t('source');
        toggleBtn.classList.remove('active');
        _previewState.rendered = true;
    }
}

function renderJsonPreview(body, content) {
    let parsed;
    try { parsed = JSON.parse(content); } catch {
        const pre = document.createElement('pre');
        pre.textContent = content;
        body.appendChild(pre);
        return;
    }
    const container = document.createElement('div');
    container.className = 'pf-json-sections';
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        Object.keys(parsed).forEach(k => { container.innerHTML += buildJsonSection(k, parsed[k]); });
    } else {
        container.innerHTML = buildJsonSection('root', parsed);
    }
    body.appendChild(container);
    container.querySelectorAll('.pf-jsec-header').forEach(el => {
        el.addEventListener('click', () => el.parentElement.classList.toggle('collapsed'));
    });
}

function buildJsonSection(key, val) {
    return `<div class="pf-jsec">
        <div class="pf-jsec-header">
            <span class="pf-jsec-arrow">&#9660;</span>
            <span class="pf-jsec-key">${escapeHtml(key)}</span>
            <span class="pf-jsec-badge">${jsonTypeBadge(val)}</span>
        </div>
        <div class="pf-jsec-body">${jsonValueToHtml(val)}</div>
    </div>`;
}

function jsonTypeBadge(val) {
    if (val === null) return 'null';
    if (Array.isArray(val)) return val.length + ' items';
    if (typeof val === 'object') return Object.keys(val).length + ' keys';
    return typeof val;
}

function jsonValueToHtml(val) {
    if (val === null) return '<span class="pf-jval-null">null</span>';
    if (typeof val === 'boolean') return `<span class="pf-jval-bool">${val}</span>`;
    if (typeof val === 'number')  return `<span class="pf-jval-num">${val}</span>`;
    if (typeof val === 'string')  return `<div class="pf-jval-str">${escapeHtml(val.length > 500 ? val.substring(0,500)+'…' : val)}</div>`;
    if (Array.isArray(val)) {
        if (val.length === 0) return '<span class="pf-jval-empty">[ ]</span>';
        if (val.every(v => v !== null && typeof v === 'object' && !Array.isArray(v))) return jsonArrayAsTable(val);
        return `<div class="pf-jval-list">${val.map((item, i) =>
            `<div class="pf-jval-list-item"><span class="pf-jval-idx">${i}</span>${jsonValueToHtml(item)}</div>`
        ).join('')}</div>`;
    }
    return `<div class="pf-jval-obj">${Object.keys(val).map(k =>
        `<div class="pf-jval-row"><span class="pf-jval-key">${escapeHtml(k)}</span><span class="pf-jval-val">${jsonValueToHtml(val[k])}</span></div>`
    ).join('')}</div>`;
}

function jsonArrayAsTable(arr) {
    const allKeys = [];
    arr.forEach(obj => Object.keys(obj).forEach(k => { if (!allKeys.includes(k)) allKeys.push(k); }));
    if (allKeys.length === 0) return '<span class="pf-jval-empty">[ ]</span>';
    let html = '<div class="pf-jtable-wrap"><table class="pf-jtable"><thead><tr>';
    allKeys.forEach(k => { html += `<th>${escapeHtml(k)}</th>`; });
    html += '</tr></thead><tbody>';
    arr.forEach(obj => {
        html += '<tr>';
        allKeys.forEach(k => {
            const v = obj[k];
            let cell = (v === undefined || v === null) ? '<span class="pf-jval-null">—</span>'
                     : typeof v === 'object' ? escapeHtml(JSON.stringify(v))
                     : escapeHtml(String(v));
            html += `<td>${cell}</td>`;
        });
        html += '</tr>';
    });
    return html + '</tbody></table></div>';
}

async function previewFile(category, idx) {
    const file = getFileArray(category)[idx];
    if (!file) return;

    const overlay = document.getElementById('pfPreviewOverlay');
    const body    = document.getElementById('pfPreviewBody');
    document.getElementById('pfPreviewTitle').textContent = file.name;

    const previewOpts = { fileType: file.type, filePath: file.path };

    if (!isPreviewable(file.name)) {
        renderPreviewContent(body, file.name, '', previewOpts);
        overlay.classList.add('open');
        return;
    }

    let content = file.content;
    if (!content && file.path) {
        try {
            const resp = await fetch(`${serverUrl}/api/plans/${currentPlanId}/files/${file.path}`);
            if (!resp.ok) throw new Error(resp.statusText);
            const data = await resp.json();
            content = data.content;
        } catch (e) {
            alert(t('previewFailed') + e.message);
            return;
        }
    }
    if (!content) return;
    renderPreviewContent(body, file.name, content, previewOpts);
    overlay.classList.add('open');
}

function closePreview(event) {
    if (event && event.target !== event.currentTarget) return;
    const overlay = document.getElementById('pfPreviewOverlay');
    overlay.classList.remove('open');
    document.getElementById('pfPreviewBody').innerHTML = '';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closePreview(); });

// ---- Review summary ----
function buildReview() {
    const topic    = document.getElementById('pfTopic').value.trim()    || '—';
    const audience = document.getElementById('pfAudience').value.trim() || '—';
    const length   = document.getElementById('pfLength').value.trim()   || '—';
    const tName    = pfTemplate.length > 0 ? pfTemplate[0].name : t('templateNone');
    const cCount   = pfContent.length;
    const sCount   = pfStyle.length;

    document.getElementById('pfReviewContent').innerHTML = `
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewTopic')}</span><span class="pf-review-value">${escapeHtml(topic)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewAudience')}</span><span class="pf-review-value">${escapeHtml(audience)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewLength')}</span><span class="pf-review-value">${escapeHtml(length)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewTemplate')}</span><span class="pf-review-value">${escapeHtml(tName)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewContent')}</span><span class="pf-review-value">${cCount}${t('nFiles')}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewStyle')}</span><span class="pf-review-value">${sCount}${t('nFiles')}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewModel')}</span><span class="pf-review-value">${escapeHtml(selectedModel)}</span></div>
    `;
}
