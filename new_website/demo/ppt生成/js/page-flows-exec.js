/**
 * Page-Flows Execution — PPT Generation variant
 *
 * Payload:
 *   - HTML templates (user-uploaded .html) merged with style guides into [样式参考元数据]
 *   - [内容参考元数据] axes: ["内容参考"]
 *   - [样式参考元数据] axes: ["样式参考"]
 *   - Output display highlights the final .pptx with a prominent download card.
 */

async function launchRun() {
    const topic    = document.getElementById('pfTopic').value.trim();
    const audience = document.getElementById('pfAudience').value.trim();
    const length   = document.getElementById('pfLength').value.trim();
    const userId   = `gui_${Date.now()}`;
    const launchBtn = document.getElementById('pfLaunchBtn');

    launchBtn.disabled    = true;
    launchBtn.textContent = t('uploading');

    try {
        // ---- Upload files ----
        const uploads = [];

        // Content + template + style: text upload
        for (const f of [...pfContent, ...pfTemplate, ...pfStyle]) {
            if (!f.isDefault && f.content) {
                uploads.push(
                    fetch(`${serverUrl}/api/userbenches/${userId}/files/${f.path}`, {
                        method:  'PUT',
                        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                        body:    f.content
                    })
                );
            }
        }

        // If no content files provided, upload a placeholder so the plan always
        // receives a non-empty [内容参考元数据] axis.
        const PLACEHOLDER_PATH = 'provisions/inputs/content/无内容参考.txt';
        if (pfContent.length === 0) {
            uploads.push(
                fetch(`${serverUrl}/api/userbenches/${userId}/files/${PLACEHOLDER_PATH}`, {
                    method:  'PUT',
                    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                    body:    '用户未提供内容参考，请根据演示主题自由发挥。'
                })
            );
        }

        await Promise.all(uploads);

        // ---- Build ground_inputs ----
        const contentRefs = pfContent.length > 0
            ? pfContent.map(f => ({
                name: f.name.replace(/\.[^.]+$/, ''),
                path: f.path,
                type: f.type || 'content'
              }))
            : [{ name: '无内容参考', path: PLACEHOLDER_PATH, type: 'content' }];

        const templateRefs = pfTemplate.map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path,
            type: f.type || 'html_template'
        }));

        const styleRefs = pfStyle.map(f => ({
            name: f.name.replace(/\.[^.]+$/, ''),
            path: f.path,
            type: f.type || 'guide'
        }));

        const allStyleRefs = [...templateRefs, ...styleRefs];

        const payload = {
            plan_id:   currentPlanId,
            llm_model: selectedModel,
            user_id:   userId,
            ground_inputs: {
                '{演示主题}': { data: [[topic]],                    axes: ['_none_axis'] },
                '{目标受众}': { data: [[audience || '一般受众']],   axes: ['_none_axis'] },
                '{期望长度}': { data: [[length  || '6张幻灯片']],   axes: ['_none_axis'] },
                '[内容参考元数据]': { data: [contentRefs],   axes: ['内容参考'] },
                '[样式参考元数据]': { data: [allStyleRefs],  axes: ['样式参考'] },
            }
        };

        // Upload merged inputs.json snapshot to userbench
        await fetch(`${serverUrl}/api/userbenches/${userId}/files/inputs.json`, {
            method:  'PUT',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload.ground_inputs, null, 2)
        });

        launchBtn.textContent = t('starting');

        const resp = await fetch(`${serverUrl}/api/runs`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || t('launchFailed'));
        }

        const data  = await resp.json();
        const runId = data.run_id;

        goTo(6);
        currentRunId  = runId;
        currentUserId = userId;
        document.getElementById('pfRunStatus').textContent      = t('runStarted') + `${runId.substring(0, 8)}...`;
        document.getElementById('pfProgressFill').style.width   = '10%';
        document.getElementById('pfTimeline').innerHTML         = '';
        document.getElementById('pfFinalFiles').innerHTML       = '';
        document.getElementById('pfIntermediateFiles').innerHTML = '';
        pfTimelineMap = {};
        pfRestartMap  = {};

        startPfEventStream(runId, userId);

    } catch (e) {
        alert(t('launchFailed') + e.message);
        launchBtn.disabled    = false;
        launchBtn.textContent = t('launch');
    }
}

