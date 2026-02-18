/**
 * Section Loader — Dynamically loads HTML section partials into <main>
 *
 * Fetches all section files in parallel, inserts them in order,
 * then loads the remaining scripts that depend on the DOM being populated
 * (main.js, lang files, hero-rotation.js).
 */

(function () {
    'use strict';

    // Ordered list of section partials to load
    var sections = [
        'sections/hero.html',
        'sections/gap.html',
        'sections/language.html',
        'sections/why-language.html',
        'sections/lifecycle.html',
        'sections/see-it.html',
        'sections/properties.html',
        'sections/who.html',
        'sections/credibility.html',
        'sections/get-started.html'
    ];

    // Scripts to load AFTER all sections are in the DOM
    var postScripts = [
        'js/main.js',
        'lang/index.js',
        'lang/language-section.js',
        'js/hero-rotation.js',
        'js/tut-align.js'
    ];

    var mainEl = document.getElementById('main');

    /**
     * Load a script dynamically and return a Promise
     */
    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            var script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.body.appendChild(script);
        });
    }

    /**
     * Load scripts sequentially (order matters for lang files)
     */
    function loadScriptsInOrder(scripts) {
        return scripts.reduce(function (chain, src) {
            return chain.then(function () { return loadScript(src); });
        }, Promise.resolve());
    }

    /**
     * Fetch all sections in parallel, insert in order, then boot scripts
     */
    Promise.all(
        sections.map(function (url) {
            return fetch(url).then(function (res) {
                if (!res.ok) throw new Error('Failed to load ' + url + ': ' + res.status);
                return res.text();
            });
        })
    )
    .then(function (htmlFragments) {
        // Insert all sections into <main> in order
        mainEl.innerHTML = htmlFragments.join('\n');

        // Now that the DOM is populated, load scripts that depend on it
        return loadScriptsInOrder(postScripts);
    })
    .catch(function (err) {
        console.error('[section-loader]', err);
        mainEl.innerHTML = '<p style="color:red;text-align:center;padding:2rem;">Failed to load page sections. Please refresh.</p>';
    });
})();

