// ============================================================================
// State Management & DOM References
// ============================================================================

// ===== Global State =====
let serverUrl = sessionStorage.getItem('normcode_server_url') || '';
let currentPlanId = null;
let currentRunId = null;
let currentUserId = null;
let eventSource = null;
let uploadedContent = [];
let uploadedTemplate = [];
let uploadedStyle = [];
let defaultInputs = null;
let currentPreviewContent = '';
let currentPreviewFilePath = '';
let inputsModified = false;

// Loop progress tracking
let loopProgress = {
    currentLoop: null,
    iteration: 0,
    totalIterations: null,
    completedInferences: 0,
    totalInferences: 0,
};

// ===== DOM Element References =====
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const runIdEl = document.getElementById('runId');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const eventsLog = document.getElementById('eventsLog');
const startBtn = document.getElementById('startBtn');
const planSelect = document.getElementById('planSelect');