// ---- SSE event stream ----
function startPfEventStream(runId) {
    if (pfEvtSource) pfEvtSource.close();
    pfEvtSource = new EventSource(`${serverUrl}/api/runs/${runId}/stream`);

    pfEvtSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            pfHandleEvent(data.event || 'message', data);
        } catch {}
    };

    pfEvtSource.onerror = () => {
        pfEvtSource.close();
        setTimeout(() => pfPollStatus(runId), 2000);
    };
}

// ---- Plan-specific step name translation (cc407e98 / 生成ppt_v1) ----
const STEP_LABELS = {
    // Content reference loading
    '[内容参考]':                                                        '加载内容参考',
    '*. %>([内容参考元数据]) %<({加载的内容}) %:({当前内容元数据':       '处理每个内容参考',
    // Style reference loading
    '[样式参考]':                                                        '加载样式参考',
    '{加载的样式}':                                                      '加载样式文件',
    '*. %>([样式参考元数据]) %<({加载的样式}) %:({当前样式元数据':       '处理每个样式参考',
    // Aggregation
    '{所有内容参考}':                                                    '汇总内容参考',
    '{所有样式参考}':                                                    '汇总样式参考',
    // Analysis
    '{分析}':                                                            '分析内容',
    '{已保存的分析}':                                                    '保存分析结果',
    // Outline
    '{大纲}':                                                            '生成大纲',
    '{已保存的大纲}':                                                    '保存大纲',
    // Slide spec generation
    '[幻灯片规格]':                                                      '生成幻灯片规格',
    // Slide rendering loop
    '[所有已渲染的幻灯片]':                                              '成功生成所有已渲染的幻灯片',
    '*. %>([幻灯片规格]) %<({幻灯片渲染结果}) %:({当前幻灯片规格':       '处理每个幻灯片规格',
    // Per-slide steps
    '{幻灯片内容上下文}':                                                '准备内容上下文',
    '{幻灯片内容}':                                                      '生成幻灯片内容',
    '{已保存的幻灯片内容}':                                              '保存幻灯片内容',
    '{选定的html模板}':                                                  '选择 HTML 模板',
    '{html模板内容}':                                                    '加载 HTML 模板',
    '{html幻灯片}':                                                      '渲染 HTML 幻灯片',
    '{已保存的html幻灯片}':                                              '保存 HTML 幻灯片',
    '{选定的pptx布局}':                                                  '选择 PPTX 布局',
    '{pptx幻灯片规格}':                                                  '生成 PPTX 规格',
    '{已保存的pptx幻灯片规格}':                                          '保存 PPTX 规格',
    '{幻灯片渲染结果}':                                                  '完成幻灯片渲染',
    // Final assembly
    '{所有幻灯片集合}':                                                  '汇总所有幻灯片',
    '{html演示文稿}':                                                    '生成 HTML 演示文稿',
    '{已保存的html演示文稿}':                                            '保存 HTML 演示文稿',
    '{pptx演示文稿}':                                                    '生成 PPTX 演示文稿',
    '{已保存的pptx演示文稿}':                                            '保存 PPTX 演示文稿',
    '{所有报告输出}':                                                    '汇总输出文件',
    '{演示文稿包}':                                                      '打包演示文稿',
};

function translateStepName(raw) {
    if (!raw) return raw;
    if (STEP_LABELS[raw]) return STEP_LABELS[raw];
    // Prefix match — handles expressions that may be truncated on either end
    for (const key of Object.keys(STEP_LABELS)) {
        if (raw.startsWith(key) || key.startsWith(raw)) return STEP_LABELS[key];
    }
    return raw;
}

