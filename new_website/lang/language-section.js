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
            filename: 'batch_summarization.ncds',
            codeExample: ''
                + '<span class="line-num">1</span><span class="keyword">&lt;-</span> <span class="variable">all summaries</span>\n'
                + '<span class="line-num">1.1</span>    <span class="keyword">&lt;=</span> <span class="function">for every document in the list return the document summary</span>\n'
                + '<span class="line-num">1.1.1</span>        <span class="keyword">&lt;=</span> <span class="function">select document summary to return</span>\n'
                + '<span class="line-num">1.1.2</span>        <span class="keyword">&lt;-</span> <span class="variable">document summary</span>\n'
                + '<span class="line-num">1.1.2.1</span>            <span class="keyword">&lt;=</span> <span class="function">summarize this document</span>\n'
                + '<span class="line-num">1.1.2.2</span>            <span class="keyword">&lt;-</span> <span class="string">document to process now</span>\n'
                + '<span class="line-num">1.2</span>    <span class="keyword">&lt;-</span> <span class="string">documents</span>\n'
                + '<span class="line-num">1.3</span>    <span class="keyword">&lt;*</span> <span class="string">document to process now</span>',

            /* ── Aha explanation ── */
            aha: 'That\'s a complete AI agent workflow. <strong>8 lines of NormCode.</strong> '
                + 'Executes inside-out, top-to-bottom: summarize each document → select the summary → collect all results.'
                + '<br><br>'
                + '<strong>Indentation = what each step can see.</strong> '
                + 'The summarize step sees only the current document. The select step sees only the document summary — nothing else. '
                + '<code>&lt;*</code> drives the loop, iterating over each document in the collection.',

            /* ── Flow indices explanation ── */
            flowIndices: '<strong>Flow indices</strong> — the numbers on the left (<code>1</code>, <code>1.1</code>, <code>1.1.2</code>…) give every step a unique address. '
                + 'The rule is simple: each new indentation level starts a fresh counter. '
                + 'The action (<code>&lt;=</code>) is always <code>.1</code> under its parent; '
                + 'value inputs (<code>&lt;-</code>) and timing states (<code>&lt;*</code>) are siblings <code>.2</code>, <code>.3</code>, <code>.4</code> and so on. '
                + 'So <code>1.1.2.1</code> means: root <code>1</code> → first action <code>.1</code> → second input <code>.2</code> → its action <code>.1</code>.'
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
            filename: '批量摘要.ncds',
            codeExample: ''
                + '<span class="line-num">1</span><span class="keyword">&lt;-</span> <span class="variable">所有摘要</span>\n'
                + '<span class="line-num">1.1</span>    <span class="keyword">&lt;=</span> <span class="function">对列表中的每个文档返回文档摘要</span>\n'
                + '<span class="line-num">1.1.1</span>        <span class="keyword">&lt;=</span> <span class="function">选择要返回的文档摘要</span>\n'
                + '<span class="line-num">1.1.2</span>        <span class="keyword">&lt;-</span> <span class="variable">文档摘要</span>\n'
                + '<span class="line-num">1.1.2.1</span>            <span class="keyword">&lt;=</span> <span class="function">总结此文档</span>\n'
                + '<span class="line-num">1.1.2.2</span>            <span class="keyword">&lt;-</span> <span class="string">当前处理的文档</span>\n'
                + '<span class="line-num">1.2</span>    <span class="keyword">&lt;-</span> <span class="string">文档列表</span>\n'
                + '<span class="line-num">1.3</span>    <span class="keyword">&lt;*</span> <span class="string">当前处理的文档</span>',

            /* ── Aha 解释 ── */
            aha: '这就是一个完整的AI智能体工作计划。<strong>8行诺码。</strong>'
                + '从内到外、从上到下执行：总结每个文档 → 选择摘要 → 收集所有结果。'
                + '<br><br>'
                + '<strong>缩进 = 每个步骤能看到什么。</strong>'
                + '总结步骤只能看到当前处理的文档。选择步骤只能看到文档摘要——仅此而已。<code>&lt;*</code> 标记驱动循环，遍历集合中的每个文档。',

            /* ── 流程索引解释 ── */
            flowIndices: '<strong>流程索引</strong>——左侧的编号（<code>1</code>、<code>1.1</code>、<code>1.1.2</code>…）为每个步骤提供唯一地址。'
                + '规则很简单：每个新的缩进层级启动一个新的计数器。'
                + '功能概念（<code>&lt;=</code>）在其父级下始终是 <code>.1</code>；'
                + '值输入（<code>&lt;-</code>）和时序状态（<code>&lt;*</code>）是同级的 <code>.2</code>、<code>.3</code>、<code>.4</code> 等。'
                + '因此 <code>1.1.2.1</code> 表示：根节点 <code>1</code> → 第一个动作 <code>.1</code> → 第二个输入 <code>.2</code> → 它的动作 <code>.1</code>。'
        }
    }
});
