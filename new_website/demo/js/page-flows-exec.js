/**
 * Page-Flows Execution Module
 * Launch, SSE events, progress tracking, timeline, output files
 */

        // ---- Step 3 → 4: Launch ----
        async function launchRun() {
            const topic = document.getElementById('pfTopic').value.trim();
            const audience = document.getElementById('pfAudience').value.trim();
            const length = document.getElementById('pfLength').value.trim();
            const userId = `gui_${Date.now()}`;
            const launchBtn = document.getElementById('pfLaunchBtn');

            launchBtn.disabled = true;
            launchBtn.textContent = t('uploading');

            try {
                // Upload user files
                const uploadFile = (f, category) => {
                    return fetch(`${serverUrl}/api/userbenches/${userId}/files/${f.path}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                        body: f.content
                    });
                };

                const uploads = [];
                [...pfContent, ...pfTemplate, ...pfStyle].forEach(f => {
                    if (!f.isDefault && f.content) uploads.push(uploadFile(f));
                });
                await Promise.all(uploads);

                // Build refs
                const contentRefs = pfContent.map(f => ({ name: f.name.replace(/\.[^.]+$/, ''), path: f.path, type: f.type || 'content' }));
                const templateRefs = pfTemplate.map(f => ({ name: f.name.replace(/\.[^.]+$/, ''), path: f.path, type: f.type || 'html_template' }));
                const styleRefs = pfStyle.map(f => ({ name: f.name.replace(/\.[^.]+$/, ''), path: f.path, type: f.type || 'guide' }));
                const allStyleRefs = [...templateRefs, ...styleRefs];

                const payload = {
                    plan_id: currentPlanId,
                    llm_model: selectedModel,
                    user_id: userId,
                    ground_inputs: {
                        '{演示主题}': { data: [[topic]], axes: ['_none_axis'] },
                        '{目标受众}': { data: [[audience || '一般受众']], axes: ['_none_axis'] },
                        '{期望长度}': { data: [[length || '6张幻灯片']], axes: ['_none_axis'] },
                    }
                };
                if (contentRefs.length > 0) payload.ground_inputs['[内容参考元数据]'] = { data: [contentRefs], axes: ['内容参考'] };
                if (allStyleRefs.length > 0) payload.ground_inputs['[样式参考元数据]'] = { data: [allStyleRefs], axes: ['样式参考'] };

                launchBtn.textContent = t('starting');

                const resp = await fetch(`${serverUrl}/api/runs`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || t('launchFailed'));
                }

                const data = await resp.json();
                const runId = data.run_id;

                // Move to step 4
                goTo(4);
                currentRunId = runId;
                currentUserId = userId;
                document.getElementById('pfRunStatus').textContent = t('runStarted') + `${runId.substring(0, 8)}...`;
                document.getElementById('pfProgressFill').style.width = '10%';
                document.getElementById('pfTimeline').innerHTML = '';
                document.getElementById('pfFinalFiles').innerHTML = '';
                document.getElementById('pfIntermediateFiles').innerHTML = '';

                startPfEventStream(runId, userId);

            } catch (e) {
                alert(t('launchFailed') + e.message);
                launchBtn.disabled = false;
                launchBtn.textContent = t('launch');
            }
        }

        // ---- SSE event stream ----
        // NOTE: Server sends all events as generic `data:` frames with event type
        // inside the JSON payload (data.event), NOT as named SSE events.
        // Therefore we use onmessage, not addEventListener.
        function startPfEventStream(runId, userId) {
            if (pfEvtSource) pfEvtSource.close();
            pfEvtSource = new EventSource(`${serverUrl}/api/runs/${runId}/stream`);

            pfEvtSource.onmessage = (e) => {
                try {
                    const data = JSON.parse(e.data);
                    const type = data.event || 'message';
                    pfHandleEvent(type, data);
                } catch (err) {}
            };

            pfEvtSource.onerror = () => {
                pfEvtSource.close();
                setTimeout(() => pfPollStatus(runId), 2000);
            };
        }

        function pfHandleEvent(type, data) {
            if (type === 'inference:started') {
                const name = (data.concept_name || data.flow_index || '…').substring(0, 40);
                const idx = data.flow_index || name;
                const isLoop = (data.sequence_type || '').toLowerCase().includes('loop') ||
                               (data.sequence_type || '').toLowerCase().includes('iterate');
                if (isLoop) {
                    pfLoop.current = idx;
                    pfLoop.iteration = 1;
                }
                addTimelineItem(idx, name, 'running', isLoop ? `${t('loopIter')} 1` : '');
            }
            else if (type === 'inference:completed') {
                const idx = data.flow_index || '';
                const dur = (data.duration || 0).toFixed(1) + t('seconds');
                if (data.is_loop && pfLoop.current === idx) {
                    const totalIter = data.total_iterations || pfLoop.iteration || 1;
                    updateTimelineItem(idx, 'done', `${totalIter} ${t('loopIter')} · ${dur}`);
                    pfLoop.current = null;
                    pfLoop.iteration = 0;
                } else {
                    updateTimelineItem(idx, 'done', dur);
                }
                pfPollOutputFiles();
            }
            else if (type === 'inference:failed') {
                const idx = data.flow_index || '';
                updateTimelineItem(idx, 'failed', data.error || data.status || '');
            }
            else if (type === 'inference:skipped') {
                const idx = data.flow_index || '';
                if (!pfTimelineMap[idx]) addTimelineItem(idx, idx, 'skipped', '');
                else updateTimelineItem(idx, 'skipped', '');
            }
            else if (type === 'inference:pending' || type === 'inference:restarted' || type === 'loop:progress') {
                const idx = data.flow_index || '';
                const iter = data.iteration || (pfLoop.iteration + 1);
                pfLoop.current = idx;
                pfLoop.iteration = iter;
                updateTimelineMeta(idx, `${t('loopIter')} ${iter}`);
            }
            else if (type === 'inference:in_progress' || type === 'inference:retry') {
                const idx = data.flow_index || '';
                if (!pfTimelineMap[idx]) addTimelineItem(idx, idx, 'running', '');
            }
            else if (type === 'inference:error') {
                const idx = data.flow_index || '';
                updateTimelineItem(idx, 'failed', data.error || '');
            }
            else if (type === 'execution:progress') {
                pfLoop.completed = data.completed_count || data.completed || 0;
                pfLoop.total = data.total_count || data.total || 0;
                pfUpdateProgress(pfLoop.completed, pfLoop.total);
            }
            else if (type === 'file:changed') {
                pfPollOutputFiles();
            }
            else if (type === 'run:completed') {
                if (pfEvtSource) pfEvtSource.close();
                document.getElementById('pfProgressFill').style.width = '100%';
                document.getElementById('pfRunStatus').textContent = t('runCompleted');
                document.getElementById('pfRunSub').textContent = t('runCompletedSub');
                pfPollOutputFiles();
                // Auto-expand files section
                const toggle = document.getElementById('pfFilesToggle');
                if (!toggle.classList.contains('open')) toggle.classList.add('open');
            }
            else if (type === 'run:failed') {
                if (pfEvtSource) pfEvtSource.close();
                document.getElementById('pfRunStatus').textContent = t('runFailed') + (data.error || 'Unknown');
                document.getElementById('pfProgressFill').style.width = '0%';
            }
        }

        // ---- Progress bar ----
        function pfUpdateProgress(completed, total) {
            const pct = total > 0 ? Math.min(Math.round(completed / total * 100), 100) : 0;
            document.getElementById('pfProgressFill').style.width = pct + '%';
            let text = `${completed} / ${total}${t('inferences')}`;
            if (pfLoop.current && pfLoop.iteration > 0) {
                text += ` · ${t('loopIter')} ${pfLoop.iteration}`;
            }
            document.getElementById('pfRunStatus').textContent = text;
        }

        // ---- Timeline helpers ----
        function addTimelineItem(id, name, status, meta) {
            const timeline = document.getElementById('pfTimeline');
            const icons = { running: '&#9654;', done: '&#10003;', failed: '&#10007;', skipped: '&#8709;' };
            const div = document.createElement('div');
            div.className = `pf-tl-item ${status}`;
            div.dataset.id = id;
            div.innerHTML = `
                <span class="pf-tl-icon">${icons[status] || '&#9654;'}</span>
                <span class="pf-tl-name">${escapeHtml(name)}</span>
                <span class="pf-tl-meta">${escapeHtml(meta)}</span>
            `;
            timeline.appendChild(div);
            timeline.scrollTop = timeline.scrollHeight;
            pfTimelineMap[id] = div;
        }

        function updateTimelineItem(id, status, meta) {
            const div = pfTimelineMap[id];
            if (!div) return;
            const icons = { running: '&#9654;', done: '&#10003;', failed: '&#10007;', skipped: '&#8709;' };
            div.className = `pf-tl-item ${status}`;
            div.querySelector('.pf-tl-icon').innerHTML = icons[status] || '';
            if (meta !== undefined) div.querySelector('.pf-tl-meta').textContent = meta;
        }

        function updateTimelineMeta(id, meta) {
            const div = pfTimelineMap[id];
            if (!div) return;
            div.querySelector('.pf-tl-meta').textContent = meta;
        }

        // ---- File polling ----
        let pfPollTimer = null;
        async function pfPollOutputFiles() {
            if (!currentUserId) return;
            // Debounce rapid calls
            clearTimeout(pfPollTimer);
            pfPollTimer = setTimeout(async () => {
                try {
                    const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files?category=productions&recursive=true`);
                    if (!resp.ok) return;
                    const files = await resp.json();
                    pfRenderFiles(files);
                } catch (e) {}
            }, 500);
        }

        function pfRenderFiles(files) {
            const allFiles = files.filter(f => !f.is_dir);
            const finals = allFiles.filter(f => f.path.includes('output/'));
            const intermediates = allFiles.filter(f => !f.path.includes('output/'));

            const extIcons = { html: '&#127760;', pptx: '&#128202;', json: '&#128203;', pdf: '&#128196;', md: '&#128221;', css: '&#127912;', txt: '&#128196;' };
            function icon(name) {
                const ext = name.split('.').pop().toLowerCase();
                return extIcons[ext] || '&#128196;';
            }
            function size(bytes) {
                return bytes > 1024 ? (bytes / 1024).toFixed(1) + ' KB' : bytes + ' B';
            }

            const finalEl = document.getElementById('pfFinalFiles');
            const interEl = document.getElementById('pfIntermediateFiles');

            if (finals.length > 0) {
                finalEl.innerHTML = `<div class="pf-section-label">${t('finalOutputs')}</div>` +
                    finals.map(f => `
                        <div class="pf-file-card final">
                            <span class="pf-fc-icon">${icon(f.name)}</span>
                            <span class="pf-fc-name">${escapeHtml(f.name)}</span>
                            <span class="pf-fc-size">${size(f.size || 0)}</span>
                            <div class="pf-fc-actions">
                                <button class="pf-fc-btn" onclick="pfPreviewOutput('${f.path}','${escapeHtml(f.name)}')" title="${t('preview')}">&#128065;</button>
                                <button class="pf-fc-btn" onclick="pfDownload('${f.path}','${escapeHtml(f.name)}')" title="${t('download')}">&#11015;</button>
                            </div>
                        </div>
                    `).join('');
            } else {
                finalEl.innerHTML = '';
            }

            if (intermediates.length > 0) {
                interEl.innerHTML = `<div class="pf-section-label">${t('intermediateFiles')}</div>` +
                    intermediates.map(f => `
                        <div class="pf-file-card">
                            <span class="pf-fc-icon">${icon(f.name)}</span>
                            <span class="pf-fc-name">${escapeHtml(f.name)}</span>
                            <span class="pf-fc-size">${size(f.size || 0)}</span>
                            <div class="pf-fc-actions">
                                <button class="pf-fc-btn" onclick="pfPreviewOutput('${f.path}','${escapeHtml(f.name)}')" title="${t('preview')}">&#128065;</button>
                            </div>
                        </div>
                    `).join('');
            } else {
                interEl.innerHTML = '';
            }

            // Auto-expand when first file arrives
            if (allFiles.length > 0) {
                const toggle = document.getElementById('pfFilesToggle');
                if (!toggle.classList.contains('open')) toggle.classList.add('open');
            }
        }

        // ---- Preview / Download output files (reuses existing modal) ----
        async function pfPreviewOutput(path, name) {
            const overlay = document.getElementById('pfPreviewOverlay');
            const body = document.getElementById('pfPreviewBody');
            document.getElementById('pfPreviewTitle').textContent = name;

            // Binary file — show placeholder (no fetch)
            if (!isPreviewable(name)) {
                renderPreviewContent(body, name, '', { downloadUrl: path });
                overlay.classList.add('open');
                return;
            }

            try {
                const resp = await fetch(`${serverUrl}/api/userbenches/${currentUserId}/files/${path}`);
                if (!resp.ok) throw new Error(resp.statusText);

                let content;
                const ct = resp.headers.get('content-type') || '';
                if (ct.includes('application/json')) {
                    const data = await resp.json();
                    content = typeof data.content === 'string' ? data.content : JSON.stringify(data, null, 2);
                } else {
                    content = await resp.text();
                }

                renderPreviewContent(body, name, content, { downloadUrl: path });
                overlay.classList.add('open');
            } catch (e) {
                alert(t('previewFailed') + e.message);
            }
        }

        function pfDownload(path, name) {
            const a = document.createElement('a');
            a.href = `${serverUrl}/api/userbenches/${currentUserId}/files/${path}`;
            a.download = name;
            a.click();
        }

        // ---- Fallback: poll run status if SSE drops ----
        async function pfPollStatus(runId) {
            if (!runId) return;
            try {
                const resp = await fetch(`${serverUrl}/api/runs/${runId}`);
                const data = await resp.json();
                if (data.progress) {
                    pfUpdateProgress(data.progress.completed_count || 0, data.progress.total_count || 0);
                }
                if (data.status === 'completed') {
                    pfHandleEvent('run:completed', {});
                } else if (data.status === 'failed') {
                    pfHandleEvent('run:failed', { error: data.error });
                } else if (data.status === 'running') {
                    setTimeout(() => pfPollStatus(runId), 3000);
                }
            } catch (e) {
                setTimeout(() => pfPollStatus(runId), 5000);
            }
        }