function pfHandleEvent(type, data) {
    if (type === 'inference:started') {
        const raw    = data.concept_name || data.flow_index || '…';
        const name   = translateStepName(raw) || raw.substring(0, 40);
        const idx    = data.flow_index || raw;
        const isLoop = (data.sequence_type || '').toLowerCase().includes('loop') ||
                       (data.sequence_type || '').toLowerCase().includes('iterate');
        if (isLoop) { pfLoop.current = idx; pfLoop.iteration = 1; }

        if (pfTimelineMap[idx]) {
            // Step already in timeline — restart or new loop iteration; never add a duplicate
            pfRestartMap[idx] = (pfRestartMap[idx] || 1) + 1;
            const meta = isLoop
                ? `${t('loopIter')} ${pfRestartMap[idx]}`
                : `#${pfRestartMap[idx]}`;
            updateTimelineItem(idx, 'retry', meta);
        } else {
            pfRestartMap[idx] = 1;
            addTimelineItem(idx, name, 'running', isLoop ? `${t('loopIter')} 1` : '');
        }
    }
    else if (type === 'inference:completed') {
        const idx = data.flow_index || '';
        const dur = (data.duration || 0).toFixed(1) + t('seconds');
        if (data.is_loop && pfLoop.current === idx) {
            updateTimelineItem(idx, 'done', `${data.total_iterations || pfLoop.iteration || 1} ${t('loopIter')} · ${dur}`);
            pfLoop.current = null; pfLoop.iteration = 0;
        } else {
            updateTimelineItem(idx, 'done', dur);
        }
        pfPollOutputFiles();
    }
    else if (type === 'inference:failed')  { updateTimelineItem(data.flow_index || '', 'failed',  data.error || data.status || ''); }
    else if (type === 'inference:skipped') {
        const idx = data.flow_index || '';
        if (!pfTimelineMap[idx]) addTimelineItem(idx, translateStepName(idx), 'skipped', '');
        else updateTimelineItem(idx, 'skipped', '');
    }
    else if (type === 'inference:pending' || type === 'loop:progress') {
        const idx  = data.flow_index || '';
        const iter = data.iteration || (pfLoop.iteration + 1);
        pfLoop.current = idx; pfLoop.iteration = iter;
        updateTimelineMeta(idx, `${t('loopIter')} ${iter}`);
    }
    else if (type === 'inference:restarted' || type === 'inference:retry') {
        const idx     = data.flow_index || '';
        const attempt = data.attempt || data.retry_count || '';
        const meta    = attempt ? `#${attempt}` : '';
        if (!pfTimelineMap[idx]) addTimelineItem(idx, translateStepName(idx), 'retry', meta);
        else updateTimelineItem(idx, 'retry', meta);
    }
    else if (type === 'inference:in_progress') {
        const idx = data.flow_index || '';
        if (!pfTimelineMap[idx]) addTimelineItem(idx, translateStepName(idx), 'running', '');
    }
    else if (type === 'inference:error') {
        updateTimelineItem(data.flow_index || '', 'failed', data.error || '');
    }
    else if (type === 'execution:progress') {
        pfLoop.completed = data.completed_count || data.completed || 0;
        pfLoop.total     = data.total_count     || data.total     || 0;
        pfUpdateProgress(pfLoop.completed, pfLoop.total);
    }
    else if (type === 'file:changed') { pfPollOutputFiles(); }
    else if (type === 'run:completed') {
        if (pfEvtSource) pfEvtSource.close();
        document.getElementById('pfProgressFill').style.width   = '100%';
        document.getElementById('pfRunStatus').textContent      = t('runCompleted');
        document.getElementById('pfRunSub').textContent         = t('runCompletedSub');
        pfPollOutputFiles();
        const toggle = document.getElementById('pfFilesToggle');
        if (!toggle.classList.contains('open')) toggle.classList.add('open');
    }
    else if (type === 'run:failed') {
        if (pfEvtSource) pfEvtSource.close();
        document.getElementById('pfRunStatus').textContent    = t('runFailed') + (data.error || 'Unknown');
        document.getElementById('pfProgressFill').style.width = '0%';
    }
}

