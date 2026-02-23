/**
 * Tools Panel – standalone vanilla JS (no React / build step)
 *
 * Renders deployment-tool cards inside a container element, with
 * expand / collapse, config display, and per-tool test forms.
 */
(function () {
  'use strict';

  const API = window.location.origin + '/api';

  // -- palette (matches server.css variables) ----------------------------
  const C = {
    bg:     '#0d1117',
    card:   '#161b22',
    hover:  '#21262d',
    border: '#30363d',
    text:   '#c9d1d9',
    dim:    '#8b949e',
    blue:   '#58a6ff',
    green:  '#3fb950',
    red:    '#f85149',
    yellow: '#d29922',
    purple: '#a371f7',
  };

  const CATEGORY_STYLE = {
    core:        { color: C.blue,   bg: C.blue   + '1a' },
    media:       { color: C.purple, bg: C.purple + '1a' },
    utility:     { color: C.yellow, bg: C.yellow + '1a' },
    interaction: { color: C.green,  bg: C.green  + '1a' },
  };

  const TOOL_ICON = {
    llm: '🧠', file_system: '💾', python_interpreter: '🐍',
    gim: '🖼️', prompt: '📄', formatter: '{ }',
    composition: '🔗', user_input: '💬',
  };

  // -- helpers -----------------------------------------------------------
  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) Object.entries(attrs).forEach(([k, v]) => {
      if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
      else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
      else e.setAttribute(k, v);
    });
    if (typeof children === 'string') e.innerHTML = children;
    else if (Array.isArray(children)) children.forEach(c => { if (c) e.appendChild(c); });
    else if (children instanceof Node) e.appendChild(children);
    return e;
  }

  async function fetchJson(url)  { const r = await fetch(url);  if (!r.ok) throw new Error(`${r.status}: ${r.statusText}`); return r.json(); }
  async function postJson(url, body) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const t = await r.text().catch(() => r.statusText); throw new Error(`${r.status}: ${t}`); }
    return r.json();
  }

  // -- state -------------------------------------------------------------
  let _container = null;
  let _tools = [];
  let _expanded = null;
  let _pythonPackages = null;   // cached package list
  let _pythonPkgFilter = '';
  let _pythonPkgLoading = false;

  // -- public API --------------------------------------------------------
  function mount(container) {
    _container = container;
    render();
    loadTools();
  }

  async function loadTools() {
    renderLoading();
    try {
      const data = await fetchJson(`${API}/tools`);
      _tools = data.tools || [];
      render();
    } catch (e) {
      renderError(e.message);
    }
  }

  // -- renderers ---------------------------------------------------------
  function renderLoading() {
    if (!_container) return;
    _container.innerHTML = '';
    _container.appendChild(el('div', { style: {
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '256px', color: C.blue, fontSize: '1.5rem',
    }}, '⟳ Loading tools…'));
  }

  function renderError(msg) {
    if (!_container) return;
    _container.innerHTML = '';
    const wrap = el('div', { style: {
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', height: '256px', color: C.dim,
    }});
    wrap.appendChild(el('div', { style: { fontSize: '2.5rem', marginBottom: '8px', opacity: '0.3' } }, '🔧'));
    wrap.appendChild(el('div', { style: { fontSize: '0.875rem', color: C.red } }, esc(msg)));
    const retry = el('button', {
      style: { marginTop: '12px', fontSize: '0.75rem', color: C.blue, background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' },
      onClick: loadTools,
    }, 'Retry');
    wrap.appendChild(retry);
    _container.appendChild(wrap);
  }

  function render() {
    if (!_container) return;
    _container.innerHTML = '';

    const root = el('div', { style: { padding: '16px', minHeight: '100%', background: C.bg } });

    // header
    const header = el('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' } });
    header.appendChild(el('div', { style: { display: 'flex', alignItems: 'center', gap: '8px', color: C.text, fontWeight: '600', fontSize: '0.875rem' } },
      '🔧 Deployment Tools'));
    const refreshBtn = el('button', {
      style: { fontSize: '0.75rem', color: C.dim, background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px', borderRadius: '4px' },
      onClick: loadTools,
    }, '↻ Refresh');
    refreshBtn.onmouseenter = () => { refreshBtn.style.color = C.text; refreshBtn.style.background = C.hover; };
    refreshBtn.onmouseleave = () => { refreshBtn.style.color = C.dim; refreshBtn.style.background = 'none'; };
    header.appendChild(refreshBtn);
    root.appendChild(header);

    // summary
    const avail = _tools.filter(t => t.available).length;
    root.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim, marginBottom: '12px' } },
      `${avail} of ${_tools.length} tools available`));

    const core  = _tools.filter(t => t.category === 'core');
    const other = _tools.filter(t => t.category !== 'core');

    if (core.length) {
      root.appendChild(sectionLabel('Core Tools'));
      core.forEach(t => root.appendChild(toolCard(t)));
    }
    if (other.length) {
      root.appendChild(sectionLabel('Other Tools'));
      other.forEach(t => root.appendChild(toolCard(t)));
    }

    _container.appendChild(root);
  }

  function sectionLabel(text) {
    return el('div', { style: {
      fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em',
      color: C.dim, fontWeight: '600', marginTop: '16px', marginBottom: '8px',
    }}, text);
  }

  // -- tool card ---------------------------------------------------------
  function toolCard(tool) {
    const isExpanded = _expanded === tool.id;
    const icon = TOOL_ICON[tool.id] || '🔧';
    const cat = CATEGORY_STYLE[tool.category] || CATEGORY_STYLE.utility;

    const card = el('div', { style: {
      background: C.card, borderRadius: '8px', border: `1px solid ${C.border}`,
      overflow: 'hidden', marginBottom: '8px',
    }});

    // header button
    const btn = el('button', { style: {
      width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
      padding: '12px 16px', textAlign: 'left', background: 'none',
      border: 'none', cursor: 'pointer', color: C.text, transition: 'background .15s',
    }});
    btn.onmouseenter = () => { btn.style.background = C.hover; };
    btn.onmouseleave = () => { btn.style.background = 'none'; };
    btn.onclick = () => {
      const wasExpanded = _expanded === tool.id;
      _expanded = wasExpanded ? null : tool.id;
      if (wasExpanded && tool.id === 'python_interpreter') {
        _pythonPackages = null;
        _pythonPkgFilter = '';
      }
      render();
    };

    btn.appendChild(el('span', { style: { fontSize: '1rem', flexShrink: '0', filter: tool.available ? 'none' : 'grayscale(1) opacity(0.5)' } }, icon));

    // name + desc
    const info = el('div', { style: { flex: '1', minWidth: '0' } });
    const nameRow = el('div', { style: { display: 'flex', alignItems: 'center', gap: '6px' } });
    nameRow.appendChild(el('span', { style: { fontSize: '0.875rem', fontWeight: '500', color: C.text } }, esc(tool.name)));
    nameRow.appendChild(el('span', { style: {
      fontSize: '10px', padding: '1px 6px', borderRadius: '9999px',
      color: cat.color, background: cat.bg,
    }}, tool.category));
    info.appendChild(nameRow);
    info.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: '2px' } }, esc(tool.description)));
    btn.appendChild(info);

    // status badge
    const badge = tool.available
      ? el('span', { style: { fontSize: '10px', padding: '2px 8px', borderRadius: '9999px', color: C.green, background: C.green + '1a', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: '0' } }, '✓ Available')
      : el('span', { style: { fontSize: '10px', padding: '2px 8px', borderRadius: '9999px', color: C.red,   background: C.red   + '1a', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: '0' } }, '✗ Missing');
    btn.appendChild(badge);

    btn.appendChild(el('span', { style: { color: C.dim, fontSize: '0.875rem', flexShrink: '0' } }, isExpanded ? '▾' : '▸'));
    card.appendChild(btn);

    // expanded body
    if (isExpanded) {
      const body = el('div', { style: { borderTop: `1px solid ${C.border}`, padding: '12px 16px' } });
      body.appendChild(configSection(tool));
      if (tool.testable && tool.available) body.appendChild(testerSection(tool));
      card.appendChild(body);
    }

    return card;
  }

  // -- config display ----------------------------------------------------
  function configRow(label, value, mono) {
    const row = el('div', { style: { display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.75rem', marginBottom: '4px' } });
    row.appendChild(el('span', { style: { color: C.dim, width: '80px', flexShrink: '0' } }, label));
    row.appendChild(el('span', { style: { color: C.text, wordBreak: 'break-all', fontFamily: mono ? 'monospace' : 'inherit', fontSize: mono ? '11px' : 'inherit' } }, esc(String(value))));
    return row;
  }

  // -- Python packages management ----------------------------------------
  async function loadPythonPackages() {
    _pythonPkgLoading = true;
    render();
    try {
      const data = await fetchJson(`${API}/tools/python/packages`);
      _pythonPackages = data.packages || [];
    } catch (e) {
      _pythonPackages = [];
    }
    _pythonPkgLoading = false;
    render();
  }

  async function installPythonPackage(pkgString) {
    const pkgs = pkgString.split(/[,\s]+/).filter(p => p.length > 0);
    if (!pkgs.length) return;
    try {
      await postJson(`${API}/tools/python/packages/install`, { packages: pkgs });
    } catch (e) { /* ignore */ }
    await loadPythonPackages();
  }

  async function uninstallPythonPackage(pkg) {
    try {
      await postJson(`${API}/tools/python/packages/uninstall`, { packages: [pkg] });
    } catch (e) { /* ignore */ }
    await loadPythonPackages();
  }

  function pythonPackagesSection(tool) {
    const cfg = tool.config || {};
    const wrap = el('div', { style: { marginBottom: '12px' } });

    // compact Python info header
    const infoRow = el('div', { style: {
      display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px',
      background: C.hover, borderRadius: '6px', marginBottom: '12px',
    }});
    infoRow.appendChild(el('span', { style: { fontSize: '1rem' } }, '🐍'));
    const infoText = el('div', { style: { flex: '1', minWidth: '0' } });
    if (cfg.python_version) {
      infoText.appendChild(el('div', { style: { fontSize: '0.75rem', fontWeight: '500', color: C.text } },
        'Python ' + esc(cfg.python_version)));
    }
    if (cfg.python_path) {
      infoText.appendChild(el('div', { style: { fontSize: '10px', color: C.dim, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } },
        esc(cfg.python_path)));
    }
    infoRow.appendChild(infoText);
    wrap.appendChild(infoRow);

    // section header
    const hdr = el('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' } });
    hdr.appendChild(el('div', { style: { fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: C.dim, fontWeight: '600' } },
      '📦 Environment Packages' + (_pythonPackages ? ` (${_pythonPackages.length})` : '')));
    const refreshBtn = el('button', {
      style: { fontSize: '10px', color: C.dim, background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', borderRadius: '4px' },
      onClick: loadPythonPackages,
    }, '↻');
    refreshBtn.onmouseenter = () => { refreshBtn.style.color = C.text; refreshBtn.style.background = C.hover; };
    refreshBtn.onmouseleave = () => { refreshBtn.style.color = C.dim; refreshBtn.style.background = 'none'; };
    hdr.appendChild(refreshBtn);
    wrap.appendChild(hdr);

    // install input row
    const installRow = el('div', { style: { display: 'flex', gap: '6px', marginBottom: '10px' } });
    const installInput = el('input', { type: 'text', placeholder: 'numpy, pandas==2.1.0, requests…', style: {
      flex: '1', fontSize: '0.75rem', border: `1px solid ${C.border}`, borderRadius: '4px',
      padding: '6px 8px', color: C.text, background: C.bg, outline: 'none', fontFamily: 'monospace',
      boxSizing: 'border-box',
    }});
    const installBtn = el('button', { style: {
      display: 'flex', alignItems: 'center', gap: '4px',
      padding: '6px 10px', fontSize: '0.7rem', fontWeight: '500', borderRadius: '4px',
      background: '#238636', color: '#fff', border: 'none', cursor: 'pointer', whiteSpace: 'nowrap',
    }}, '⬇ Install');
    installBtn.onmouseenter = () => { installBtn.style.background = '#2ea043'; };
    installBtn.onmouseleave = () => { installBtn.style.background = '#238636'; };
    installBtn.onclick = async () => {
      const val = installInput.value.trim();
      if (!val) return;
      installBtn.disabled = true;
      installBtn.textContent = '⟳ Installing…';
      installBtn.style.opacity = '0.6';
      await installPythonPackage(val);
      installBtn.disabled = false;
      installBtn.textContent = '⬇ Install';
      installBtn.style.opacity = '1';
    };
    installInput.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); installBtn.click(); } };
    installRow.appendChild(installInput);
    installRow.appendChild(installBtn);
    wrap.appendChild(installRow);

    // loading state
    if (_pythonPkgLoading) {
      wrap.appendChild(el('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', color: C.dim, fontSize: '0.75rem' } },
        '⟳ Loading packages…'));
      return wrap;
    }

    // trigger initial load
    if (_pythonPackages === null) {
      loadPythonPackages();
      wrap.appendChild(el('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', color: C.dim, fontSize: '0.75rem' } },
        '⟳ Loading packages…'));
      return wrap;
    }

    if (_pythonPackages.length === 0) {
      wrap.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim, fontStyle: 'italic', textAlign: 'center', padding: '8px' } },
        'No packages found'));
      return wrap;
    }

    // filter input
    const filterRow = el('div', { style: { marginBottom: '6px' } });
    const filterInput = el('input', { type: 'text', placeholder: 'Filter packages…', style: {
      width: '100%', fontSize: '0.7rem', border: `1px solid ${C.border}`, borderRadius: '4px',
      padding: '5px 8px', color: C.text, background: C.bg, outline: 'none', boxSizing: 'border-box',
    }});
    filterInput.value = _pythonPkgFilter;
    filterInput.oninput = () => { _pythonPkgFilter = filterInput.value; renderPkgList(); };
    filterRow.appendChild(filterInput);
    wrap.appendChild(filterRow);

    // package list container
    const listContainer = el('div', { style: { maxHeight: '200px', overflowY: 'auto' } });
    wrap.appendChild(listContainer);

    function renderPkgList() {
      listContainer.innerHTML = '';
      const filtered = _pythonPkgFilter
        ? _pythonPackages.filter(p => p.name.toLowerCase().includes(_pythonPkgFilter.toLowerCase()))
        : _pythonPackages;

      if (filtered.length === 0) {
        listContainer.appendChild(el('div', { style: { fontSize: '0.7rem', color: C.dim, fontStyle: 'italic', textAlign: 'center', padding: '8px' } },
          `No packages matching "${esc(_pythonPkgFilter)}"`));
        return;
      }

      filtered.forEach(pkg => {
        const row = el('div', { style: {
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '4px 6px', borderRadius: '4px', fontSize: '0.7rem',
          transition: 'background .1s',
        }});
        row.onmouseenter = () => { row.style.background = C.hover; };
        row.onmouseleave = () => { row.style.background = 'none'; };

        const left = el('div', { style: { display: 'flex', alignItems: 'center', gap: '6px', minWidth: '0', flex: '1' } });
        left.appendChild(el('span', { style: { color: C.text, fontFamily: 'monospace', fontSize: '11px' } }, esc(pkg.name)));
        left.appendChild(el('span', { style: { color: C.dim, fontSize: '10px' } }, esc(pkg.version)));
        row.appendChild(left);

        const rmBtn = el('button', { style: {
          fontSize: '10px', color: C.dim, background: 'none', border: 'none', cursor: 'pointer',
          padding: '2px 4px', borderRadius: '3px', opacity: '0', transition: 'opacity .15s',
        }}, '✗');
        row.onmouseenter = () => { row.style.background = C.hover; rmBtn.style.opacity = '1'; };
        row.onmouseleave = () => { row.style.background = 'none'; rmBtn.style.opacity = '0'; };
        rmBtn.onmouseenter = () => { rmBtn.style.color = C.red; };
        rmBtn.onmouseleave = () => { rmBtn.style.color = C.dim; };
        rmBtn.onclick = async () => {
          rmBtn.textContent = '⟳';
          await uninstallPythonPackage(pkg.name);
        };
        row.appendChild(rmBtn);

        listContainer.appendChild(row);
      });
    }

    renderPkgList();
    return wrap;
  }

  function configSection(tool) {
    const cfg = tool.config || {};

    // Python interpreter gets the packages panel
    if (tool.id === 'python_interpreter') {
      return pythonPackagesSection(tool);
    }

    const wrap = el('div', { style: { marginBottom: '12px' } });
    wrap.appendChild(el('div', { style: { fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: C.dim, fontWeight: '600', marginBottom: '8px' } }, 'Configuration'));

    if (tool.id === 'llm') {
      if (cfg.base_url) wrap.appendChild(configRow('Base URL', cfg.base_url, true));
      if (cfg.settings_path) wrap.appendChild(configRow('Settings', cfg.settings_path, true));
      const models = cfg.models || [];
      if (models.length) {
        wrap.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim, marginTop: '4px' } }, 'Models'));
        const badges = el('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' } });
        models.forEach(m => {
          const isMock = m.is_mock;
          badges.appendChild(el('span', { style: {
            fontSize: '10px', padding: '2px 8px', borderRadius: '4px', fontFamily: 'monospace',
            background: isMock ? C.yellow + '1a' : C.hover, color: isMock ? C.yellow : C.text,
          }}, esc(m.id) + (isMock ? ' (mock)' : '')));
        });
        wrap.appendChild(badges);
      }
    } else if (tool.id === 'file_system') {
      if (cfg.base_dir) wrap.appendChild(configRow('Base Dir', cfg.base_dir, true));
    } else if (tool.id === 'gim') {
      if (cfg.default_model) wrap.appendChild(configRow('Model', cfg.default_model, true));
      if (cfg.default_size)  wrap.appendChild(configRow('Size', cfg.default_size));
    } else if (tool.id === 'user_input') {
      const modes = cfg.modes || [];
      if (modes.length) {
        wrap.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim } }, 'Modes'));
        const badges = el('div', { style: { display: 'flex', gap: '4px', marginTop: '4px' } });
        modes.forEach(m => badges.appendChild(el('span', { style: { fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: C.hover, color: C.text } }, esc(m))));
        wrap.appendChild(badges);
      }
    } else {
      wrap.appendChild(el('div', { style: { fontSize: '0.75rem', color: C.dim, fontStyle: 'italic' } }, 'No additional configuration'));
    }

    return wrap;
  }

  // -- tester section ----------------------------------------------------
  function testerSection(tool) {
    const wrap = el('div', { style: { borderTop: `1px solid ${C.border}`, paddingTop: '12px' } });
    wrap.appendChild(el('div', { style: { fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: C.dim, fontWeight: '600', marginBottom: '8px' } }, 'Test Tool'));

    const inputStyle = {
      width: '100%', fontSize: '0.75rem', border: `1px solid ${C.border}`, borderRadius: '4px',
      padding: '6px 8px', color: C.text, background: C.bg, outline: 'none', fontFamily: 'monospace',
      boxSizing: 'border-box',
    };
    const labelStyle = { fontSize: '10px', color: C.dim, display: 'block', marginBottom: '4px' };

    const resultBox = el('div');

    // per-tool inputs
    let getParams;

    if (tool.id === 'llm') {
      const models = (tool.config.models || []);
      const select = el('select', { style: { ...inputStyle, fontFamily: 'inherit' } });
      models.forEach(m => { const o = el('option', { value: m.id }, esc(m.id)); select.appendChild(o); });
      if (models.find(m => m.id === 'demo')) select.value = 'demo';
      const textarea = el('textarea', { rows: '2', style: { ...inputStyle, resize: 'none', marginTop: '8px' } });
      textarea.value = 'Say hello in one sentence.';

      wrap.appendChild(el('div', { style: labelStyle }, 'Model'));
      wrap.appendChild(select);
      wrap.appendChild(el('div', { style: { ...labelStyle, marginTop: '8px' } }, 'Prompt'));
      wrap.appendChild(textarea);
      getParams = () => ({ url: `${API}/tools/llm/test`, body: { model: select.value, prompt: textarea.value } });

    } else if (tool.id === 'python_interpreter') {
      const textarea = el('textarea', { rows: '3', style: { ...inputStyle, resize: 'none' } });
      textarea.value = 'result = 2 + 2';
      wrap.appendChild(el('div', { style: labelStyle }, 'Python Code'));
      wrap.appendChild(textarea);
      getParams = () => ({ url: `${API}/tools/python/test`, body: { code: textarea.value } });

    } else if (tool.id === 'file_system') {
      const row = el('div', { style: { display: 'flex', gap: '8px' } });
      const select = el('select', { style: { ...inputStyle, width: '110px', fontFamily: 'inherit' } });
      ['list', 'read', 'exists'].forEach(op => { const o = el('option', { value: op }, op === 'list' ? 'List Dir' : op === 'read' ? 'Read File' : 'Exists'); select.appendChild(o); });
      const input = el('input', { type: 'text', value: '.', style: { ...inputStyle, flex: '1' } });
      const left = el('div', { style: { width: '110px' } }); left.appendChild(el('div', { style: labelStyle }, 'Operation')); left.appendChild(select);
      const right = el('div', { style: { flex: '1' } }); right.appendChild(el('div', { style: labelStyle }, 'Path')); right.appendChild(input);
      row.appendChild(left); row.appendChild(right);
      wrap.appendChild(row);
      getParams = () => ({ url: `${API}/tools/filesystem/test`, body: { operation: select.value, path: input.value } });

    } else if (tool.id === 'gim') {
      const input = el('input', { type: 'text', value: 'A simple blue square', style: inputStyle });
      wrap.appendChild(el('div', { style: labelStyle }, 'Image Prompt'));
      wrap.appendChild(input);
      wrap.appendChild(el('div', { style: { fontSize: '10px', color: C.dim, marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' } }, '⚠ Tests run in mock mode'));
      getParams = () => ({ url: `${API}/tools/gim/test`, body: { prompt: input.value, mock_mode: true } });
    } else {
      getParams = null;
    }

    if (!getParams) return wrap;

    // run button
    const runBtn = el('button', { style: {
      marginTop: '12px', display: 'flex', alignItems: 'center', gap: '6px',
      padding: '6px 12px', fontSize: '0.75rem', fontWeight: '500', borderRadius: '6px',
      background: '#238636', color: '#fff', border: 'none', cursor: 'pointer', transition: 'background .15s',
    }}, '▶ Run Test');
    runBtn.onmouseenter = () => { runBtn.style.background = '#2ea043'; };
    runBtn.onmouseleave = () => { runBtn.style.background = '#238636'; };

    runBtn.onclick = async () => {
      runBtn.disabled = true;
      runBtn.textContent = '⟳ Running…';
      runBtn.style.opacity = '0.6';
      resultBox.innerHTML = '';
      try {
        const { url, body } = getParams();
        const result = await postJson(url, body);
        renderResult(resultBox, result, tool.id);
      } catch (e) {
        renderResult(resultBox, { status: 'error', error: e.message }, tool.id);
      } finally {
        runBtn.disabled = false;
        runBtn.textContent = '▶ Run Test';
        runBtn.style.opacity = '1';
      }
    };

    wrap.appendChild(runBtn);
    wrap.appendChild(resultBox);
    return wrap;
  }

  // -- test result -------------------------------------------------------
  function renderResult(container, result, toolId) {
    const ok = result.status === 'success';
    const box = el('div', { style: {
      marginTop: '12px', borderRadius: '8px', padding: '12px',
      border: `1px solid ${ok ? C.green + '4d' : C.red + '4d'}`,
      background: ok ? C.green + '0d' : C.red + '0d',
    }});

    // status line
    const statusRow = el('div', { style: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' } });
    statusRow.appendChild(el('span', { style: { color: ok ? C.green : C.red, fontSize: '0.875rem' } }, ok ? '✓' : '✗'));
    statusRow.appendChild(el('span', { style: { fontSize: '0.75rem', fontWeight: '500', color: ok ? C.green : C.red } }, ok ? 'Test Passed' : 'Test Failed'));
    if (result.duration_ms != null) statusRow.appendChild(el('span', { style: { fontSize: '10px', color: C.dim, marginLeft: 'auto' } }, result.duration_ms + 'ms'));
    if (result.is_mock) statusRow.appendChild(el('span', { style: { fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: C.yellow + '1a', color: C.yellow } }, 'mock'));
    box.appendChild(statusRow);

    // output
    let content = '';
    if (ok) {
      content = toolId === 'llm' ? (result.response || '') : JSON.stringify(result.result, null, 2);
    } else {
      content = result.error || 'Unknown error';
    }
    box.appendChild(el('pre', { style: {
      fontSize: '0.75rem', fontFamily: 'monospace', color: C.text, background: C.bg,
      borderRadius: '4px', padding: '8px', maxHeight: '192px', overflow: 'auto',
      whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: '0',
    }}, esc(content)));

    // stats
    if (result.stats) {
      const statsRow = el('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' } });
      Object.entries(result.stats).forEach(([k, v]) => {
        statsRow.appendChild(el('span', { style: { fontSize: '10px', color: C.dim, padding: '2px 6px', background: C.hover, borderRadius: '4px' } }, `${k}: ${v}`));
      });
      box.appendChild(statsRow);
    }

    container.innerHTML = '';
    container.appendChild(box);
  }

  // -- expose ------------------------------------------------------------
  window.ToolsPanel = { mount, refresh: loadTools };
})();
