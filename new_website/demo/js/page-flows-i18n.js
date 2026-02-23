/**
 * Page-Flows Internationalization Module
 *
 * Handles translations for the page-flows wizard interface.
 * Supports English (en) and Chinese (zh) languages.
 */

// ---- i18n initialization ----
i18n.init({
    en: {
        nav: { brandText: 'Psylens.AI', home: 'Home', docs: 'Documentation', overview: 'Overview', syntax: 'Syntax Reference', execution: 'Execution Model', compilation: 'Compilation', examples: 'Examples', demo: 'Demo', about: 'About', features: 'Features' },
        footer: { tagline: 'Structured AI Planning That You Can Audit', paper: 'Research Paper', contact: 'Contact', office: 'TIMETABLE GBA Youth Innovation Base, Nansha, Guangzhou' },
        pf: {
            s0title: 'Connection', s0sub: 'Verifying server and loading configuration...',
            s1title: 'Basic Inputs', s1sub: 'What should this presentation be about?',
            s2title: 'Content Files', s2sub: 'Add content reference files (optional).',
            s3title: 'HTML Templates', s3sub: 'Add HTML slide templates (optional).',
            s4title: 'Style Guides', s4sub: 'Add CSS or text style guides (optional).',
            s5title: 'Review & Launch', s5sub: 'Confirm your settings and start generation.',
            s6title: 'Running',
            labelServer: 'Server', labelPlan: 'Plan', labelModel: 'Model',
            connecting: 'Connecting...', connected: 'Connected successfully', connFailed: 'Connection failed: ',
            labelTopic: 'Topic <span class="pf-required">*</span>', labelAudience: 'Audience', labelLength: 'Length',
            phTopic: 'e.g. Machine Learning Basics', phAudience: 'e.g. Technical beginners', phLength: 'e.g. 6 slides including title and Q&A',
            refContent: 'Content Files', refTemplate: 'HTML Templates', refStyle: 'Style Guides',
            dropContent: '+ Add .md, .txt, .json, .pdf, .docx, .pptx, .xlsx', dropTemplate: '+ Add .html', dropStyle: '+ Add .css, .md, .txt',
            convertTitle: 'Convert to Plain Text?', convertMsg: 'These files will be converted to plain text. Formatting, images, charts, and layout will be lost. Only the extracted text will be used as reference content.', convertProceed: 'Convert & Add', convertCancel: 'Cancel',
            reviewTopic: 'Topic', reviewAudience: 'Audience', reviewLength: 'Length',
            reviewContent: 'Content refs', reviewTemplate: 'Templates', reviewStyle: 'Style guides', reviewModel: 'Model',
            nFiles: ' file(s)',
            launch: 'Launch', uploading: 'Uploading files...', starting: 'Starting run...',
            launchFailed: 'Launch failed: ',
            runSub: 'Generating your presentation...', runWaiting: 'Waiting...', runPlaceholder: 'Event monitor coming soon',
            runStarted: 'Run started: ', runCompleted: 'Completed!', runCompletedSub: 'Generation finished successfully.',
            runFailed: 'Failed: ', inferences: ' inferences',
            preview: 'Preview', previewFailed: 'Preview failed: ',
            changeModel: 'change', mock: 'mock',
            labelLlm: 'Model Link', labelFiles: 'File System', labelPython: 'Code',
            testing: 'testing...', testPass: 'pass', testFail: 'fail',
            rendered: 'Rendered', source: 'Source',
            timelineTitle: 'Steps', filesTitle: 'Files',
            finalOutputs: 'Final Outputs', intermediateFiles: 'Intermediate',
            noFiles: 'Files will appear here...', download: 'Download',
            loopIter: 'iter', seconds: 's',
            back: '\u2190 Back', next: 'Next \u2192'
        }
    },
    zh: {
        nav: { brandText: '心镜智', home: '首页', docs: '文档', overview: '概述', syntax: '语法参考', execution: '执行模型', compilation: '编译流程', examples: '示例', demo: '演示', about: '关于', features: '功能' },
        footer: { tagline: '可审计的结构化AI规划', paper: '研究论文', contact: '联系我们', office: '广州市南沙区黄阁镇海滨路创享湾4栋TIMETABLE粤港澳青创基地' },
        pf: {
            s0title: '连接', s0sub: '正在验证服务器并加载配置...',
            s1title: '基本输入', s1sub: '这个演示文稿应该关于什么？',
            s2title: '内容文件', s2sub: '添加内容参考文件（可选）。',
            s3title: 'HTML 模板', s3sub: '添加HTML幻灯片模板（可选）。',
            s4title: '样式指南', s4sub: '添加CSS或文字样式指南（可选）。',
            s5title: '确认并启动', s5sub: '确认设置并开始生成。',
            s6title: '运行中',
            labelServer: '服务器', labelPlan: '计划', labelModel: '模型',
            connecting: '正在连接...', connected: '连接成功', connFailed: '连接失败：',
            labelTopic: '主题 <span class="pf-required">*</span>', labelAudience: '目标受众', labelLength: '期望长度',
            phTopic: '例如：机器学习基础', phAudience: '例如：技术初学者', phLength: '例如：6张幻灯片（含标题和问答）',
            refContent: '内容文件', refTemplate: 'HTML 模板', refStyle: '样式指南',
            dropContent: '+ 添加 .md, .txt, .json, .pdf, .docx, .pptx, .xlsx', dropTemplate: '+ 添加 .html', dropStyle: '+ 添加 .css, .md, .txt',
            convertTitle: '转换为纯文本？', convertMsg: '这些文件将被转换为纯文本。格式、图片、图表和布局将会丢失，仅提取文本内容作为参考材料。', convertProceed: '转换并添加', convertCancel: '取消',
            reviewTopic: '主题', reviewAudience: '受众', reviewLength: '长度',
            reviewContent: '内容引用', reviewTemplate: '模板', reviewStyle: '样式指南', reviewModel: '模型',
            nFiles: ' 个文件',
            launch: '启动生成', uploading: '正在上传文件...', starting: '正在启动运行...',
            launchFailed: '启动失败：',
            runSub: '正在生成演示文稿...', runWaiting: '等待中...', runPlaceholder: '事件监视器即将上线',
            runStarted: '运行已启动：', runCompleted: '已完成！', runCompletedSub: '生成已成功完成。',
            runFailed: '失败：', inferences: ' 次推理',
            preview: '预览', previewFailed: '预览失败：',
            changeModel: '更换', mock: '模拟',
            labelLlm: '模型链接', labelFiles: '文件系统', labelPython: '代码',
            testing: '检测中...', testPass: '通过', testFail: '失败',
            rendered: '渲染视图', source: '源代码',
            timelineTitle: '步骤', filesTitle: '文件',
            finalOutputs: '最终输出', intermediateFiles: '中间文件',
            noFiles: '文件将在此显示...', download: '下载',
            loopIter: '轮', seconds: '秒',
            back: '\u2190 返回', next: '下一步 \u2192'
        }
    }
});