// ---- Progress bar ----
function pfUpdateProgress(completed, total) {
    const pct  = total > 0 ? Math.min(Math.round(completed / total * 100), 100) : 0;
    document.getElementById('pfProgressFill').style.width = pct + '%';
    let text = `${completed} / ${total}${t('inferences')}`;
    if (pfLoop.current && pfLoop.iteration > 0) text += ` · ${t('loopIter')} ${pfLoop.iteration}`;
    document.getElementById('pfRunStatus').textContent = text;
}

// ---- Timeline ----
function addTimelineItem(id, name, status, meta) {
    const timeline = document.getElementById('pfTimeline');
    const icons    = { running: '&#9654;', done: '&#10003;', failed: '&#10007;', skipped: '&#8709;', retry: '&#8635;' };
    const div      = document.createElement('div');
    div.className  = `pf-tl-item ${status}`;
    div.dataset.id = id;
    div.innerHTML  = `
        <span class="pf-tl-icon">${icons[status] || '&#9654;'}</span>
        <span class="pf-tl-name">${escapeHtml(name)}</span>
        <span class="pf-tl-meta">${escapeHtml(meta)}</span>
    `;
    timeline.appendChild(div);
    timeline.scrollTop = timeline.scrollHeight;
    pfTimelineMap[id]  = div;
}

function updateTimelineItem(id, status, meta) {
    const div   = pfTimelineMap[id];
    if (!div) return;
    const icons = { running: '&#9654;', done: '&#10003;', failed: '&#10007;', skipped: '&#8709;', retry: '&#8635;' };
    div.className = `pf-tl-item ${status}`;
    div.querySelector('.pf-tl-icon').innerHTML = icons[status] || '';
    if (meta !== undefined) div.querySelector('.pf-tl-meta').textContent = meta;
}

function updateTimelineMeta(id, meta) {
    const div = pfTimelineMap[id];
    if (div) div.querySelector('.pf-tl-meta').textContent = meta;
}

