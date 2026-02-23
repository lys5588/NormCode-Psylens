/**
 * Page-Flows Document Conversion Module
 *
 * Client-side extraction of text from PDF, DOCX, PPTX, and XLSX files.
 * Requires CDN libraries: pdf.js (pdfjsLib), mammoth.js, JSZip.
 */

const CONVERTIBLE_EXTS = /\.(pdf|docx|pptx|xlsx)$/i;
const LEGACY_BINARY_EXTS = /\.(doc|ppt|xls)$/i;
const PDFJS_WORKER_URL = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

function isConvertible(filename) {
    return CONVERTIBLE_EXTS.test(filename);
}

/**
 * Show a warning overlay listing the files that will be converted.
 * Returns a Promise<boolean> — true if the user clicks "Convert & Add".
 */
function showConvertWarning(filenames) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('pfConvertOverlay');
        const list = document.getElementById('pfConvertFileList');
        list.innerHTML = filenames
            .map(n => `<div class="pf-convert-fname">${escapeHtml(n)}</div>`)
            .join('');

        const proceedBtn = document.getElementById('pfConvertProceed');
        const cancelBtn  = document.getElementById('pfConvertCancel');

        function cleanup() {
            overlay.classList.remove('open');
            proceedBtn.removeEventListener('click', onProceed);
            cancelBtn.removeEventListener('click', onCancel);
        }
        function onProceed() { cleanup(); resolve(true); }
        function onCancel()  { cleanup(); resolve(false); }

        proceedBtn.addEventListener('click', onProceed);
        cancelBtn.addEventListener('click', onCancel);
        overlay.classList.add('open');
    });
}

/**
 * Convert a File object to plain text.
 * Throws if the required library is missing or the format is unsupported.
 */
async function convertFileToText(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const buffer = await file.arrayBuffer();

    switch (ext) {
        case 'pdf':
            if (typeof pdfjsLib === 'undefined')
                throw new Error('PDF.js library not loaded');
            return _convertPdf(buffer);
        case 'docx':
            if (typeof mammoth === 'undefined')
                throw new Error('Mammoth.js library not loaded');
            return _convertDocx(buffer);
        case 'pptx':
            if (typeof JSZip === 'undefined')
                throw new Error('JSZip library not loaded');
            return _convertPptx(buffer);
        case 'xlsx':
            if (typeof JSZip === 'undefined')
                throw new Error('JSZip library not loaded');
            return _convertXlsx(buffer);
        default:
            throw new Error('Unsupported format: .' + ext);
    }
}

// ---- Internal converters ----

async function _convertPdf(buffer) {
    if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;
    }
    const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
    const pages = [];
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const tc   = await page.getTextContent();
        pages.push(tc.items.map(item => item.str).join(' '));
    }
    return pages.join('\n\n');
}

async function _convertDocx(buffer) {
    const result = await mammoth.extractRawText({ arrayBuffer: buffer });
    return result.value;
}

async function _convertPptx(buffer) {
    const zip = await JSZip.loadAsync(buffer);
    const slideNames = Object.keys(zip.files)
        .filter(n => /^ppt\/slides\/slide\d+\.xml$/i.test(n))
        .sort((a, b) =>
            parseInt(a.match(/slide(\d+)/)[1]) - parseInt(b.match(/slide(\d+)/)[1])
        );

    const slides = [];
    for (const name of slideNames) {
        const xml = await zip.file(name).async('text');
        const doc = new DOMParser().parseFromString(xml, 'text/xml');
        const tNodes = doc.getElementsByTagNameNS('*', 't');
        const texts = [];
        for (let i = 0; i < tNodes.length; i++) {
            const s = tNodes[i].textContent;
            if (s) texts.push(s);
        }
        if (texts.length) {
            const num = name.match(/slide(\d+)/)[1];
            slides.push('[Slide ' + num + ']\n' + texts.join('\n'));
        }
    }
    return slides.join('\n\n');
}

async function _convertXlsx(buffer) {
    const zip = await JSZip.loadAsync(buffer);

    // Shared strings table
    const strings = [];
    const ssFile = zip.file('xl/sharedStrings.xml');
    if (ssFile) {
        const xml = await ssFile.async('text');
        const doc = new DOMParser().parseFromString(xml, 'text/xml');
        const siNodes = doc.getElementsByTagNameNS('*', 'si');
        for (let i = 0; i < siNodes.length; i++) {
            const tNodes = siNodes[i].getElementsByTagNameNS('*', 't');
            let text = '';
            for (let j = 0; j < tNodes.length; j++) text += tNodes[j].textContent || '';
            strings.push(text);
        }
    }

    // Worksheet data
    const sheetNames = Object.keys(zip.files)
        .filter(n => /^xl\/worksheets\/sheet\d+\.xml$/i.test(n))
        .sort((a, b) =>
            parseInt(a.match(/sheet(\d+)/)[1]) - parseInt(b.match(/sheet(\d+)/)[1])
        );

    const sheets = [];
    for (const name of sheetNames) {
        const xml = await zip.file(name).async('text');
        const doc = new DOMParser().parseFromString(xml, 'text/xml');
        const rowNodes = doc.getElementsByTagNameNS('*', 'row');
        const rows = [];

        for (let r = 0; r < rowNodes.length; r++) {
            const cellNodes = rowNodes[r].getElementsByTagNameNS('*', 'c');
            const cells = [];
            for (let c = 0; c < cellNodes.length; c++) {
                const cell = cellNodes[c];
                const type = cell.getAttribute('t');
                const vNodes = cell.getElementsByTagNameNS('*', 'v');
                const val = vNodes.length ? vNodes[0].textContent : '';
                cells.push(type === 's' && val ? (strings[parseInt(val)] || '') : val);
            }
            rows.push(cells.join('\t'));
        }

        const num = name.match(/sheet(\d+)/)[1];
        sheets.push('[Sheet ' + num + ']\n' + rows.join('\n'));
    }
    return sheets.join('\n\n');
}
