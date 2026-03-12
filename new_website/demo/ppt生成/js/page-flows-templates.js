/**
 * Page-Flows Templates — Template Set Picker
 *
 * Loads sets.json, renders set tabs + visual thumbnail grid,
 * tracks per-set selection state, and syncs into pfTemplate
 * before the Review step or launch.
 */

const TEMPLATES_BASE = 'templates';

async function loadTemplateSets() {
    try {
        const resp = await fetch(`${TEMPLATES_BASE}/sets.json`);
        if (!resp.ok) throw new Error(resp.statusText);
        templateSetsData = await resp.json();
        renderSetTabs();
        if (templateSetsData.sets.length > 0) {
            const firstId = templateSetsData.sets[0].id;
            templateSetsData.sets.forEach(set => {
                templateSelections[set.id] = new Set(
                    set.templates.map((_, i) => i)
                );
            });
            await switchSet(firstId);
        }
    } catch (e) {
        console.warn('[loadTemplateSets]', e);
    }
}

function renderSetTabs() {
    const container = document.getElementById('pfSetTabs');
    if (!container || !templateSetsData) return;
    const lang = (typeof i18n !== 'undefined' && i18n.getLang) ? i18n.getLang() : 'zh';

    container.innerHTML = templateSetsData.sets.map(set => {
        const name = set.name[lang] || set.name.en || set.id;
        const active = set.id === currentSetId ? ' active' : '';
        return `<button class="pf-set-tab${active}" data-set-id="${set.id}"
                    style="--set-accent:${set.accent}"
                    onclick="switchSet('${set.id}')">
                    <span class="pf-set-dot" style="background:${set.accent}"></span>
                    ${escapeHtml(name)}
                </button>`;
    }).join('');
}

async function switchSet(setId) {
    currentSetId = setId;
    renderSetTabs();

    const set = templateSetsData.sets.find(s => s.id === setId);
    if (!set) return;

    if (!templateContentCache[setId]) {
        await fetchSetTemplates(set);
    }

    renderTemplateGrid();
    updateSelectionCount();
}

async function fetchSetTemplates(set) {
    const cache = {};
    const fetches = set.templates.map(async (tmpl) => {
        try {
            const resp = await fetch(`${TEMPLATES_BASE}/${set.id}/${tmpl.file}`);
            if (resp.ok) {
                cache[tmpl.file] = await resp.text();
            }
        } catch (e) {
            console.warn(`[fetchSetTemplates] ${set.id}/${tmpl.file}`, e);
        }
    });
    await Promise.all(fetches);
    templateContentCache[set.id] = cache;
}

