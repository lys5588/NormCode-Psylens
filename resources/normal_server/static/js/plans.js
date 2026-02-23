/**
 * NormCode Server UI - Plans Management
 */

async function fetchPlans() {
    try {
        const resp = await fetch(`${API}/plans`);
        const data = await safeJson(resp, 'fetch plans');
        if (data === null) return;
        plans = {};
        data.forEach(p => plans[p.id] = p);
        renderPlans(data);
        document.getElementById('statPlans').textContent = data.length;
    } catch (e) {
        showToast('Failed to fetch plans: ' + e.message, 'error');
    }
}

function renderPlans(list) {
    const el = document.getElementById('plansList');
    if (!list.length) {
        el.innerHTML = '<div class="empty-state">No plans deployed</div>';
        return;
    }
    el.innerHTML = list.map(p => `
        <div class="plan-item ${p.id === selectedPlanId ? 'selected' : ''}" onclick="selectPlan('${p.id}')">
            <div class="plan-name">${p.name || 'Unnamed'}</div>
            <div class="plan-id">${p.id.slice(0, 16)}</div>
        </div>
    `).join('');
}

function selectPlan(id) {
    selectedPlanId = id;
    document.getElementById('runBtn').disabled = false;
    document.getElementById('removeBtn').disabled = false;
    renderPlans(Object.values(plans));
}

async function removePlan() {
    if (!selectedPlanId || !confirm('Remove this plan? This cannot be undone.')) return;
    try {
        const resp = await fetch(`${API}/plans/${selectedPlanId}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Plan removed', 'success');
            selectedPlanId = null;
            document.getElementById('runBtn').disabled = true;
            document.getElementById('removeBtn').disabled = true;
            fetchPlans();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Failed to remove', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}
