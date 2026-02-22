// ============================================================================
// UI Helpers
// ============================================================================

function toggleSection(header) {
    header.parentElement.classList.toggle('open');
}

function showTab(name) {
    document.querySelectorAll('.panel:nth-child(2) .tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel:nth-child(2) .tab-content').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(name + 'Tab').classList.add('active');
}

function showInspectorTab(name) {
    document.querySelectorAll('.panel:nth-child(3) .tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel:nth-child(3) .tab-content').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(name + 'InspectorTab').classList.add('active');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeHtmlAttr(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;');
}

function toggleModelPicker() {
    const picker = document.getElementById('modelPicker');
    const list = document.getElementById('modelPickerList');
    const llmSelect = document.getElementById('llmModel');

    if (!picker.hidden) {
        picker.hidden = true;
        return;
    }

    // Build options from the hidden select
    list.innerHTML = '';
    Array.from(llmSelect.options).forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'model-picker-item' + (opt.value === llmSelect.value ? ' active' : '');
        btn.textContent = opt.textContent;
        btn.onclick = () => {
            llmSelect.value = opt.value;
            document.getElementById('sessionModel').textContent = opt.textContent;
            picker.hidden = true;
        };
        list.appendChild(btn);
    });

    picker.hidden = false;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

