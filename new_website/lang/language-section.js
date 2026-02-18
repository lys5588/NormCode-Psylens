/**
 * "Three symbols" tutorial section — translations (EN + ZH)
 *
 * Loaded after lang/index.js on the homepage.
 * Uses i18n.extend() so it can be edited independently.
 */

i18n.extend({
    en: {
        language: {
            title: 'Three symbols. Plain language. That\'s the whole syntax.',

            /* ── Left annotations: the 3 symbols ── */
            sym1meaning: 'This is content',
            sym1hint:    'Data, documents, results — the nouns flowing through the workflow.',
            sym2meaning: 'This is an action',
            sym2hint:    'Operations the AI performs — extract, check, generate.',
            sym3meaning: 'Loop / timing state',
            sym3hint:    'Repeat, wait, branch on conditions.',

            /* ── Right annotations: structural concepts ── */
            indentLabel: 'Indentation = scope',
            indentHint:  'Each step sees only the data indented beneath it. No global context. No data leaking between steps.',
            readLabel:   'Inside-out, top-down',
            readHint:    'Deepest indentation runs first, then upward. Within the same level, top to bottom.',

            /* ── Code block ── */
            everything: 'Everything else you write is natural language.',
            filename: 'document_analysis.ncds',
            codeExample: ''
                + '<span class="line-num">1</span><span class="keyword">&lt;-</span> <span class="variable">executive summary</span>\n'
                + '<span class="line-num">2</span>    <span class="keyword">&lt;=</span> <span class="function">generate summary from flagged items</span>\n'
                + '<span class="line-num">3</span>    <span class="keyword">&lt;-</span> <span class="variable">discrepancy flags</span>\n'
                + '<span class="line-num">4</span>        <span class="keyword">&lt;=</span> <span class="function">check for mismatches</span>\n'
                + '<span class="line-num">5</span>        <span class="keyword">&lt;-</span> <span class="variable">extracted figures</span>\n'
                + '<span class="line-num">6</span>            <span class="keyword">&lt;=</span> <span class="function">extract financial data</span>\n'
                + '<span class="line-num">7</span>            <span class="keyword">&lt;-</span> <span class="string">raw document</span>\n'
                + '<span class="line-num">8</span>        <span class="keyword">&lt;-</span> <span class="string">database results</span>',

            /* ── Aha explanation ── */
            aha: 'That\'s a complete AI agent workflow. <strong>7 lines of NormCode.</strong> '
                + 'Executes inside-out, top-to-bottom: extract data from the document → check for mismatches → summarize the flags.'
                + '<br><br>'
                + '<strong>Indentation = what each step can see.</strong> '
                + 'The extraction step sees only the raw document. The mismatch check sees extracted figures + database results — nothing else. '
                + 'No global context. No data leaking between steps.'
        }
    },
    zh: {
        language: {
            title: '三个符号。自然语言。这就是全部语法。',

            /* ── 左侧标注：3个符号 ── */
            sym1meaning: '这是内容',
            sym1hint:    '数据、文档、结果——流经工作流的名词。',
            sym2meaning: '这是动作',
            sym2hint:    'AI执行的操作——提取、检查、生成。',
            sym3meaning: '循环 / 时序状态',
            sym3hint:    '重复、等待、条件分支。',

            /* ── 右侧标注：结构概念 ── */
            indentLabel: '缩进 = 作用域',
            indentHint:  '每个步骤只能看到其缩进内的数据。没有全局上下文，步骤间没有数据泄漏。',
            readLabel:   '从内到外，从上到下',
            readHint:    '最深缩进先执行，再向外层推进。同一层级内从上到下执行。',

            /* ── 代码块 ── */
            everything: '其他所有内容都用自然语言编写。',
            filename: '文档分析.ncds',
            codeExample: ''
                + '<span class="line-num">1</span><span class="keyword">&lt;-</span> <span class="variable">执行摘要</span>\n'
                + '<span class="line-num">2</span>    <span class="keyword">&lt;=</span> <span class="function">根据标记项生成摘要</span>\n'
                + '<span class="line-num">3</span>    <span class="keyword">&lt;-</span> <span class="variable">差异标记</span>\n'
                + '<span class="line-num">4</span>        <span class="keyword">&lt;=</span> <span class="function">检查不匹配项</span>\n'
                + '<span class="line-num">5</span>        <span class="keyword">&lt;-</span> <span class="variable">提取的数据</span>\n'
                + '<span class="line-num">6</span>            <span class="keyword">&lt;=</span> <span class="function">提取财务数据</span>\n'
                + '<span class="line-num">7</span>            <span class="keyword">&lt;-</span> <span class="string">原始文档</span>\n'
                + '<span class="line-num">8</span>        <span class="keyword">&lt;-</span> <span class="string">数据库结果</span>',

            /* ── Aha 解释 ── */
            aha: '这就是一个完整的AI智能体工作计划。<strong>7行诺码。</strong>'
                + '从内到外、从上到下执行：从文档中提取数据 → 检查不匹配 → 汇总标记。'
                + '<br><br>'
                + '<strong>缩进 = 每个步骤能看到什么。</strong>'
                + '提取步骤只能看到原始文档。不匹配检查看到提取的数据 + 数据库结果——仅此而已。没有全局上下文。步骤之间没有数据泄漏。'
        }
    }
});
