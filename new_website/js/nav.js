/**
 * Navigation — Shared navigation component
 * 
 * Generates the nav bar, handles mobile menu, dropdown, and language switching.
 * Include this script on every page AFTER i18n.js.
 */

(function () {
    'use strict';

    const storedLang = localStorage.getItem('lang') || 'en';

    // ---- Path helpers ----

    function getBasePath() {
        const path = window.location.pathname;
        if (path.includes('/docs/') || path.includes('/demo/')) {
            return '../';
        }
        return '';
    }

    function isHomePage() {
        const path = window.location.pathname;
        if (path.includes('/demo/') || path.includes('/docs/')) return false;
        return path.endsWith('/') ||
            path.endsWith('/index.html') ||
            path.endsWith('/new_website/') ||
            path.endsWith('/new_website/index.html');
    }

    function getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('/docs/')) {
            const filename = path.split('/').pop();
            return filename.replace('.html', '');
        }
        if (path.includes('/demo/')) return 'demo';
        if (path.includes('about.html')) return 'about';
        return 'home';
    }

    // ---- Generate nav HTML ----

    function generateNavHTML() {
        const base = getBasePath();
        const page = getCurrentPage();
        const isHome = isHomePage();

        const docsActive = ['overview', 'execution', 'compilation', 'syntax', 'examples', 'index'].includes(page) && window.location.pathname.includes('/docs/') ? 'active' : '';
        const demoActive = page === 'demo' ? 'active' : '';
        const aboutActive = page === 'about' ? 'active' : '';

        const homeLink = isHome ? '#features' : (base + 'index.html');

        return `
            <nav class="site-nav">
                <div class="nav-inner">
                    <a href="${base}index.html" class="nav-brand">
                        <img src="${base}assets/images/logo.png" alt="Psylens.AI" loading="eager">
                        <span class="nav-brand-text" data-i18n="nav.brandText">Psylens.AI</span>
                    </a>
                    <button class="menu-toggle" aria-label="Toggle navigation menu">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                    <div class="nav-links">
                        ${isHome
                ? '<a href="#features" data-i18n="nav.features">Features</a>'
                : `<a href="${homeLink}" data-i18n="nav.home">Home</a>`
            }
                        <div class="nav-dropdown">
                            <button class="nav-dropdown-trigger ${docsActive}" data-i18n="nav.docs">
                                Documentation
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </button>
                            <div class="nav-dropdown-menu">
                                <a href="${base}docs/index.html" data-i18n="nav.overview">Overview</a>
                                <a href="${base}docs/syntax.html" data-i18n="nav.syntax">Syntax Reference</a>
                                <a href="${base}docs/execution.html" data-i18n="nav.execution">Execution Model</a>
                                <a href="${base}docs/compilation.html" data-i18n="nav.compilation">Compilation</a>
                                <a href="${base}docs/examples.html" data-i18n="nav.examples">Examples</a>
                            </div>
                        </div>
                        <a href="${base}demo/index.html" class="${demoActive}" data-i18n="nav.demo">Demo</a>
                        <a href="${base}about.html" class="${aboutActive}" data-i18n="nav.about">About</a>
                        <div class="lang-switcher">
                            <button class="lang-btn${storedLang === 'en' ? ' active' : ''}" data-lang="en">EN</button>
                            <button class="lang-btn${storedLang === 'zh' ? ' active' : ''}" data-lang="zh">中文</button>
                        </div>
                    </div>
                </div>
            </nav>
        `;
    }

    // ---- Generate footer HTML ----

    function generateFooterHTML() {
        return `
            <footer class="site-footer">
                <p><strong>NormCode 规范码</strong> — <span data-i18n="footer.tagline">Structured AI Planning That You Can Audit</span></p>
                <p>广州心镜智科技工作室 © 2025</p>
                <div class="footer-links">
                    <a href="https://arxiv.org/abs/2512.10563" target="_blank" rel="noopener noreferrer" data-i18n="footer.paper">Research Paper</a>
                    <a href="mailto:xin.guan@psylensai.com" data-i18n="footer.contact">Contact</a>
                </div>
                <p style="margin-top: var(--space-md); font-size: var(--text-xs); opacity: 0.7;">
                    <span data-i18n="footer.office">TIMETABLE GBA Youth Innovation Base, Nansha, Guangzhou</span>
                </p>
            </footer>
        `;
    }

    // ---- Initialize ----

    function init() {
        // Insert nav
        const navHTML = generateNavHTML();
        const navTemp = document.createElement('div');
        navTemp.innerHTML = navHTML;
        const navEl = navTemp.querySelector('.site-nav');
        document.body.insertBefore(navEl, document.body.firstChild);

        // Insert footer (if a <footer> placeholder or end of body)
        const existingFooter = document.querySelector('footer');
        if (!existingFooter) {
            document.body.insertAdjacentHTML('beforeend', generateFooterHTML());
        }

        // Insert menu overlay
        const overlay = document.createElement('div');
        overlay.className = 'menu-overlay';
        document.body.insertBefore(overlay, document.body.firstChild);

        // Mobile menu
        const menuToggle = document.querySelector('.menu-toggle');
        const navLinks = document.querySelector('.nav-links');

        function toggleMenu(open) {
            const isOpen = open !== undefined ? open : !navLinks.classList.contains('active');
            menuToggle.classList.toggle('active', isOpen);
            navLinks.classList.toggle('active', isOpen);
            overlay.classList.toggle('active', isOpen);
            document.body.style.overflow = isOpen ? 'hidden' : '';
        }

        if (menuToggle) {
            menuToggle.addEventListener('click', () => toggleMenu());
        }
        overlay.addEventListener('click', () => toggleMenu(false));

        // Smooth scroll for anchor links
        navEl.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href === '#') return;
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                toggleMenu(false);
            });
        });

        // Language buttons
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const lang = this.getAttribute('data-lang');
                if (typeof window.setLanguage === 'function') {
                    window.setLanguage(lang);
                }
            });
        });
    }

    // Run immediately (script is at end of body)
    init();
    document.documentElement.lang = storedLang;
})();

