/**
 * Page-Flows Files — PPT Generation variant
 *
 * Content / Template (.html) / Style categories.
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
    // ---- CONTENT / STYLE: text + conversion pipeline ----
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
            const catPath = category === 'template' ? 'templates' : category === 'style' ? 'style' : 'content';
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
        const catPath = category === 'template' ? 'templates' : category === 'style' ? 'style' : 'content';
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
    if (opts?.renderAs)                                      return opts.renderAs;
    if (/\.html?$/i.test(name))                              return 'html';
    if (opts?.filePath && /\.html?$/i.test(opts.filePath))   return 'html';
    if (opts?.fileType === 'html_template')                  return 'html';
    if (/\.md$/i.test(name))                                 return 'markdown';
    if (opts?.filePath && /\.md$/i.test(opts.filePath))      return 'markdown';
    if (/\.json$/i.test(name))                               return 'json';
    if (opts?.filePath && /\.json$/i.test(opts.filePath))    return 'json';
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
    const openBtn   = document.getElementById('pfPreviewOpenBtn');

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
        if (openBtn) openBtn.style.display = 'none';
        return;
    }

    const mode      = detectRenderMode(name, opts);
    const hasToggle = mode === 'html' || mode === 'markdown' || mode === 'json';
    _previewState   = { name, content, rendered: hasToggle, mode };

    if (openBtn) openBtn.style.display = (mode === 'html' || mode === 'markdown') ? '' : 'none';

    if (hasToggle) {
        toggleBtn.style.display = '';
        toggleBtn.textContent   = t('source');
        toggleBtn.classList.remove('active');
    } else {
        toggleBtn.style.display = 'none';
    }

    if (mode === 'html' || mode === 'markdown') {
        renderRenderedView(body, content, mode);
    } else if (mode === 'json') {
        const modal = body.closest('.pf-modal');
        if (modal) modal.classList.remove('pf-modal-wide');
        renderJsonPreview(body, content);
    } else {
        const modal = body.closest('.pf-modal');
        if (modal) modal.classList.remove('pf-modal-wide');
        const pre = document.createElement('pre');
        pre.textContent = content;
        body.appendChild(pre);
    }
}

/** Render HTML or Markdown in a sandboxed iframe. HTML gets scale-to-fit. */
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
                iframe.style.width  = cw + 'px';
                iframe.style.height = ch + 'px';
                const scale = Math.min(fw / cw, fh / ch);
                iframe.style.transform = 'scale(' + scale + ')';
                iframe.style.left = Math.max(0, (fw - cw * scale) / 2) + 'px';
                iframe.style.top  = Math.max(0, (fh - ch * scale) / 2) + 'px';
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
        else renderRenderedView(body, content, mode);
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
    const modal = overlay.querySelector('.pf-modal');
    if (modal) modal.classList.remove('pf-modal-wide');
}

// ---- Open rendered HTML/Markdown in a new popup window ----
function pfOpenInWindow() {
    const { name, content } = _previewState;
    openRenderedHtmlWindow(content, name);
}

