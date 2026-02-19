/**
 * docs-common.js — Shared translations for all documentation pages
 * 
 * Provides nav, sidebar, and footer translations that are identical
 * across all docs pages, plus a helper to merge page-specific translations.
 * 
 * Usage:
 *   <script src="../js/docs-common.js"></script>
 *   <script>
 *       initDocsPage({
 *           en: { page: {...}, section: {...}, ... },
 *           zh: { page: {...}, section: {...}, ... }
 *       });
 *   </script>
 */

const docsCommonTranslations = {
    en: {
        nav: {
            companyName: 'Psylens.AI',
            brandText: 'Psylens.AI',
            home: 'Home',
            docs: 'Documentation',
            overview: 'Overview',
            syntax: 'Syntax Reference',
            execution: 'Execution Model',
            compilation: 'Compilation',
            examples: 'Examples',
            demo: 'Demo',
            team: 'Team',
            about: 'About',
            backDocs: 'Back to Documentation',
            backHome: 'Back to Home'
        },
        sidebar: {
            title: 'Documentation'
        },
        footer: {
            paper: 'Research Paper',
            tagline: 'Structured AI Planning That You Can Audit',
            contact: 'Contact',
            office: 'TIMETABLE GBA Youth Innovation Base, Nansha, Guangzhou'
        }
    },
    zh: {
        nav: {
            companyName: '心镜智',
            brandText: '心镜智',
            home: '首页',
            docs: '文档',
            overview: '概述',
            syntax: '语法参考',
            execution: '执行模型',
            compilation: '编译流程',
            examples: '示例',
            demo: '演示',
            team: '团队',
            about: '关于',
            backDocs: '返回文档',
            backHome: '返回首页'
        },
        sidebar: {
            title: '文档'
        },
        footer: {
            paper: '研究论文',
            tagline: '可审计的结构化AI规划',
            contact: '联系我们',
            office: '广州市南沙区黄阁镇海滨路创享湾4栋TIMETABLE粤港澳青创基地'
        }
    }
};

/**
 * Deep-merge two objects (source wins on conflict)
 */
function _deepMerge(target, source) {
    for (const key of Object.keys(source)) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            if (!target[key]) target[key] = {};
            _deepMerge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

/**
 * Initialize a docs page with shared + page-specific translations.
 * Page-specific keys override shared keys if they collide.
 * 
 * @param {Object} pageTranslations - { en: {...}, zh: {...} }
 */
function initDocsPage(pageTranslations) {
    // Clone shared translations so we don't mutate the original
    const merged = JSON.parse(JSON.stringify(docsCommonTranslations));

    // Deep-merge page-specific translations on top
    if (pageTranslations) {
        for (const lang of Object.keys(pageTranslations)) {
            if (!merged[lang]) merged[lang] = {};
            _deepMerge(merged[lang], pageTranslations[lang]);
        }
    }

    i18n.init(merged);
}

