// ============================================================================
// Event Stream Handling & Progress
// ============================================================================

function startEventStream() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource(`${serverUrl}/api/runs/${currentRunId}/stream`);

    eventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            handleEvent(data.event || 'message', data);
        } catch (err) {}
    };

    ['inference:started', 'inference:completed', 'inference:failed',
     'inference:pending', 'inference:restarted', 'inference:skipped',
     'inference:in_progress', 'inference:retry', 'inference:error',
     'run:completed', 'run:failed', 'run:started',
     'execution:progress', 'execution:paused',
     'cycle:started', 'cycle:completed',
     'file:changed', 'node:statuses',
     'userbench:created', 'breakpoint:hit',
     'loop:progress'].forEach(type => {
        eventSource.addEventListener(type, (e) => {
            try {
                handleEvent(type, JSON.parse(e.data));
            } catch (err) {}
        });
    });

    eventSource.onerror = () => {
        setTimeout(pollStatus, 2000);
    };
}

function handleEvent(type, data) {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    if (type === 'inference:started') {
        const name = (data.concept_name || '推理').substring(0, 35);
        const seqType = data.sequence_type || '';
        if (seqType.toLowerCase().includes('loop') || seqType.toLowerCase().includes('iterate')) {
            loopProgress.currentLoop = data.flow_index || '';
            loopProgress.iteration = 1;
            loopProgress.totalIterations = data.total_iterations || null;
            addEvent(time, 'started', `🔄 ${name} (循环开始)`);
        } else {
            addEvent(time, 'started', `▶ ${name}`);
        }
    }
    else if (type === 'inference:completed') {
        const idx = data.flow_index || '';
        const dur = (data.duration || 0).toFixed(1);
        if (data.is_loop) {
            const totalIter = data.total_iterations || loopProgress.iteration || 1;
            addEvent(time, 'completed', `✓ ${idx} 循环完成 (共 ${totalIter} 轮, ${dur}秒)`);
            if (loopProgress.currentLoop === idx) {
                loopProgress.currentLoop = null;
                loopProgress.iteration = 0;
            }
        } else {
            addEvent(time, 'completed', `✓ ${idx} (${dur}秒)`);
        }
        pollOutputFiles();
    }
    else if (type === 'inference:failed') {
        addEvent(time, 'failed', `✗ ${data.flow_index || ''}: ${data.error || data.status || '失败'}`);
    }
    else if (type === 'inference:pending') {
        const idx = data.flow_index || '';
        const iteration = data.iteration || 1;
        loopProgress.currentLoop = idx;
        loopProgress.iteration = iteration;
        addEvent(time, 'pending', `⟳ ${idx} 循环第 ${iteration} 轮`);
        updateLoopDisplay(idx, iteration);
    }
    else if (type === 'inference:restarted') {
        const idx = data.flow_index || '';
        const iteration = data.iteration || (loopProgress.iteration + 1);
        loopProgress.currentLoop = idx;
        loopProgress.iteration = iteration;
        addEvent(time, 'restarted', `↺ ${idx} 开始第 ${iteration} 轮`);
        updateLoopDisplay(idx, iteration);
    }
    else if (type === 'inference:skipped') {
        addEvent(time, 'skipped', `⊘ ${data.flow_index || ''} (条件不满足，跳过)`);
    }
    else if (type === 'inference:in_progress') {
        addEvent(time, 'in_progress', `⏳ ${data.flow_index || ''} (处理中)`);
    }
    else if (type === 'inference:retry') {
        addEvent(time, 'retry', `🔄 ${data.flow_index || ''} (重试)`);
    }
    else if (type === 'inference:error') {
        addEvent(time, 'failed', `❌ ${data.flow_index || ''}: ${data.error || '错误'}`);
    }
    else if (type === 'execution:progress') {
        updateProgress(data.completed_count || 0, data.total_count || 0, data.loop_iterations || 0);
    }
    else if (type === 'loop:progress') {
        const idx = data.flow_index || '';
        const iteration = data.iteration || 1;
        loopProgress.currentLoop = idx;
        loopProgress.iteration = iteration;
        updateLoopDisplay(idx, iteration);
    }
    else if (type === 'execution:paused') {
        addEvent(time, 'paused', `⏸️ 已暂停`);
    }
    else if (type === 'file:changed') {
        addEvent(time, 'file', `📄 ${data.path || data.file || '文件'}`);
        pollOutputFiles();
    }
    else if (type === 'run:started') {
        addEvent(time, 'started', `🚀 运行开始: ${data.plan_id || ''}`);
    }
    else if (type === 'run:completed') {
        onRunCompleted();
    }
    else if (type === 'run:failed') {
        onRunFailed(data.error || '未知错误');
    }
    else if (type === 'userbench:created') {
        addEvent(time, 'info', `📂 工作空间已创建`);
    }
    else if (type === 'breakpoint:hit') {
        addEvent(time, 'paused', `🔴 断点命中: ${data.flow_index || ''}`);
    }
}

