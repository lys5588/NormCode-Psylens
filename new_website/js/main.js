/**
 * Main — Shared page utilities
 * 
 * Scroll-triggered animations, video lazy-loading, download button feedback.
 * Include this script on every page AFTER nav.js.
 */

(function () {
    'use strict';

    // ---- Scroll-triggered fade-in ----

    function initScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -40px 0px'
        });

        document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
    }

    // ---- Video lazy-load (click to play) ----

    function initVideoPlayers() {
        document.querySelectorAll('.video-container[data-src]').forEach(container => {
            const poster = container.querySelector('.video-poster');

            container.addEventListener('click', function handleClick() {
                const src = container.getAttribute('data-src');
                if (!src) return;

                // Create and insert video element
                let video = container.querySelector('video');
                if (!video) {
                    video = document.createElement('video');
                    video.controls = true;
                    video.autoplay = true;
                    video.playsInline = true;
                    video.style.width = '100%';
                    video.style.display = 'block';

                    const source = document.createElement('source');
                    source.src = src;
                    source.type = 'video/mp4';
                    video.appendChild(source);

                    container.appendChild(video);
                } else {
                    video.play().catch(() => { });
                }

                // Hide poster
                if (poster) poster.classList.add('hidden');

                // Remove click handler (only need it once)
                container.removeEventListener('click', handleClick);
            });
        });
    }

    // ---- Download button feedback ----

    function initDownloadButtons() {
        document.querySelectorAll('.btn-primary[download]').forEach(btn => {
            btn.addEventListener('click', function (e) {
                // Ripple effect
                const ripple = document.createElement('span');
                ripple.classList.add('btn-ripple');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
                ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
                this.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);

                // Store original content
                const originalContent = this.innerHTML.replace(/<span class="btn-ripple".*?<\/span>/g, '');

                // Downloading state
                this.classList.add('downloading');
                this.innerHTML = `
                    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 1s linear infinite;">
                        <circle cx="12" cy="12" r="10" stroke-dasharray="50" stroke-dashoffset="15" stroke-linecap="round"></circle>
                    </svg>
                    <span>Preparing download...</span>
                `;

                // Success state
                setTimeout(() => {
                    this.classList.remove('downloading');
                    this.classList.add('download-started');
                    this.innerHTML = `
                        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        <span>Download started!</span>
                    `;
                }, 800);

                // Restore original
                setTimeout(() => {
                    this.classList.remove('download-started');
                    this.innerHTML = originalContent;
                }, 4000);
            });
        });
    }

    // ---- Initialize everything ----

    function init() {
        initScrollAnimations();
        initVideoPlayers();
        initDownloadButtons();
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

