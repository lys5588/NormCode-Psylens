/**
 * Hero example rotation — Homepage only
 *
 * Cycles through 3 NormCode examples in the hero section,
 * updating the instruction text, code editor, and graph SVG.
 * Supports EN/ZH via i18n.getLang().
 */

(function () {
    'use strict';

    /* ── Example data ──────────────────────────────────────────── */
    var examples = [
        {
            instruction: {
                en: 'Read the uploaded file and create a report. Then summarize the findings using the report and a style guide.',
                zh: '读取上传的文件并创建报告。然后使用报告和风格指南总结发现。'
            },
            filename: 'summary.ncds',
            code: {
                en: [
                    '<span class="nc-kw">:&lt;:</span> summary',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> summarize the findings',
                    '    <span class="nc-dep">&lt;-</span> report',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-in">:&gt;</span><span class="nc-ann">(file):</span> read the uploaded file',
                    '    <span class="nc-dep">&lt;-</span> style guide'
                ],
                zh: [
                    '<span class="nc-kw">:&lt;:</span> 总结',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> 总结发现',
                    '    <span class="nc-dep">&lt;-</span> 报告',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-in">:&gt;</span><span class="nc-ann">(文件):</span> 读取上传的文件',
                    '    <span class="nc-dep">&lt;-</span> 风格指南'
                ]
            },
            graph: {
                en: { action1: 'read the uploaded file', data1: 'report', data2: 'style guide', action2: 'summarize the findings', output: 'summary' },
                zh: { action1: '读取上传的文件', data1: '报告', data2: '风格指南', action2: '总结发现', output: '总结' }
            }
        },
        {
            instruction: {
                en: 'Search for recent papers on the topic. Extract key findings from each and write a literature review.',
                zh: '搜索该主题的最新论文。从每篇论文中提取关键发现并撰写文献综述。'
            },
            filename: 'review.ncds',
            code: {
                en: [
                    '<span class="nc-kw">:&lt;:</span> review',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> write the review',
                    '    <span class="nc-dep">&lt;-</span> papers',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-in">:&gt;</span><span class="nc-ann">(search):</span> search for papers',
                    '    <span class="nc-dep">&lt;-</span> topic brief'
                ],
                zh: [
                    '<span class="nc-kw">:&lt;:</span> 综述',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> 撰写综述',
                    '    <span class="nc-dep">&lt;-</span> 论文',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-in">:&gt;</span><span class="nc-ann">(搜索):</span> 搜索论文',
                    '    <span class="nc-dep">&lt;-</span> 主题简介'
                ]
            },
            graph: {
                en: { action1: 'search for papers', data1: 'papers', data2: 'topic brief', action2: 'write the review', output: 'review' },
                zh: { action1: '搜索论文', data1: '论文', data2: '主题简介', action2: '撰写综述', output: '综述' }
            }
        },
        {
            instruction: {
                en: 'Analyze customer feedback for sentiment. Combine with sales data to generate product suggestions.',
                zh: '分析客户反馈的情感倾向。结合销售数据生成产品建议。'
            },
            filename: 'product.ncds',
            code: {
                en: [
                    '<span class="nc-kw">:&lt;:</span> suggestions',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> generate suggestions',
                    '    <span class="nc-dep">&lt;-</span> feedback',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> analyze sentiment',
                    '    <span class="nc-dep">&lt;-</span> sales data'
                ],
                zh: [
                    '<span class="nc-kw">:&lt;:</span> 建议',
                    '    <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> 生成建议',
                    '    <span class="nc-dep">&lt;-</span> 反馈',
                    '        <span class="nc-dep">&lt;=</span> <span class="nc-fn">::</span> 分析情感',
                    '    <span class="nc-dep">&lt;-</span> 销售数据'
                ]
            },
            graph: {
                en: { action1: 'analyze sentiment', data1: 'feedback', data2: 'sales data', action2: 'generate suggestions', output: 'suggestions' },
                zh: { action1: '分析情感', data1: '反馈', data2: '销售数据', action2: '生成建议', output: '建议' }
            }
        }
    ];

    /* ── DOM refs ─────────────────────────────────────────────── */
    var splitEl   = document.querySelector('.hero-visual-split');
    var instrEl   = document.getElementById('hero-instruction-text');
    var codeEl    = document.getElementById('hero-code-pre');
    var fileEl    = document.getElementById('hero-code-filename');
    var dots      = document.querySelectorAll('.hero-dot');
    var visualEl  = document.querySelector('.hero-visual');
    var graphEls  = {
        action1: document.getElementById('graph-action1'),
        data1:   document.getElementById('graph-data1'),
        data2:   document.getElementById('graph-data2'),
        action2: document.getElementById('graph-action2'),
        output:  document.getElementById('graph-output')
    };

    /* ── State ────────────────────────────────────────────────── */
    var currentIdx      = 0;
    var intervalId      = null;
    var isTransitioning = false;
    var INTERVAL        = 6000;  // ms between rotations
    var FADE_MS         = 420;   // fade-out duration

    /* ── Helpers ──────────────────────────────────────────────── */
    function getLang() {
        return (typeof i18n !== 'undefined' && i18n.getLang) ? i18n.getLang() : 'en';
    }

    function applyExample(idx) {
        var ex   = examples[idx];
        var lang = getLang();

        // Instruction text
        instrEl.textContent = ex.instruction[lang] || ex.instruction.en;

        // Code editor (language-aware)
        var codeLines = ex.code[lang] || ex.code.en;
        codeEl.innerHTML = codeLines.join('\n');
        fileEl.textContent = ex.filename;

        // Graph SVG labels (language-aware)
        var graphLabels = ex.graph[lang] || ex.graph.en;
        for (var key in graphLabels) {
            if (graphEls[key]) graphEls[key].textContent = graphLabels[key];
        }

        // Dots
        dots.forEach(function (d, i) {
            d.classList.toggle('active', i === idx);
        });
    }

    function goTo(idx) {
        if (idx === currentIdx || isTransitioning) return;
        isTransitioning = true;
        splitEl.classList.add('transitioning');

        setTimeout(function () {
            currentIdx = idx;
            applyExample(idx);
            splitEl.classList.remove('transitioning');
            isTransitioning = false;
        }, FADE_MS);
    }

    function next() {
        goTo((currentIdx + 1) % examples.length);
    }

    function startRotation() { intervalId = setInterval(next, INTERVAL); }
    function stopRotation()  { clearInterval(intervalId); }

    /* ── Dot click handlers ───────────────────────────────────── */
    dots.forEach(function (dot, i) {
        dot.addEventListener('click', function () {
            stopRotation();
            goTo(i);
            startRotation();
        });
    });

    /* ── Pause on hover ───────────────────────────────────────── */
    if (visualEl) {
        visualEl.addEventListener('mouseenter', stopRotation);
        visualEl.addEventListener('mouseleave', startRotation);
    }

    /* ── Language change hook ─────────────────────────────────── */
    var _origSetLang = window.setLanguage;
    window.setLanguage = function (lang) {
        _origSetLang(lang);
        applyExample(currentIdx);          // refresh instruction text
    };

    /* ── Respect reduced-motion ───────────────────────────────── */
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        FADE_MS = 0;
    }

    /* ── Start ────────────────────────────────────────────────── */
    applyExample(0);   // apply correct language for code + graph on load
    startRotation();
})();