function openRenderedHtmlWindow(content, filePath) {
    const isHtml = /\.html?$/i.test(filePath);
    const isMd   = /\.md$/i.test(filePath);
    let previewContent;
    if (isHtml) {
        previewContent = replaceTemplatePlaceholders(content);
    } else if (isMd) {
        previewContent = renderMarkdownToHtml(content);
    } else {
        previewContent = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:monospace;padding:20px;white-space:pre-wrap;}</style></head><body>${escapeHtml(content)}</body></html>`;
    }
    const blob     = new Blob([previewContent], { type: 'text/html' });
    const url      = URL.createObjectURL(blob);
    const fileName = filePath.split('/').pop() || 'preview.html';
    const width = 1100, height = 700;
    const left  = Math.round((screen.width  - width)  / 2);
    const top   = Math.round((screen.height - height) / 2);
    const win   = window.open(url, `preview_${Date.now()}`,
        `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no`);
    if (win) {
        win.document.title = `预览: ${fileName}`;
        win.onload = () => URL.revokeObjectURL(url);
    } else {
        alert('无法打开新窗口，请检查浏览器是否阻止了弹出窗口');
        URL.revokeObjectURL(url);
    }
}

// ---- Replace {{placeholder}} tokens in HTML templates for preview ----
function replaceTemplatePlaceholders(content) {
    const sampleData = {
        title:                '示例标题 - Sample Title',
        presentation_title:   '演示文稿标题',
        subtitle:             '副标题内容',
        presenter:            '演讲者姓名',
        date:                 new Date().toLocaleDateString('zh-CN'),
        slide_number:         '1',
        visual_description:   '[图表/图像描述区域]',
        caption:              '图片说明文字',
        speaker_notes:        '演讲者备注：这里是演讲提示内容...',
        content:              '• 要点一\n• 要点二\n• 要点三',
        bullet_points:        '• 第一点内容\n• 第二点内容\n• 第三点内容',
        bullets:              '<li>关键发现与分析</li><li>策略建议与方案</li><li>下一步实施计划</li>',
        key_message:          '核心信息内容',
        intro_text:           '以下是本次讨论的核心要点总结：',
        quote:                '"数据驱动决策是现代企业的核心竞争力。"',
        author:               '张明远',
        author_role:          '首席数据官',
        badge:                '核心',
        side_panel_title:     '关键指标',
        footnote:             '数据来源：2026年度报告',
        section_number:       '02',
        contact_email:        'contact@example.com',
        contact_link:         'www.example.com',
        outcome:              '实现30%效率提升',
        call_to_action:       '立即开始数字化转型 →',
        diagram_label:        '系统架构图',
        chart_title:          '季度营收趋势',
        insights_title:       '关键洞察',
        insights:             '<li>同比增长 23%</li><li>用户留存率提升</li><li>成本降低 15%</li>',
        takeaways:            '<li>1. 营收同比增长 23%</li><li>2. 用户满意度达 96%</li><li>3. 市场份额扩大 5%</li>',
        table_rows:           '<tr><td>Q1</td><td>¥2.4M</td><td>+18%</td><td>1,240</td><td>92%</td></tr><tr><td>Q2</td><td>¥3.1M</td><td>+29%</td><td>1,580</td><td>95%</td></tr><tr><td>Q3</td><td>¥2.8M</td><td>+12%</td><td>1,420</td><td>94%</td></tr>',
        highlight_1_value: '42%', highlight_1_label: '增长率',
        highlight_2_value: '1.2M', highlight_2_label: '用户数',
        highlight_3_value: '99.9%', highlight_3_label: '可用性',
        metric_1_value: '¥2,847', metric_1_label: '营收(万)', metric_1_trend: '+12%',
        metric_2_value: '1,580', metric_2_label: '新客户', metric_2_trend: '+29%',
        metric_3_value: '96%', metric_3_label: '满意度', metric_3_trend: '+3%',
        metric_4_value: '45ms', metric_4_label: '响应时间', metric_4_trend: '-18%',
        bar_1_value: '78%', bar_1_label: 'Q1',
        bar_2_value: '85%', bar_2_label: 'Q2',
        bar_3_value: '92%', bar_3_label: 'Q3',
        bar_4_value: '88%', bar_4_label: 'Q4',
        bar_5_value: '95%', bar_5_label: '目标',
        left_icon: '📊', left_header: '方案 A', left_metric_value: '¥1.2M', left_metric_label: '预算',
        left_bullets: '<li>快速部署</li><li>低风险</li><li>3个月周期</li>',
        right_icon: '🚀', right_header: '方案 B', right_metric_value: '¥2.5M', right_metric_label: '预算',
        right_bullets: '<li>全面升级</li><li>长期收益</li><li>6个月周期</li>',
        annotation_1_value: '42%', annotation_1_text: '效率提升',
        annotation_2_value: '3x', annotation_2_text: '吞吐量',
        annotation_3_value: '99.9%', annotation_3_text: '系统可用性',
        milestone_1_date: '2025 Q1', milestone_1_title: '项目启动', milestone_1_desc: '需求分析与团队组建',
        milestone_2_date: '2025 Q2', milestone_2_title: '原型开发', milestone_2_desc: '核心功能开发完成',
        milestone_3_date: '2025 Q3', milestone_3_title: '测试上线', milestone_3_desc: '内测与优化迭代',
        milestone_4_date: '2025 Q4', milestone_4_title: '全面推广', milestone_4_desc: '市场推广与用户增长',
        milestone_5_date: '2026 Q1', milestone_5_title: '持续优化', milestone_5_desc: '数据驱动持续改进',
        step_1_title: '数据采集', step_1_desc: '多渠道数据整合',
        step_2_title: '分析建模', step_2_desc: 'AI驱动深度分析',
        step_3_title: '策略制定', step_3_desc: '基于洞察的决策',
        step_4_title: '执行优化', step_4_desc: '持续迭代改进',
        stat_1_value: '2.4M', stat_1_label: '月活用户', stat_1_detail: '同比+35%',
        stat_2_value: '99.9%', stat_2_label: '系统可用性', stat_2_detail: 'SLA达标',
        stat_3_value: '45ms', stat_3_label: '平均响应', stat_3_detail: 'P99<100ms',
        stat_4_value: '¥8.2M', stat_4_label: '季度营收', stat_4_detail: '超目标12%',
        stat_5_value: '96%', stat_5_label: '客户满意度', stat_5_detail: 'NPS 72',
        stat_6_value: '340+', stat_6_label: '企业客户', stat_6_detail: '新增58家',
        quote_stat_1_value: '73%', quote_stat_1_label: '效率提升',
        quote_stat_2_value: '2.1x', quote_stat_2_label: '投资回报',
        quote_stat_3_value: '96%', quote_stat_3_label: '推荐率',
        summary_metric_1_value: '+23%', summary_metric_1_label: '营收增长',
        summary_metric_2_value: '1.2M', summary_metric_2_label: '用户规模',
        summary_metric_3_value: '96%', summary_metric_3_label: '满意度',
        col_1_header: '季度', col_2_header: '营收', col_3_header: '增长', col_4_header: '客户数', col_5_header: '满意度',
        center_concept: '数字化转型',
        spoke_1_title: '数据驱动', spoke_1_desc: '建立统一数据平台，实现决策智能化',
        spoke_2_title: '流程优化', spoke_2_desc: '端到端自动化，减少人工干预',
        spoke_3_title: '客户体验', spoke_3_desc: '全渠道触达，提升满意度',
        spoke_4_title: '组织升级', spoke_4_desc: '敏捷协作，赋能创新文化',
        flow_1_title: '需求分析', flow_1_desc: '深入调研用户痛点与业务目标',
        flow_2_title: '方案设计', flow_2_desc: '制定技术架构与实施路线图',
        flow_3_title: '开发交付', flow_3_desc: '迭代开发并持续集成测试',
        flow_4_title: '运营优化', flow_4_desc: '数据监控与持续改进闭环',
        flow_outcome: '实现端到端数字化闭环，关键指标提升30%以上',
        root_title: '企业战略', root_desc: '公司愿景与核心目标',
        branch_1_title: '产品线', branch_1_desc: '核心产品与创新业务',
        branch_2_title: '运营体系', branch_2_desc: '供应链与客户服务',
        branch_3_title: '技术平台', branch_3_desc: '基础设施与数据能力',
        leaf_1a: '旗舰产品', leaf_1b: '新兴业务',
        leaf_2a: '供应链', leaf_2b: '客户服务',
        leaf_3a: '云平台', leaf_3b: '数据中台',
    };
    return content.replace(/\{\{(\w+)\}\}/g, (_, key) => sampleData[key.toLowerCase()] || `[${key}]`);
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closePreview(); });

// ---- Review summary ----
function buildReview() {
    const topic    = document.getElementById('pfTopic').value.trim()    || '—';
    const audience = document.getElementById('pfAudience').value.trim() || '—';
    const length   = document.getElementById('pfLength').value.trim()   || '—';
    const cCount   = pfContent.length;
    const tCount   = pfTemplate.length;

    document.getElementById('pfReviewContent').innerHTML = `
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewTopic')}</span><span class="pf-review-value">${escapeHtml(topic)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewAudience')}</span><span class="pf-review-value">${escapeHtml(audience)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewLength')}</span><span class="pf-review-value">${escapeHtml(length)}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewContent')}</span><span class="pf-review-value">${cCount}${t('nFiles')}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewTemplate')}</span><span class="pf-review-value">${tCount}${t('nFiles')}</span></div>
        <div class="pf-review-item"><span class="pf-review-label">${t('reviewModel')}</span><span class="pf-review-value">${escapeHtml(selectedModel)}</span></div>
    `;
}