// ---- File polling ----
let pfPollTimer = null;
async function pfPollOutputFiles() {
    if (!currentUserId) return;
    clearTimeout(pfPollTimer);
    pfPollTimer = setTimeout(async () => {
        try {
            const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files?category=productions&recursive=true`);
            if (!resp.ok) return;
            pfRenderFiles(await resp.json());
        } catch {}
    }, 500);
}

/**
 * Render output file cards.
 * .pptx final outputs get a large prominent download card.
 * All other finals and intermediates use the standard compact card.
 */
function pfRenderFiles(files) {
    const allFiles     = files.filter(f => !f.is_dir);
    const finals       = allFiles.filter(f =>  f.path.includes('output/'));
    const intermediates = allFiles.filter(f => !f.path.includes('output/'));

    const extIcons = { html: '&#127760;', pptx: '&#128202;', json: '&#128203;', pdf: '&#128196;', md: '&#128221;', txt: '&#128196;' };
    function icon(name) { return extIcons[name.split('.').pop().toLowerCase()] || '&#128196;'; }
    function size(bytes) { return bytes > 1024 ? (bytes / 1024).toFixed(1) + ' KB' : bytes + ' B'; }

    const finalEl = document.getElementById('pfFinalFiles');
    const interEl = document.getElementById('pfIntermediateFiles');

    if (finals.length > 0) {
        const pptxFinals  = finals.filter(f => /\.pptx$/i.test(f.name));
        const otherFinals = finals.filter(f => !/\.pptx$/i.test(f.name));

        let html = `<div class="pf-section-label">${t('finalOutputs')}</div>`;

        // Prominent PPTX download card
        pptxFinals.forEach(f => {
            html += `
            <div class="pf-pptx-card" onclick="pfDownload('${f.path}','${escapeHtml(f.name)}')">
                <span class="pf-pptx-icon">&#128202;</span>
                <div class="pf-pptx-info">
                    <div class="pf-pptx-name">${escapeHtml(f.name)}</div>
                    <div class="pf-pptx-size">${size(f.size || 0)}</div>
                </div>
                <button class="pf-pptx-dl" onclick="event.stopPropagation();pfDownload('${f.path}','${escapeHtml(f.name)}')" title="${t('download')}">
                    &#11015; ${t('download')}
                </button>
            </div>`;
        });

        // Standard cards for other finals
        otherFinals.forEach(f => {
            html += `
            <div class="pf-file-card final" onclick="pfPreviewOutput('${f.path}','${escapeHtml(f.name)}')">
                <span class="pf-fc-icon">${icon(f.name)}</span>
                <span class="pf-fc-name">${escapeHtml(f.name)}</span>
                <span class="pf-fc-size">${size(f.size || 0)}</span>
                <button class="pf-fc-btn" onclick="event.stopPropagation();pfDownload('${f.path}','${escapeHtml(f.name)}')" title="${t('download')}">&#11015;</button>
            </div>`;
        });

        finalEl.innerHTML = html;
    } else {
        finalEl.innerHTML = '';
    }

    if (intermediates.length > 0) {
        interEl.innerHTML = `<div class="pf-section-label">${t('intermediateFiles')}</div>` +
            intermediates.map(f => `
            <div class="pf-file-card" onclick="pfPreviewOutput('${f.path}','${escapeHtml(f.name)}')">
                <span class="pf-fc-icon">${icon(f.name)}</span>
                <span class="pf-fc-name">${escapeHtml(f.name)}</span>
                <span class="pf-fc-size">${size(f.size || 0)}</span>
            </div>`).join('');
    } else {
        interEl.innerHTML = '';
    }

    if (allFiles.length > 0) {
        const toggle = document.getElementById('pfFilesToggle');
        if (!toggle.classList.contains('open')) toggle.classList.add('open');
    }
}

// ---- Preview / download output files ----
async function pfPreviewOutput(path, name) {
    const overlay = document.getElementById('pfPreviewOverlay');
    const body    = document.getElementById('pfPreviewBody');
    document.getElementById('pfPreviewTitle').textContent = name;

    if (!isPreviewable(name)) {
        renderPreviewContent(body, name, '', { downloadUrl: path });
        overlay.classList.add('open');
        return;
    }

    try {
        const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files/${path}`);
        if (!resp.ok) throw new Error(resp.statusText);
        const ct      = resp.headers.get('content-type') || '';
        const content = ct.includes('application/json')
            ? (() => { return resp.json().then(d => typeof d.content === 'string' ? d.content : JSON.stringify(d, null, 2)); })()
            : resp.text();
        renderPreviewContent(body, name, await content, { downloadUrl: path });
        overlay.classList.add('open');
    } catch (e) {
        alert(t('previewFailed') + e.message);
    }
}

function pfDownload(path, name) {
    const a  = document.createElement('a');
    a.href   = `${serverUrl}/api/userbenches/${currentUserId}/files/${path}`;
    a.download = name;
    a.click();
}

// ---- Fallback poll ----
async function pfPollStatus(runId) {
    if (!runId) return;
    try {
        const resp = await fetch(`${serverUrl}/api/runs/${runId}`);
        const data = await resp.json();
        if (data.progress) pfUpdateProgress(data.progress.completed_count || 0, data.progress.total_count || 0);
        if (data.status === 'completed')     pfHandleEvent('run:completed', {});
        else if (data.status === 'failed')   pfHandleEvent('run:failed', { error: data.error });
        else if (data.status === 'running')  setTimeout(() => pfPollStatus(runId), 3000);
    } catch {
        setTimeout(() => pfPollStatus(runId), 5000);
    }
}
