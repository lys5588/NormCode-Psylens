/**
 * Page-Flows Files & Preview Module
 * File upload, management, preview modal, and rendering
 */

        function getFileArray(category) {
            if (category === 'content') return pfContent;
            if (category === 'template') return pfTemplate;
            return pfStyle;
        }

        function renderFileList(category) {
            const arr = getFileArray(category);
            const listId = category === 'content' ? 'pfContentList' : category === 'template' ? 'pfTemplateList' : 'pfStyleList';
            const el = document.getElementById(listId);
            if (arr.length === 0) { el.innerHTML = ''; return; }
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

        function removeFile(category, idx) {
            getFileArray(category).splice(idx, 1);
            renderFileList(category);
        }

        async function pfFiles(event, category) {
            const files = event.target.files;
            if (!files) return;
            const list = Array.from(files);
            event.target.value = '';
            await pfProcessFiles(list, category);
        }

        async function pfDrop(event, category) {
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            const files = event.dataTransfer.files;
            if (!files) return;
            await pfProcessFiles(Array.from(files), category);
        }

        function pfReadTextFile(file, category) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const catPath = category === 'template' ? 'templates' : category;
                getFileArray(category).push({
                    name: file.name,
                    path: `provisions/inputs/${catPath}/${file.name}`,
                    content: e.target.result,
                    isDefault: false
                });
                renderFileList(category);
            };
            reader.readAsText(file);
        }

        async function pfProcessFiles(files, category) {
            const textFiles = [];
            const convertibles = [];
            const legacy = [];

            files.forEach(file => {
                if (LEGACY_BINARY_EXTS.test(file.name)) {
                    legacy.push(file);
                } else if (isConvertible(file.name)) {
                    convertibles.push(file);
                } else {
                    textFiles.push(file);
                }
            });

            textFiles.forEach(f => pfReadTextFile(f, category));

            if (legacy.length > 0) {
                alert(t('legacyFormat'));
            }

            if (convertibles.length === 0) return;

            const proceed = await showConvertWarning(convertibles.map(f => f.name));
            if (!proceed) return;

            const dropId = category === 'content' ? 'pfContentDrop'
                         : category === 'template' ? 'pfTemplateDrop' : 'pfStyleDrop';
            const dropSpan = document.getElementById(dropId).querySelector('span');
            const origText = dropSpan.textContent;

            for (const file of convertibles) {
                dropSpan.textContent = t('converting') + ' ' + file.name + '…';
                try {
                    const text = await convertFileToText(file);
                    const txtName = file.name.replace(/\.[^.]+$/, '.txt');
                    const catPath = category === 'template' ? 'templates' : category;
                    getFileArray(category).push({
                        name: txtName,
                        path: `provisions/inputs/${catPath}/${txtName}`,
                        content: text,
                        isDefault: false,
                        convertedFrom: file.name
                    });
                    renderFileList(category);
                } catch (e) {
                    alert(t('convertFailed') + file.name + ': ' + e.message);
                }
            }

            dropSpan.textContent = origText;
        }

        function pfDragOver(event) {
            event.preventDefault();
            event.currentTarget.classList.add('dragover');
        }

        function pfDragLeave(event) {
            event.currentTarget.classList.remove('dragover');
        }

        // ---- File preview helpers ----
        const BINARY_EXTS = /\.(pptx|xlsx|docx|pdf|zip|tar|gz|7z|rar|png|jpg|jpeg|gif|bmp|webp|svg|ico|mp3|mp4|wav|avi|mov|woff2?|ttf|eot|exe|dll|so|bin|dat)$/i;

        // ---- Markdown → HTML renderer (lightweight, no dependencies) ----
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
    h1, h2, h3 { color: #0550ae; margin-top: 1.5em; }
    h1 { font-size: 1.8em; border-bottom: 2px solid #0550ae; padding-bottom: 0.3em; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; }
    pre { background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }
    pre code { background: none; padding: 0; }
    ul, ol { padding-left: 24px; }
    li { margin: 8px 0; }
    strong { color: #0550ae; }
    hr { border: none; border-top: 1px solid #e1e8ed; margin: 24px 0; }
    p { margin: 12px 0; }
</style>
</head><body><p>${html}</p></body></html>`;
        }

        // ---- Template placeholder replacement for HTML preview ----
        function replaceTemplatePlaceholders(content) {
            const sampleData = {
                'title': 'Sample Title', 'presentation_title': 'Presentation Title',
                'subtitle': 'Subtitle text', 'presenter': 'Presenter Name',
                'date': new Date().toLocaleDateString(), 'slide_number': '1',
                'visual_description': '[Visual / Chart area]', 'caption': 'Image caption',
                'speaker_notes': 'Speaker notes go here...',
                'content': '• Point one\n• Point two\n• Point three',
                'bullet_points': '• First point\n• Second point\n• Third point',
                'key_message': 'Key message content', 'quote': '"A sample quote"',
                'author': 'Author Name'
            };
            return content.replace(/\{\{(\w+)\}\}/g, (match, key) => {
                return sampleData[key.toLowerCase()] || `[${key}]`;
            });
        }
        const TEXT_EXTS = /\.(txt|md|css|js|ts|py|yaml|yml|toml|ini|cfg|sh|bat|xml|csv|log|sql|rs|go|java|c|cpp|h|hpp|rb|php|pl|swift|kt)$/i;

        function isPreviewable(name) {
            if (BINARY_EXTS.test(name)) return false;
            return true;
        }

        /**
         * Detect render mode from filename, path, and file type.
         * Returns 'html' | 'markdown' | 'json' | 'text'.
         */
        function detectRenderMode(name, opts) {
            if (opts && opts.renderAs) return opts.renderAs;
            if (/\.html?$/i.test(name)) return 'html';
            if (opts && opts.filePath && /\.html?$/i.test(opts.filePath)) return 'html';
            if (opts && opts.fileType === 'html_template') return 'html';
            if (/\.md$/i.test(name)) return 'markdown';
            if (opts && opts.filePath && /\.md$/i.test(opts.filePath)) return 'markdown';
            if (opts && opts.fileType === 'content') return 'markdown';
            if (/\.json$/i.test(name)) return 'json';
            if (opts && opts.filePath && /\.json$/i.test(opts.filePath)) return 'json';
            return 'text';
        }

        /**
         * Render content into the preview modal body.
         * Handles: binary, HTML (rendered iframe), Markdown (rendered), JSON (tree), plain text.
         * opts.renderAs / opts.fileType / opts.filePath used to detect render mode
         * when the filename alone lacks an extension.
         */
        function renderPreviewContent(body, name, content, opts) {
            body.innerHTML = '';
            const toggleBtn = document.getElementById('pfPreviewToggle');

            if (!isPreviewable(name) && !(opts && (opts.renderAs || opts.fileType))) {
                const ext = name.split('.').pop().toUpperCase();
                const div = document.createElement('div');
                div.className = 'pf-preview-placeholder';
                div.innerHTML = `
                    <div class="pf-ph-icon">&#128196;</div>
                    <div class="pf-ph-name">${escapeHtml(name)}</div>
                    <div>${ext} file — preview not available</div>
                    ${opts && opts.downloadUrl ? `<button class="pf-preview-dl" onclick="pfDownload('${opts.downloadUrl}','${escapeHtml(name)}')">${t('download')}</button>` : ''}
                `;
                body.appendChild(div);
                toggleBtn.style.display = 'none';
                return;
            }

            const mode = detectRenderMode(name, opts);
            const hasToggle = mode === 'html' || mode === 'markdown' || mode === 'json';

            _previewState = { name, content, rendered: hasToggle, mode };

            if (hasToggle) {
                toggleBtn.style.display = '';
                toggleBtn.textContent = t('source');
                toggleBtn.classList.remove('active');
            } else {
                toggleBtn.style.display = 'none';
            }

            if (mode === 'html' || mode === 'markdown') {
                renderRenderedView(body, content, mode);
            } else if (mode === 'json') {
                renderJsonPreview(body, content);
            } else {
                const pre = document.createElement('pre');
                pre.textContent = content;
                body.appendChild(pre);
            }
        }

        /** Render HTML or Markdown in an iframe, with scale-to-fit for HTML */
        function renderRenderedView(body, content, mode) {
            body.innerHTML = '';
            const modal = body.closest('.pf-modal');
            if (modal) modal.classList.add('pf-modal-wide');

            const rendered = mode === 'html'
                ? replaceTemplatePlaceholders(content)
                : renderMarkdownToHtml(content);

            if (mode === 'html') {
                const wrapper = document.createElement('div');
                wrapper.className = 'pf-preview-scaled';
                body.appendChild(wrapper);

                const iframe = document.createElement('iframe');
                iframe.sandbox = 'allow-same-origin allow-scripts';
                iframe.style.cssText = 'position:absolute;border:none;width:100%;height:100%;transform-origin:top left';
                wrapper.appendChild(iframe);

                iframe.contentDocument.open();
                iframe.contentDocument.write(rendered);
                iframe.contentDocument.close();

                requestAnimationFrame(() => requestAnimationFrame(() => {
                    const doc = iframe.contentDocument;
                    if (!doc || !doc.body) return;

                    const fw = iframe.clientWidth;
                    const fh = iframe.clientHeight;
                    const cw = doc.documentElement.scrollWidth;
                    const ch = doc.documentElement.scrollHeight;

                    if (cw > fw || ch > fh) {
                        iframe.style.width = cw + 'px';
                        iframe.style.height = ch + 'px';
                        const scale = Math.min(fw / cw, fh / ch);
                        iframe.style.transform = 'scale(' + scale + ')';
                        iframe.style.left = Math.max(0, (fw - cw * scale) / 2) + 'px';
                        iframe.style.top = Math.max(0, (fh - ch * scale) / 2) + 'px';
                    }
                }));
            } else {
                const iframe = document.createElement('iframe');
                iframe.sandbox = 'allow-same-origin allow-scripts';
                body.appendChild(iframe);
                iframe.contentDocument.open();
                iframe.contentDocument.write(rendered);
                iframe.contentDocument.close();
            }
        }

        /** Render raw source in a <pre> block */
        function renderSourceView(body, content) {
            body.innerHTML = '';
            const pre = document.createElement('pre');
            pre.textContent = content;
            body.appendChild(pre);
        }

        /** Toggle between rendered view and source view */
        function togglePreviewMode() {
            const body = document.getElementById('pfPreviewBody');
            const toggleBtn = document.getElementById('pfPreviewToggle');
            const { content, rendered, mode } = _previewState;

            if (rendered) {
                renderSourceView(body, content);
                toggleBtn.textContent = t('rendered');
                toggleBtn.classList.add('active');
                _previewState.rendered = false;
            } else {
                if (mode === 'json') {
                    renderJsonPreview(body, content);
                } else {
                    renderRenderedView(body, content, mode);
                }
                toggleBtn.textContent = t('source');
                toggleBtn.classList.remove('active');
                _previewState.rendered = true;
            }
        }

        /** Render JSON as visual section boxes */
        function renderJsonPreview(body, content) {
            let parsed;
            try {
                parsed = JSON.parse(content);
            } catch (e) {
                const pre = document.createElement('pre');
                pre.textContent = content;
                body.appendChild(pre);
                return;
            }

            const container = document.createElement('div');
            container.className = 'pf-json-sections';

            if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
                Object.keys(parsed).forEach(key => {
                    container.innerHTML += buildJsonSection(key, parsed[key]);
                });
            } else {
                container.innerHTML = buildJsonSection('root', parsed);
            }
            body.appendChild(container);

            container.querySelectorAll('.pf-jsec-header').forEach(el => {
                el.addEventListener('click', () => el.parentElement.classList.toggle('collapsed'));
            });
        }

        /** Build a section box for a JSON key-value pair */
        function buildJsonSection(key, val) {
            const header = `<div class="pf-jsec-header">
                <span class="pf-jsec-arrow">&#9660;</span>
                <span class="pf-jsec-key">${escapeHtml(key)}</span>
                <span class="pf-jsec-badge">${jsonTypeBadge(val)}</span>
            </div>`;
            const body = `<div class="pf-jsec-body">${jsonValueToHtml(val)}</div>`;
            return `<div class="pf-jsec">${header}${body}</div>`;
        }

        function jsonTypeBadge(val) {
            if (val === null) return 'null';
            if (Array.isArray(val)) return val.length + ' items';
            if (typeof val === 'object') return Object.keys(val).length + ' keys';
            return typeof val;
        }

        /** Render a JSON value as readable HTML for inside a section box */
        function jsonValueToHtml(val) {
            if (val === null) return '<span class="pf-jval-null">null</span>';
            if (typeof val === 'boolean') return `<span class="pf-jval-bool">${val}</span>`;
            if (typeof val === 'number') return `<span class="pf-jval-num">${val}</span>`;
            if (typeof val === 'string') {
                if (val.length > 500) {
                    return `<div class="pf-jval-str">${escapeHtml(val.substring(0, 500))}…</div>`;
                }
                return `<div class="pf-jval-str">${escapeHtml(val)}</div>`;
            }

            if (Array.isArray(val)) {
                if (val.length === 0) return '<span class="pf-jval-empty">[ ]</span>';
                if (val.every(v => v !== null && typeof v === 'object' && !Array.isArray(v))) {
                    return jsonArrayAsTable(val);
                }
                return `<div class="pf-jval-list">${val.map((item, i) =>
                    `<div class="pf-jval-list-item"><span class="pf-jval-idx">${i}</span>${jsonValueToHtml(item)}</div>`
                ).join('')}</div>`;
            }

            if (typeof val === 'object') {
                return `<div class="pf-jval-obj">${Object.keys(val).map(k =>
                    `<div class="pf-jval-row">
                        <span class="pf-jval-key">${escapeHtml(k)}</span>
                        <span class="pf-jval-val">${jsonValueToHtml(val[k])}</span>
                    </div>`
                ).join('')}</div>`;
            }
            return escapeHtml(String(val));
        }

        /** Render an array of objects as a compact table */
        function jsonArrayAsTable(arr) {
            const allKeys = [];
            arr.forEach(obj => {
                Object.keys(obj).forEach(k => { if (!allKeys.includes(k)) allKeys.push(k); });
            });
            if (allKeys.length === 0) return '<span class="pf-jval-empty">[ ]</span>';

            let html = '<div class="pf-jtable-wrap"><table class="pf-jtable"><thead><tr>';
            allKeys.forEach(k => { html += `<th>${escapeHtml(k)}</th>`; });
            html += '</tr></thead><tbody>';
            arr.forEach(obj => {
                html += '<tr>';
                allKeys.forEach(k => {
                    const v = obj[k];
                    let cell = '';
                    if (v === undefined || v === null) cell = '<span class="pf-jval-null">—</span>';
                    else if (typeof v === 'object') cell = escapeHtml(JSON.stringify(v));
                    else cell = escapeHtml(String(v));
                    html += `<td>${cell}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            return html;
        }

        // ---- File preview (in-page modal) ----
        async function previewFile(category, idx) {
            const file = getFileArray(category)[idx];
            if (!file) return;

            const overlay = document.getElementById('pfPreviewOverlay');
            const body = document.getElementById('pfPreviewBody');
            document.getElementById('pfPreviewTitle').textContent = file.name;

            const previewOpts = { fileType: file.type, filePath: file.path };

            if (!isPreviewable(file.name) && !file.type) {
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
            const modal = overlay.querySelector('.pf-modal');
            if (modal) modal.classList.remove('pf-modal-wide');
            document.getElementById('pfPreviewBody').innerHTML = '';
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closePreview();
        });

        // ---- Step 3: Review ----
        function buildReview() {
            const topic = document.getElementById('pfTopic').value.trim() || '—';
            const audience = document.getElementById('pfAudience').value.trim() || '—';
            const length = document.getElementById('pfLength').value.trim() || '—';
            const cCount = pfContent.length;
            const tCount = pfTemplate.length;
            const sCount = pfStyle.length;

            document.getElementById('pfReviewContent').innerHTML = `
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewTopic')}</span><span class="pf-review-value">${escapeHtml(topic)}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewAudience')}</span><span class="pf-review-value">${escapeHtml(audience)}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewLength')}</span><span class="pf-review-value">${escapeHtml(length)}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewContent')}</span><span class="pf-review-value">${cCount}${t('nFiles')}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewTemplate')}</span><span class="pf-review-value">${tCount}${t('nFiles')}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewStyle')}</span><span class="pf-review-value">${sCount}${t('nFiles')}</span></div>
                <div class="pf-review-item"><span class="pf-review-label">${t('reviewModel')}</span><span class="pf-review-value">${escapeHtml(selectedModel)}</span></div>
            `;
        }

