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
            el.innerHTML = arr.map((f, i) => `
                <div class="pf-file-item">
                    <span>${f.isDefault ? '📌 ' : ''}${f.name}</span>
                    <div class="pf-file-actions">
                        <button class="pf-file-preview" onclick="previewFile('${category}',${i})" title="${t('preview')}">&#128065;</button>
                        <button class="pf-file-remove" onclick="removeFile('${category}',${i})">&times;</button>
                    </div>
                </div>
            `).join('');
        }

        function removeFile(category, idx) {
            getFileArray(category).splice(idx, 1);
            renderFileList(category);
        }

        function pfFiles(event, category) {
            const files = event.target.files;
            if (!files) return;
            Array.from(files).forEach(file => {
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
            });
            event.target.value = '';
        }

        function pfDrop(event, category) {
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            const files = event.dataTransfer.files;
            if (!files) return;
            Array.from(files).forEach(file => {
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
            });
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
         * Render content into the preview modal body.
         * Handles: binary, HTML (rendered iframe), Markdown (rendered), JSON (tree), plain text.
         * For HTML and Markdown, defaults to rendered view with a toggle to source.
         */
        function renderPreviewContent(body, name, content, opts) {
            body.innerHTML = '';
            const toggleBtn = document.getElementById('pfPreviewToggle');

            // Binary / non-previewable
            if (!isPreviewable(name)) {
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

            const isHtml = /\.html?$/i.test(name);
            const isMd = /\.md$/i.test(name);
            const isJson = /\.json$/i.test(name);
            const hasRenderedView = isHtml || isMd;

            // Store state for toggle
            _previewState = { name, content, rendered: hasRenderedView };

            // Show/hide toggle button
            if (hasRenderedView) {
                toggleBtn.style.display = '';
                toggleBtn.textContent = t('source');
                toggleBtn.classList.remove('active');
            } else {
                toggleBtn.style.display = 'none';
            }

            if (hasRenderedView) {
                // Rendered view by default
                renderRenderedView(body, name, content);
            } else if (isJson) {
                renderJsonPreview(body, content);
            } else {
                const pre = document.createElement('pre');
                pre.textContent = content;
                body.appendChild(pre);
            }
        }

        /** Render HTML or Markdown in an iframe */
        function renderRenderedView(body, name, content) {
            body.innerHTML = '';
            const isHtml = /\.html?$/i.test(name);
            const iframe = document.createElement('iframe');
            iframe.sandbox = 'allow-same-origin';
            body.appendChild(iframe);

            let rendered;
            if (isHtml) {
                rendered = replaceTemplatePlaceholders(content);
            } else {
                // Markdown
                rendered = renderMarkdownToHtml(content);
            }

            iframe.contentDocument.open();
            iframe.contentDocument.write(rendered);
            iframe.contentDocument.close();
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
            const { name, content, rendered } = _previewState;

            if (rendered) {
                // Switch to source
                renderSourceView(body, content);
                toggleBtn.textContent = t('rendered');
                toggleBtn.classList.add('active');
                _previewState.rendered = false;
            } else {
                // Switch to rendered
                renderRenderedView(body, name, content);
                toggleBtn.textContent = t('source');
                toggleBtn.classList.remove('active');
                _previewState.rendered = true;
            }
        }

        /** Parse JSON string and render a collapsible tree view */
        function renderJsonPreview(body, content) {
            let parsed;
            try {
                parsed = JSON.parse(content);
            } catch (e) {
                // Not valid JSON — fall back to plain text
                const pre = document.createElement('pre');
                pre.textContent = content;
                body.appendChild(pre);
                return;
            }

            const container = document.createElement('div');
            container.className = 'pf-json-tree';
            container.innerHTML = jsonToHtml(parsed, '');
            body.appendChild(container);

            // Attach collapse/expand handlers
            container.querySelectorAll('.jl').forEach(el => {
                el.addEventListener('click', () => el.classList.toggle('collapsed'));
            });
        }

        /** Recursively build HTML for a JSON value */
        function jsonToHtml(val, indent) {
            if (val === null) return '<span class="jb">null</span>';
            if (typeof val === 'boolean') return `<span class="jb">${val}</span>`;
            if (typeof val === 'number') return `<span class="jn">${val}</span>`;
            if (typeof val === 'string') {
                const escaped = escapeHtml(val);
                // Long strings: show truncated with linebreaks preserved
                if (val.length > 300) {
                    return `<span class="js">"${escaped.substring(0, 300)}…"</span>`;
                }
                return `<span class="js">"${escaped}"</span>`;
            }

            if (Array.isArray(val)) {
                if (val.length === 0) return '<span class="jend">[]</span>';
                // Small arrays of primitives: inline
                if (val.length <= 3 && val.every(v => v === null || typeof v !== 'object')) {
                    const items = val.map(v => jsonToHtml(v, '')).join(', ');
                    return `[${items}]`;
                }
                const count = val.length;
                let html = `<span class="jl">[<span class="jcollapsed"> ${count} items… ]</span></span>`;
                html += '<div class="jc">';
                val.forEach((item, i) => {
                    const comma = i < val.length - 1 ? ',' : '';
                    html += `<div>${jsonToHtml(item, indent)}${comma}</div>`;
                });
                html += '</div>';
                html += '<div class="jend">]</div>';
                return html;
            }

            if (typeof val === 'object') {
                const keys = Object.keys(val);
                if (keys.length === 0) return '<span class="jend">{}</span>';
                const count = keys.length;
                let html = `<span class="jl">{<span class="jcollapsed"> ${count} keys… }</span></span>`;
                html += '<div class="jc">';
                keys.forEach((key, i) => {
                    const comma = i < keys.length - 1 ? ',' : '';
                    html += `<div><span class="jk">"${escapeHtml(key)}"</span>: ${jsonToHtml(val[key], indent)}${comma}</div>`;
                });
                html += '</div>';
                html += '<div class="jend">}</div>';
                return html;
            }

            return escapeHtml(String(val));
        }

        // ---- File preview (in-page modal) ----
        async function previewFile(category, idx) {
            const file = getFileArray(category)[idx];
            if (!file) return;

            const overlay = document.getElementById('pfPreviewOverlay');
            const body = document.getElementById('pfPreviewBody');
            document.getElementById('pfPreviewTitle').textContent = file.name;

            // Binary file — show placeholder immediately (no fetch needed)
            if (!isPreviewable(file.name)) {
                renderPreviewContent(body, file.name, '');
                overlay.classList.add('open');
                return;
            }

            let content = file.content;

            // For default/server files without local content, fetch from server
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
            renderPreviewContent(body, file.name, content);
            overlay.classList.add('open');
        }

        function closePreview(event) {
            if (event && event.target !== event.currentTarget) return;
            const overlay = document.getElementById('pfPreviewOverlay');
            overlay.classList.remove('open');
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

