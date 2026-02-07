// ============================================================================
// Initialization
// ============================================================================

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

