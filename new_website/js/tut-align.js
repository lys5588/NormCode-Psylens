/**
 * Tutorial Alignment — Positions annotation notes to align with specific code lines
 *
 * Reads `data-tut-line` from each `.tut-note` element, calculates
 * the Y center of that line inside the code editor's `<pre>`, and
 * sets the note's `top` so its connector line points to the exact line.
 *
 * Runs after layout settles, on resize, and after language changes.
 */

(function () {
    'use strict';

    function alignNotes() {
        var tut = document.querySelector('.tut');
        if (!tut) return;

        var pre = tut.querySelector('.tut-code .code-editor pre');
        if (!pre) return;

        var codeEditor = tut.querySelector('.tut-code .code-editor');
        if (!codeEditor) return;

        // ---- Compute line metrics ----
        var preStyle = window.getComputedStyle(pre);
        var fontSize  = parseFloat(preStyle.fontSize);
        var lineHeight = parseFloat(preStyle.lineHeight);
        if (isNaN(lineHeight)) lineHeight = fontSize * 2;

        // Editor bar height
        var editorBar = codeEditor.querySelector('.code-editor-bar');
        var barHeight = editorBar ? editorBar.offsetHeight : 0;

        // Pre padding-top
        var prePaddingTop = parseFloat(preStyle.paddingTop) || 0;

        // ---- Compute positions relative to each side column ----
        // Because .tut uses CSS grid with align-items:stretch,
        // all three columns share the same top edge.
        // The code editor offset within .tut-code equals horizontal padding only;
        // vertically the code-editor starts at the same Y as .tut-side.

        var sides = tut.querySelectorAll('.tut-side');
        sides.forEach(function (side) {
            var sideRect = side.getBoundingClientRect();
            var editorRect = codeEditor.getBoundingClientRect();

            // Vertical offset: how far down the code-editor starts vs the side column
            var offsetY = editorRect.top - sideRect.top;

            var notes = side.querySelectorAll('.tut-note[data-tut-line]');
            notes.forEach(function (note) {
                var lineNum = parseInt(note.getAttribute('data-tut-line'), 10);
                if (isNaN(lineNum) || lineNum < 1) return;

                // Center-Y of the target line, relative to the side column
                var lineCenterY = offsetY + barHeight + prePaddingTop
                    + (lineNum - 0.5) * lineHeight;

                // CSS transform: translateY(-50%) centers the note card on this point
                note.style.top = lineCenterY + 'px';
            });
        });
    }

    // Expose for external callers
    window._tutAlign = alignNotes;

    // ================================================================
    // Hover interaction — highlight code line + pop the hovered note
    // ================================================================

    // Color map per note type: [background, borderLeft]
    var noteColors = {
        'tut-note--data':   ['rgba(156, 220, 254, 0.12)', 'var(--code-variable)'],
        'tut-note--action': ['rgba(220, 220, 170, 0.12)', 'var(--code-function)'],
        'tut-note--loop':   ['rgba(206, 145, 120, 0.12)', 'var(--code-string)'],
        'tut-note--scope':  ['rgba(78, 154, 255, 0.10)',  'var(--accent)'],
        'tut-note--flow':   ['rgba(168, 131, 255, 0.10)', 'var(--accent-purple)']
    };

    function setupHover() {
        var tut = document.querySelector('.tut');
        if (!tut) return;

        var pre = tut.querySelector('.tut-code .code-editor pre');
        if (!pre) return;

        // Ensure <pre> is a positioning context
        pre.style.position = 'relative';

        // Create a single reusable highlight overlay
        var hl = document.createElement('div');
        hl.className = 'code-line-hl';
        pre.appendChild(hl);

        var allNotes = tut.querySelectorAll('.tut-note[data-tut-line]');

        allNotes.forEach(function (note) {
            note.addEventListener('mouseenter', function () {
                var lineNum = parseInt(note.getAttribute('data-tut-line'), 10);
                if (isNaN(lineNum) || lineNum < 1) return;

                // ---- Position the highlight bar ----
                var preStyle = window.getComputedStyle(pre);
                var fontSize  = parseFloat(preStyle.fontSize);
                var lineHeight = parseFloat(preStyle.lineHeight);
                if (isNaN(lineHeight)) lineHeight = fontSize * 2;
                var paddingTop = parseFloat(preStyle.paddingTop) || 0;

                hl.style.top    = (paddingTop + (lineNum - 1) * lineHeight) + 'px';
                hl.style.height = lineHeight + 'px';

                // ---- Pick color based on note type ----
                var bg = 'rgba(78,154,255,0.08)';
                var bl = 'var(--accent)';
                for (var cls in noteColors) {
                    if (note.classList.contains(cls)) {
                        bg = noteColors[cls][0];
                        bl = noteColors[cls][1];
                        break;
                    }
                }
                hl.style.background  = bg;
                hl.style.borderLeft  = '3px solid ' + bl;

                hl.classList.add('visible');

                // ---- Active / dimmed states on note cards ----
                note.classList.add('tut-active');
                allNotes.forEach(function (other) {
                    if (other !== note) other.classList.add('tut-dimmed');
                });
            });

            note.addEventListener('mouseleave', function () {
                hl.classList.remove('visible');
                note.classList.remove('tut-active');
                allNotes.forEach(function (other) {
                    other.classList.remove('tut-dimmed');
                });
            });
        });
    }

    // ================================================================
    // Flow-index connector — arrow from info box to line-num column
    // ================================================================

    function positionFlowConnector() {
        var lineNum = document.querySelector('.tut-code .line-num');
        var infoBox = document.querySelector('.info-box--subtle');
        if (!lineNum || !infoBox) return;

        var lineNumRect = lineNum.getBoundingClientRect();
        var infoBoxRect = infoBox.getBoundingClientRect();

        // Center of the line-num element, relative to info box left edge
        var connectorLeft = (lineNumRect.left + lineNumRect.right) / 2 - infoBoxRect.left;
        infoBox.style.setProperty('--connector-left', connectorLeft + 'px');
    }

    // Run after a short delay (DOM + fonts need to settle)
    setTimeout(alignNotes, 200);
    setTimeout(setupHover, 250);
    setTimeout(positionFlowConnector, 300);
    // Also try again a bit later in case fonts loaded slowly
    setTimeout(alignNotes, 600);
    setTimeout(positionFlowConnector, 650);

    // Re-align on resize
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            alignNotes();
            positionFlowConnector();
        }, 150);
    });

    // Re-align when IntersectionObserver triggers visibility
    // (the section starts with opacity:0, getBoundingClientRect still works
    //  but fonts may shift; re-align once visible)
    var tutSection = document.querySelector('.tut');
    if (tutSection) {
        var section = tutSection.closest('.fade-in');
        if (section) {
            var mo = new MutationObserver(function (mutations) {
                mutations.forEach(function (m) {
                    if (m.attributeName === 'class' && section.classList.contains('visible')) {
                        setTimeout(alignNotes, 50);
                        mo.disconnect();
                    }
                });
            });
            mo.observe(section, { attributes: true, attributeFilter: ['class'] });
        }
    }

    // Re-align after language change (wrap window.setLanguage)
    var _prevSetLang = window.setLanguage;
    if (typeof _prevSetLang === 'function') {
        window.setLanguage = function (lang) {
            _prevSetLang(lang);
            setTimeout(alignNotes, 100);
            setTimeout(positionFlowConnector, 150);
        };
    }
})();
