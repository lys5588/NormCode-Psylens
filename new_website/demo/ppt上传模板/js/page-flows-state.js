/**
 * Page-Flows State — PPT Template variant
 *
 * pfTemplate items carry { name, path, type, isDefault, binary? }
 *   - isDefault=true  → server-side file, no upload needed
 *   - binary=ArrayBuffer → user-uploaded PPTX, uploaded as octet-stream
 */

// ---- Session guards ----
const serverUrl = sessionStorage.getItem('normcode_server_url');
if (!serverUrl) { window.location.replace('../../index.html'); }
// This client is hard-wired to a single plan — no plans.html redirect needed.

// ---- Hard-coded plan ----
const PLAN_ID = 'c1cc3210';

// ---- State ----
let step = 0;
let connected = false;
let selectedModel = '';
let availableModels = [];
let currentPlanId = PLAN_ID;

/** Exactly one entry max: { name, path, type:'pptx_file', isDefault, binary? } */
let pfTemplate = [];
/** Content reference files — text/converted */
let pfContent  = [];
/** Style guide files — text */
let pfStyle    = [];

// ---- DOM references ----
const dots    = document.querySelectorAll('.pf-dot');
const steps   = document.querySelectorAll('.pf-step');
const btnBack = document.getElementById('pfBtnBack');
const btnNext = document.getElementById('pfBtnNext');

// ---- Run tracking ----
let currentRunId  = '';
let currentUserId = '';
let pfEvtSource   = null;
let pfLoop        = { current: 0, iteration: 0, completed: 0, total: 0 };
let pfTimelineMap = {};
let _previewState = { name: '', content: '', rendered: true, mode: 'text' };