// ---- Runtime translation helper ----
/**
 * Runtime translation function for dynamic strings
 * @param {string} key - Translation key
 * @returns {string} Translated string or key if not found
 */
function t(key) {
    const lang = i18n.getLang();
    const en = { phTopic: 'e.g. Machine Learning Basics', phAudience: 'e.g. Technical beginners', phLength: 'e.g. 6 slides including title and Q&A', connecting: 'Connecting...', connected: 'Connected successfully', connFailed: 'Connection failed: ', reviewTopic: 'Topic', reviewAudience: 'Audience', reviewLength: 'Length', reviewContent: 'Content refs', reviewTemplate: 'Templates', reviewStyle: 'Style guides', reviewModel: 'Model', nFiles: ' file(s)', launch: 'Launch', uploading: 'Uploading files...', starting: 'Starting run...', launchFailed: 'Launch failed: ', runStarted: 'Run started: ', runCompleted: 'Completed!', runCompletedSub: 'Generation finished successfully.', runFailed: 'Failed: ', inferences: ' inferences', preview: 'Preview', previewFailed: 'Preview failed: ', changeModel: 'change', mock: 'mock', testing: 'testing...', testPass: 'pass', testFail: 'fail', timelineTitle: 'Steps', filesTitle: 'Files', finalOutputs: 'Final Outputs', intermediateFiles: 'Intermediate', noFiles: 'Files will appear here...', download: 'Download', loopIter: 'iter', seconds: 's', rendered: 'Rendered', source: 'Source', converting: 'Converting', convertFailed: 'Conversion failed \u2014 ', legacyFormat: 'Legacy formats (.doc, .ppt, .xls) are not supported.\nPlease save as .docx, .pptx, or .xlsx.' };
    const zh = { phTopic: '例如：机器学习基础', phAudience: '例如：技术初学者', phLength: '例如：6张幻灯片（含标题和问答）', connecting: '正在连接...', connected: '连接成功', connFailed: '连接失败：', reviewTopic: '主题', reviewAudience: '受众', reviewLength: '长度', reviewContent: '内容引用', reviewTemplate: '模板', reviewStyle: '样式指南', reviewModel: '模型', nFiles: ' 个文件', launch: '启动生成', uploading: '正在上传文件...', starting: '正在启动运行...', launchFailed: '启动失败：', runStarted: '运行已启动：', runCompleted: '已完成！', runCompletedSub: '生成已成功完成。', runFailed: '失败：', inferences: ' 次推理', preview: '预览', previewFailed: '预览失败：', changeModel: '更换', mock: '模拟', testing: '检测中...', testPass: '通过', testFail: '失败', timelineTitle: '步骤', filesTitle: '文件', finalOutputs: '最终输出', intermediateFiles: '中间文件', noFiles: '文件将在此显示...', download: '下载', loopIter: '轮', seconds: '秒', rendered: '渲染视图', source: '源代码', converting: '正在转换', convertFailed: '转换失败 \u2014 ', legacyFormat: '不支持旧版格式（.doc、.ppt、.xls）。\n请保存为 .docx、.pptx 或 .xlsx。' };
    return (lang === 'zh' ? zh : en)[key] || en[key] || key;
}

/**
 * Apply translated placeholders to form fields
 */
function applyPlaceholders() {
    document.getElementById('pfTopic').placeholder = t('phTopic');
    document.getElementById('pfAudience').placeholder = t('phAudience');
    document.getElementById('pfLength').placeholder = t('phLength');
}

// Apply placeholders initially
applyPlaceholders();

// Re-apply placeholders when language changes
const _origSetLang = window.setLanguage;
window.setLanguage = function(lang) {
    _origSetLang(lang);
    applyPlaceholders();
};
