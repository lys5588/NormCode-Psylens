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

// Auto-connect on load
setTimeout(connect, 500);