// ===== Event Log =====
function addEvent(time, type, message) {
    if (!eventsLog) {
        console.log(`[Event] ${time} [${type}] ${message}`);
        return;
    }
    if (eventsLog.querySelector('div[style*="text-align: center"]')) {
        eventsLog.innerHTML = '';
    }
    const div = document.createElement('div');
    div.className = 'event';
    div.innerHTML = `
        <span class="event-time">${time}</span>
        <span class="event-msg ${type}">${message}</span>
    `;
    eventsLog.appendChild(div);
    eventsLog.scrollTop = eventsLog.scrollHeight;
}

// ===== Progress Tracking =====
function updateProgress(completed, total, loopIterations = 0) {
    loopProgress.completedInferences = completed;
    loopProgress.totalInferences = total;

    const pct = total > 0 ? Math.min((completed / total * 100), 100) : 0;
    progressFill.style.width = `${pct}%`;

    let text = `${completed} / ${total} 推理`;
    if (loopProgress.currentLoop && loopProgress.iteration > 0) {
        text += ` | 循环第 ${loopProgress.iteration} 轮`;
    }
    if (loopIterations > 0 && !loopProgress.currentLoop) {
        text += ` (含 ${loopIterations} 次迭代)`;
    }
    progressText.textContent = text;
}

function updateLoopDisplay(flowIndex, iteration) {
    const completed = loopProgress.completedInferences;
    const total = loopProgress.totalInferences;

    progressText.textContent = `${completed} / ${total} 推理 | 🔄 循环第 ${iteration} 轮`;

    progressFill.classList.add('pulsing');
    setTimeout(() => progressFill.classList.remove('pulsing'), 500);
}

// ===== Status Polling =====
async function pollStatus() {
    if (!currentRunId) return;

    try {
        const resp = await fetch(`${serverUrl}/api/runs/${currentRunId}`);
        const data = await resp.json();

        if (data.progress) {
            updateProgress(data.progress.completed_count || 0, data.progress.total_count || 0);
        }

        if (data.status === 'completed') {
            onRunCompleted();
        } else if (data.status === 'failed') {
            onRunFailed(data.error);
        } else if (data.status === 'running') {
            setTimeout(pollStatus, 2000);
        }
    } catch (e) {
        setTimeout(pollStatus, 3000);
    }
}

// ===== Run Completion =====
function onRunCompleted() {
    if (eventSource) eventSource.close();

    statusDot.className = 'status-dot connected';
    statusText.textContent = '已完成！';
    startBtn.disabled = false;
    startBtn.textContent = '🚀 开始生成';

    addEvent(new Date().toLocaleTimeString('en-US', { hour12: false }), 'completed', '★ 运行完成！');

    pollOutputFiles();
    refreshInspector();
}

function onRunFailed(error) {
    if (eventSource) eventSource.close();

    statusDot.className = 'status-dot error';
    statusText.textContent = `失败: ${error}`;
    startBtn.disabled = false;
    startBtn.textContent = '🚀 开始生成';

    addEvent(new Date().toLocaleTimeString('en-US', { hour12: false }), 'failed', `★ ${error}`);
}

