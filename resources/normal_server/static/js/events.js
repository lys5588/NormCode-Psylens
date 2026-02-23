/**
 * NormCode Server UI - Event Stream
 */

function connectEventStream() {
    eventSource = new EventSource(`${API}/monitor/stream`);
    
    eventSource.onopen = () => {
        document.getElementById('statusDot').classList.add('connected');
        document.getElementById('statusText').textContent = 'Connected';
    };
    
    eventSource.onerror = () => {
        document.getElementById('statusDot').classList.remove('connected');
        document.getElementById('statusText').textContent = 'Disconnected';
        setTimeout(connectEventStream, 3000);
    };
    
    eventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            handleEvent(data);
        } catch {}
    };
}

function handleEvent(data) {
    const type = data.event;
    
    if (type === 'monitor:connected') {
        stats = data.stats || {};
        updateStats();
        return;
    }
    
    if (type === 'run:started') stats.runs_started = (stats.runs_started || 0) + 1;
    if (type === 'run:completed') { stats.runs_completed = (stats.runs_completed || 0) + 1; fetchRuns(); }
    if (type === 'run:failed') fetchRuns();
    if (type === 'inference:completed') stats.inferences_executed = (stats.inferences_executed || 0) + 1;
    
    updateStats();
    addEvent(data);
}

function updateStats() {
    document.getElementById('statRuns').textContent = stats.runs_started || 0;
}

function addEvent(data) {
    events.unshift(data);
    if (events.length > 200) events = events.slice(0, 200);
    document.getElementById('eventCount').textContent = events.length + ' events';
    
    const container = document.getElementById('eventsList');
    const el = document.createElement('div');
    el.className = 'event-item new';
    
    const type = data.event || '?';
    let typeClass = '';
    if (type.startsWith('run:')) typeClass = 'run';
    else if (type.startsWith('inference:')) typeClass = 'inference';
    else if (type.includes('error') || type.includes('failed')) typeClass = 'error';
    
    const time = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : '';
    const details = [data.run_id?.slice(0,8), data.flow_index, data.concept_name].filter(Boolean).join(' · ');
    
    el.innerHTML = `
        <span class="event-time">${time}</span>
        <span class="event-type ${typeClass}">${type}</span>
        <span class="event-details">${details || '—'}</span>
    `;
    
    container.insertBefore(el, container.firstChild);
    while (container.children.length > 100) container.removeChild(container.lastChild);
}

function clearEvents() {
    events = [];
    document.getElementById('eventsList').innerHTML = '';
    document.getElementById('eventCount').textContent = '0 events';
}