function renderTemplateGrid() {
    const grid = document.getElementById('pfTemplateGrid');
    if (!grid || !currentSetId) return;

    const set = templateSetsData.sets.find(s => s.id === currentSetId);
    if (!set) return;

    const cache = templateContentCache[currentSetId] || {};
    const selections = templateSelections[currentSetId] || new Set();

    grid.innerHTML = set.templates.map((tmpl, i) => {
        const selected = selections.has(i);
        const html = cache[tmpl.file];
        const rendered = html ? replaceTemplatePlaceholders(html) : '';
        const safeHtml = rendered.replace(/"/g, '&quot;');

        return `<div class="pf-tmpl-card${selected ? ' selected' : ''}"
                     onclick="toggleTemplate('${currentSetId}', ${i})"
                     title="${escapeHtml(tmpl.name)} — ${escapeHtml(tmpl.for)}">
            <div class="pf-tmpl-thumb">
                ${html ? `<iframe srcdoc="${safeHtml}" sandbox="allow-same-origin" scrolling="no" tabindex="-1"></iframe>` : '<div class="pf-tmpl-placeholder">Loading...</div>'}
                <div class="pf-tmpl-check">${selected ? '&#9745;' : '&#9744;'}</div>
            </div>
            <div class="pf-tmpl-info">
                <div class="pf-tmpl-name">${escapeHtml(tmpl.name)}</div>
                <div class="pf-tmpl-for">${escapeHtml(tmpl.for)}</div>
            </div>
        </div>`;
    }).join('');

    renderCustomUploadsInGrid();
}

function renderCustomUploadsInGrid() {
    const grid = document.getElementById('pfTemplateGrid');
    if (!grid) return;

    customUploadTemplates.forEach((f, i) => {
        const rendered = f.content ? replaceTemplatePlaceholders(f.content) : '';
        const safeHtml = rendered.replace(/"/g, '&quot;');
        const card = document.createElement('div');
        card.className = 'pf-tmpl-card selected custom';
        card.title = f.name;
        card.onclick = () => removeCustomTemplate(i);
        card.innerHTML = `
            <div class="pf-tmpl-thumb">
                ${f.content ? `<iframe srcdoc="${safeHtml}" sandbox="allow-same-origin" scrolling="no" tabindex="-1"></iframe>` : '<div class="pf-tmpl-placeholder">—</div>'}
                <button class="pf-tmpl-remove" onclick="event.stopPropagation();removeCustomTemplate(${i})">&times;</button>
            </div>
            <div class="pf-tmpl-info">
                <div class="pf-tmpl-name">${escapeHtml(f.name)}</div>
                <div class="pf-tmpl-for">${t('customUpload')}</div>
            </div>`;
        grid.appendChild(card);
    });
}

function toggleTemplate(setId, idx) {
    if (!templateSelections[setId]) templateSelections[setId] = new Set();
    const sel = templateSelections[setId];
    if (sel.has(idx)) sel.delete(idx);
    else sel.add(idx);
    renderTemplateGrid();
    updateSelectionCount();
}

function selectAllTemplates() {
    if (!currentSetId || !templateSetsData) return;
    const set = templateSetsData.sets.find(s => s.id === currentSetId);
    if (!set) return;
    templateSelections[currentSetId] = new Set(set.templates.map((_, i) => i));
    renderTemplateGrid();
    updateSelectionCount();
}

function deselectAllTemplates() {
    if (!currentSetId) return;
    templateSelections[currentSetId] = new Set();
    renderTemplateGrid();
    updateSelectionCount();
}

function updateSelectionCount() {
    const countEl = document.getElementById('pfSetCount');
    if (!countEl || !currentSetId || !templateSetsData) return;

    const set = templateSetsData.sets.find(s => s.id === currentSetId);
    if (!set) return;

    const sel = templateSelections[currentSetId] || new Set();
    const total = set.templates.length + customUploadTemplates.length;
    const selected = sel.size + customUploadTemplates.length;
    countEl.textContent = `${selected}/${total} ${t('nSelected')}`;
}

function syncPfTemplateFromSets() {
    pfTemplate = [];

    if (!templateSetsData) return;

    templateSetsData.sets.forEach(set => {
        const sel = templateSelections[set.id];
        if (!sel || sel.size === 0) return;
        const cache = templateContentCache[set.id] || {};

        set.templates.forEach((tmpl, i) => {
            if (!sel.has(i)) return;
            const content = cache[tmpl.file] || '';
            pfTemplate.push({
                name:      tmpl.file,
                path:      `provisions/inputs/templates/${tmpl.file}`,
                content:   content,
                type:      'html_template',
                isDefault: false,
                setId:     set.id
            });
        });
    });

    customUploadTemplates.forEach(f => {
        pfTemplate.push({
            name:      f.name,
            path:      f.path,
            content:   f.content,
            type:      'html_template',
            isDefault: false
        });
    });
}

function handleCustomTemplateUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    event.target.value = '';

    Array.from(files).forEach(file => {
        if (!file.name.endsWith('.html') && !file.name.endsWith('.htm')) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            customUploadTemplates.push({
                name:    file.name,
                path:    `provisions/inputs/templates/${file.name}`,
                content: e.target.result
            });
            renderTemplateGrid();
            updateSelectionCount();
        };
        reader.readAsText(file);
    });
}

function removeCustomTemplate(idx) {
    customUploadTemplates.splice(idx, 1);
    renderTemplateGrid();
    updateSelectionCount();
}

function handleCustomTemplateDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    const files = event.dataTransfer.files;
    if (!files || files.length === 0) return;
    handleCustomTemplateUpload({ target: { files, value: '' }, preventDefault: () => {} });
}

function previewSetTemplate(setId, idx) {
    const set = templateSetsData?.sets.find(s => s.id === setId);
    if (!set) return;
    const tmpl = set.templates[idx];
    if (!tmpl) return;

    const cache = templateContentCache[setId] || {};
    const content = cache[tmpl.file];
    if (!content) return;

    const overlay = document.getElementById('pfPreviewOverlay');
    const body    = document.getElementById('pfPreviewBody');
    document.getElementById('pfPreviewTitle').textContent = tmpl.name + ' — ' + tmpl.file;
    renderPreviewContent(body, tmpl.file, content, { fileType: 'html_template' });
    overlay.classList.add('open');
}
