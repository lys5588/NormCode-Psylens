/**
 * NormCode Server UI - Deploy Modal
 */

let currentDeployTab = 'upload';
let selectedFile = null;

function showDeployModal() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    resetDeployModal();
}

function hideDeployModal() {
    const modal = document.getElementById('deployModal');
    modal.classList.add('hidden');
    modal.style.display = 'none';
    resetDeployModal();
}

function resetDeployModal() {
    selectedFile = null;
    document.getElementById('uploadStatus').classList.add('hidden');
    document.getElementById('uploadProgressBar').style.width = '0%';
    document.getElementById('deployPath').value = '';
    document.getElementById('deployPlanId').value = '';
    document.getElementById('fileInput').value = '';
    document.getElementById('deployBtn').disabled = false;
    document.getElementById('deployBtn').textContent = 'Deploy';
}

function switchDeployTab(tab) {
    currentDeployTab = tab;
    document.querySelectorAll('.deploy-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.deployTab === tab);
    });
    document.getElementById('uploadPanel').classList.toggle('active', tab === 'upload');
    document.getElementById('pathPanel').classList.toggle('active', tab === 'path');
}

function initUploadZone() {
    const uploadZone = document.getElementById('uploadZone');

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length && files[0].name.endsWith('.zip')) {
            handleFile(files[0]);
        } else {
            showToast('Please drop a .zip file', 'error');
        }
    });
}

function handleFileSelect(e) {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    selectedFile = file;
    document.getElementById('uploadStatus').classList.remove('hidden');
    document.getElementById('uploadFileName').textContent = file.name + ' (' + formatSize(file.size) + ')';
    document.getElementById('uploadProgressBar').style.width = '0%';
}

async function deployPlan() {
    const btn = document.getElementById('deployBtn');
    btn.disabled = true;
    btn.textContent = 'Deploying...';
    
    try {
        const pathValue = document.getElementById('deployPath').value.trim();
        
        if (pathValue) {
            await deployFromPath();
        } else if (selectedFile) {
            await deployFromFile();
        } else {
            showToast('Please enter a path or select a zip file', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Deploy';
    }
}

async function deployFromFile() {
    if (!selectedFile) {
        showToast('Please select a zip file', 'error');
        return;
    }
    
    const progressBar = document.getElementById('uploadProgressBar');
    
    const arrayBuffer = await selectedFile.arrayBuffer();
    progressBar.style.width = '30%';
    
    const formData = new FormData();
    formData.append('plan', new Blob([arrayBuffer]), selectedFile.name);
    
    const resp = await fetch(`${API}/plans/deploy-file`, {
        method: 'POST',
        body: formData
    });
    
    progressBar.style.width = '100%';
    
    const data = await safeJson(resp, 'deploy file');
    if (data) {
        showToast(`Plan '${data.plan_id}' deployed successfully`, 'success');
        hideDeployModal();
        fetchPlans();
    }
}

async function deployFromPath() {
    const path = document.getElementById('deployPath').value.trim();
    if (!path) {
        showToast('Please enter a directory path', 'error');
        return;
    }
    
    const planId = document.getElementById('deployPlanId').value.trim();
    
    const payload = { path };
    if (planId) payload.plan_id = planId;
    
    const resp = await fetch(`${API}/plans/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    const data = await safeJson(resp, 'deploy from path');
    if (data) {
        showToast(`Plan '${data.plan_id}' deployed from ${data.source}`, 'success');
        hideDeployModal();
        fetchPlans();
    }
}
