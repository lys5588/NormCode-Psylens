/**
 * Page-Flows State Management Module
 *
 * Manages global state, DOM references, and session guards.
 */

// ---- Session guards ----
const serverUrl = sessionStorage.getItem('normcode_server_url');
if (!serverUrl) { window.location.replace('index.html'); }
else if (!sessionStorage.getItem('normcode_plan_id') && !sessionStorage.getItem('normcode_plans')) { window.location.replace('plans.html'); }

// ---- State variables ----
let step = 0;
let connected = false;
let selectedModel = '';
let availableModels = [];  // [{id, name, is_mock}]
let currentPlanId = sessionStorage.getItem('normcode_plan_id') || '';
let pfContent = [];   // { name, path, content, isDefault }
let pfTemplate = [];
let pfStyle = [];

// ---- DOM element references ----
const dots = document.querySelectorAll('.pf-dot');
const steps = document.querySelectorAll('.pf-step');
const btnBack = document.getElementById('pfBtnBack');
const btnNext = document.getElementById('pfBtnNext');

// ---- Run tracking state ----
let currentRunId = '';
let currentUserId = '';
let pfEvtSource = null;
let pfLoop = { current: 0, iteration: 0, completed: 0, total: 0 };
let pfTimelineMap = {};  // flow_index -> DOM element
let _previewState = { name: '', content: '', rendered: true, mode: 'text' };
