/**
 * i18n — Shared internationalization engine
 * 
 * Usage:
 *   1. Include this script on every page
 *   2. Each page defines `window.pageTranslations = { en: {...}, zh: {...} }`
 *   3. Call `i18n.init()` after defining translations
 * 
 * Translation keys are resolved via `data-i18n` attributes:
 *   <span data-i18n="hero.title">Fallback text</span>
 * 
 * For HTML content use `data-i18n-html`:
 *   <p data-i18n-html="section.richText">Fallback <strong>HTML</strong></p>
 * 
 * For title/tooltip: `data-i18n-title`
 * For alt text: `data-i18n-alt`
 */

const i18n = (function () {
    'use strict';

    let _translations = {};
    let _currentLang = localStorage.getItem('lang') || 'zh';

    /**
     * Resolve a dot-notation key against a translation object
     * e.g. resolve('hero.title', { hero: { title: 'Hello' } }) → 'Hello'
     */
    function resolve(key, obj) {
        const keys = key.split('.');
        let value = obj;
        for (const k of keys) {
            value = value?.[k];
        }
        return value;
    }

    /**
     * Apply all translations to the current DOM
     */
    function applyTranslations(lang) {
        const t = _translations[lang];
        if (!t) return;

        // data-i18n → textContent (or innerHTML if contains HTML tags)
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const value = resolve(el.getAttribute('data-i18n'), t);
            if (value === undefined) return;

            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.value = value;
            } else if (/<[a-z][\s\S]*>/i.test(value)) {
                el.innerHTML = value;
            } else {
                el.textContent = value;
            }
        });

        // data-i18n-html → always innerHTML
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const value = resolve(el.getAttribute('data-i18n-html'), t);
            if (value !== undefined) {
                el.innerHTML = value;
            }
        });

        // data-i18n-title → tooltip
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const value = resolve(el.getAttribute('data-i18n-title'), t);
            if (value !== undefined) {
                el.title = value;
            }
        });

        // data-i18n-alt → alt text
        document.querySelectorAll('[data-i18n-alt]').forEach(el => {
            const value = resolve(el.getAttribute('data-i18n-alt'), t);
            if (value !== undefined) {
                el.alt = value;
            }
        });

        // Update lang button active states
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
        });
    }

    /**
     * Set language and persist
     */
    function setLanguage(lang) {
        _currentLang = lang;
        localStorage.setItem('lang', lang);
        document.documentElement.lang = lang;
        applyTranslations(lang);
    }

    /**
     * Initialize i18n system
     * @param {Object} translations - { en: {...}, zh: {...} }
     */
    function init(translations) {
        _translations = translations || {};
        _currentLang = localStorage.getItem('lang') || 'zh';
        document.documentElement.lang = _currentLang;
        applyTranslations(_currentLang);
    }

    /**
     * Deep-merge source into target (mutates target)
     */
    function deepMerge(target, source) {
        for (const key of Object.keys(source)) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                if (!target[key]) target[key] = {};
                deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        }
        return target;
    }

    /**
     * Extend existing translations and re-apply
     * @param {Object} extra - { en: {...}, zh: {...} }
     */
    function extend(extra) {
        deepMerge(_translations, extra || {});
        applyTranslations(_currentLang);
    }

    /**
     * Get current language
     */
    function getLang() {
        return _currentLang;
    }

    // Expose globally for nav.js language switcher
    window.setLanguage = setLanguage;

    return { init, extend, setLanguage, getLang, resolve };
})();

