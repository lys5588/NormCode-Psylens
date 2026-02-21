// ============================================================================
// Initialization
// ============================================================================

// Guard: redirect to gateway if no server URL, or to plan selection if no plan chosen
if (!serverUrl) {
    window.location.replace('index.html');
} else if (!sessionStorage.getItem('normcode_plan_id') && !sessionStorage.getItem('normcode_plans')) {
    window.location.replace('plans.html');
}

// Populate the hidden server URL input from sessionStorage
document.getElementById('serverUrl').value = serverUrl;

// Populate session info display
try {
    const serverDisplay = serverUrl.replace(/^https?:\/\//, '');
    document.getElementById('sessionServer').textContent = serverDisplay;

    const planId = sessionStorage.getItem('normcode_plan_id') || '';
    const plans = JSON.parse(sessionStorage.getItem('normcode_plans') || '[]');
    const plan = plans.find(p => p.id === planId);
    document.getElementById('sessionPlan').textContent = plan ? (plan.name || plan.id) : planId || '—';
} catch (e) {}

// Initialize refs lists with empty state on page load
renderRefsList('content');
renderRefsList('template');
renderRefsList('style');

// Plan select change handler
planSelect.addEventListener('change', async (e) => {
    currentPlanId = e.target.value;
    await loadPlanDefaults(currentPlanId);
});

// Auto-connect once on load (no retries)
setTimeout(() => connect(true), 500);

