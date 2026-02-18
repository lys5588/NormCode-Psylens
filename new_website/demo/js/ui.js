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

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

