/**
 * NormCode Server UI - User Input Handling
 */

let currentInputRequest = null;
let inputEventSource = null;
let pendingInputs = [];

async function fetchPendingInputs() {
    try {
        const resp = await fetch(`${API}/inputs`);
        pendingInputs = await resp.json();
        renderPendingInputs();
    } catch (e) {
        console.error('Failed to fetch inputs:', e);
    }
}

function renderPendingInputs() {
    const section = document.getElementById('inputsSection');
    const list = document.getElementById('inputsList');
    const count = document.getElementById('inputsCount');
    
    if (!pendingInputs.length) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    count.textContent = pendingInputs.length;
    
    list.innerHTML = pendingInputs.map(input => {
        const typeIcon = {
            'simple_text': '📝',
            'text_editor': '📄',
            'confirm': '❓',
            'select': '📋',
            'multi_select': '☑️',
        }[input.interaction_type] || '📝';
        
        return `
            <div class="input-item" onclick="openInputModal('${input.request_id}')">
                <span class="input-icon">${typeIcon}</span>
                <div class="input-info">
                    <div class="input-prompt-preview">${escapeHtml(input.prompt.slice(0, 50))}${input.prompt.length > 50 ? '...' : ''}</div>
                    <div class="input-meta-small">
                        ${input.run_id ? input.run_id.slice(0, 8) + '...' : 'Unknown'}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function openInputModal(requestId) {
    const input = pendingInputs.find(i => i.request_id === requestId);
    if (!input) return;
    
    currentInputRequest = input;
    
    document.getElementById('inputModalTitle').textContent = getInputTypeTitle(input.interaction_type);
    document.getElementById('inputPrompt').textContent = input.prompt;
    document.getElementById('inputRunId').textContent = input.run_id ? input.run_id.slice(0, 12) : 'N/A';
    document.getElementById('inputRequestId').textContent = input.request_id;
    
    document.getElementById('textInputField').classList.add('hidden');
    document.getElementById('confirmInputField').classList.add('hidden');
    document.getElementById('selectInputField').classList.add('hidden');
    document.getElementById('inputModalFooter').classList.remove('hidden');
    
    switch (input.interaction_type) {
        case 'confirm':
            document.getElementById('confirmInputField').classList.remove('hidden');
            document.getElementById('inputModalFooter').classList.add('hidden');
            break;
        case 'select':
        case 'multi_select':
            renderSelectOptions(input.options?.choices || []);
            document.getElementById('selectInputField').classList.remove('hidden');
            break;
        case 'text_editor':
            document.getElementById('textInputField').classList.remove('hidden');
            document.getElementById('textInputValue').value = input.options?.initial_content || '';
            document.getElementById('textInputValue').rows = 10;
            break;
        default:
            document.getElementById('textInputField').classList.remove('hidden');
            document.getElementById('textInputValue').value = '';
            document.getElementById('textInputValue').rows = 4;
    }
    
    document.getElementById('inputModal').style.display = 'flex';
}

function getInputTypeTitle(type) {
    const titles = {
        'simple_text': 'Text Input',
        'text_editor': 'Text Editor',
        'confirm': 'Confirmation',
        'select': 'Select Option',
        'multi_select': 'Select Multiple',
    };
    return titles[type] || 'User Input';
}

function renderSelectOptions(choices) {
    const container = document.getElementById('selectOptions');
    container.innerHTML = choices.map((choice, i) => `
        <button class="select-option" onclick="submitSelect('${escapeHtml(choice)}')">
            ${escapeHtml(choice)}
        </button>
    `).join('');
}

function hideInputModal() {
    document.getElementById('inputModal').style.display = 'none';
    currentInputRequest = null;
}

async function submitTextInput() {
    if (!currentInputRequest) return;
    
    const value = document.getElementById('textInputValue').value;
    await submitInputResponse(currentInputRequest.request_id, value);
}

async function submitConfirm(confirmed) {
    if (!currentInputRequest) return;
    
    try {
        const resp = await fetch(`${API}/inputs/${currentInputRequest.request_id}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirmed })
        });
        
        if (resp.ok) {
            showToast('Response submitted', 'success');
            hideInputModal();
            fetchPendingInputs();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Failed to submit', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function submitSelect(selected) {
    if (!currentInputRequest) return;
    
    try {
        const resp = await fetch(`${API}/inputs/${currentInputRequest.request_id}/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected })
        });
        
        if (resp.ok) {
            showToast('Selection submitted', 'success');
            hideInputModal();
            fetchPendingInputs();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Failed to submit', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function submitInputResponse(requestId, response) {
    try {
        const resp = await fetch(`${API}/inputs/${requestId}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ response })
        });
        
        if (resp.ok) {
            showToast('Response submitted', 'success');
            hideInputModal();
            fetchPendingInputs();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Failed to submit', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function cancelInput() {
    if (!currentInputRequest) return;
    
    try {
        const resp = await fetch(`${API}/inputs/${currentInputRequest.request_id}/cancel`, {
            method: 'POST'
        });
        
        if (resp.ok) {
            showToast('Input cancelled', 'success');
            hideInputModal();
            fetchPendingInputs();
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

function connectInputEventStream() {
    inputEventSource = new EventSource(`${API}/inputs/stream`);
    
    inputEventSource.addEventListener('input:pending', (e) => {
        const input = JSON.parse(e.data);
        if (!pendingInputs.find(i => i.request_id === input.request_id)) {
            pendingInputs.push(input);
            renderPendingInputs();
            showToast(`Input required: ${input.prompt.slice(0, 30)}...`, 'info');
        }
    });
    
    inputEventSource.addEventListener('input:completed', (e) => {
        const data = JSON.parse(e.data);
        pendingInputs = pendingInputs.filter(i => i.request_id !== data.request_id);
        renderPendingInputs();
    });
    
    inputEventSource.addEventListener('input:cancelled', (e) => {
        const data = JSON.parse(e.data);
        pendingInputs = pendingInputs.filter(i => i.request_id !== data.request_id);
        renderPendingInputs();
    });
    
    inputEventSource.addEventListener('input:timeout', (e) => {
        const data = JSON.parse(e.data);
        pendingInputs = pendingInputs.filter(i => i.request_id !== data.request_id);
        renderPendingInputs();
    });
    
    inputEventSource.onerror = () => {
        setTimeout(connectInputEventStream, 5000);
    };
}
