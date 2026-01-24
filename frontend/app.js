// ==================== Configuration ====================
const API_BASE_URL = 'http://localhost:8000/api';
const POLL_INTERVAL = 2000; // 2 seconds

// ==================== State Management ====================
let uploadedDocuments = [];
let processingDocuments = new Set();
let pollInterval = null;

// ==================== DOM Elements ====================
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    views: document.querySelectorAll('.view'),

    // Upload
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    docTypeSelect: document.getElementById('docTypeSelect'),
    uploadQueue: document.getElementById('uploadQueue'),
    processingStatus: document.getElementById('processingStatus'),
    statusList: document.getElementById('statusList'),

    // Chat
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    exampleQuestions: document.querySelectorAll('.example-q'),

    // Documents
    documentsList: document.getElementById('documentsList'),

    // Utilities
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer')
};

// ==================== Navigation ====================
elements.navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetView = btn.dataset.view;

        // Update active nav button
        elements.navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update active view
        elements.views.forEach(v => v.classList.remove('active'));
        document.getElementById(`${targetView}-view`).classList.add('active');

        // Load data for specific views
        if (targetView === 'documents') {
            loadDocuments();
        }
    });
});

// ==================== File Upload ====================
// Drag and drop
elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.style.borderColor = 'var(--primary-solid)';
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.style.borderColor = '';
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.style.borderColor = '';
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
});

// Click to browse
elements.browseBtn.addEventListener('click', () => {
    elements.fileInput.click();
});

elements.uploadArea.addEventListener('click', (e) => {
    if (e.target === elements.uploadArea || e.target.closest('.upload-icon, h3, p')) {
        elements.fileInput.click();
    }
});

elements.fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
    e.target.value = ''; // Reset input
});

// Handle file uploads
async function handleFiles(files) {
    const docType = elements.docTypeSelect.value;

    for (const file of files) {
        await uploadFile(file, docType);
    }
}

async function uploadFile(file, docType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);

    try {
        showToast('Uploading ' + file.name, 'info');

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            headers: auth.getHeaders(),
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();

        showToast('Upload successful! Processing...', 'success');

        // Add to processing set
        processingDocuments.add(data.doc_id);

        // Show processing status
        elements.processingStatus.classList.remove('hidden');
        addStatusItem(data.doc_id, file.name);

        // Start polling for status
        startPolling();

    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed: ' + error.message, 'error');
    }
}

// ==================== Status Polling ====================
function startPolling() {
    if (pollInterval) return; // Already polling

    pollInterval = setInterval(async () => {
        if (processingDocuments.size === 0) {
            stopPolling();
            return;
        }

        for (const docId of processingDocuments) {
            await checkStatus(docId);
        }
    }, POLL_INTERVAL);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function checkStatus(docId) {
    try {
        const response = await fetch(`${API_BASE_URL}/status/${docId}`, {
            headers: auth.getHeaders()
        });
        const data = await response.json();

        updateStatusItem(docId, data);

        if (data.status === 'completed') {
            processingDocuments.delete(docId);
            showToast(`${data.filename} processed successfully!`, 'success');
        } else if (data.status === 'failed') {
            processingDocuments.delete(docId);
            showToast(`${data.filename} processing failed`, 'error');
        }

    } catch (error) {
        console.error('Status check error:', error);
    }
}

function addStatusItem(docId, filename) {
    const statusItem = document.createElement('div');
    statusItem.className = 'status-item';
    statusItem.id = `status-${docId}`;
    statusItem.innerHTML = `
        <div class="status-item-header">
            <span class="upload-item-name">${filename}</span>
            <span class="status-badge processing">Processing</span>
        </div>
        <div class="upload-item-progress">
            <div class="upload-item-progress-bar" style="width: 10%"></div>
        </div>
    `;

    elements.statusList.appendChild(statusItem);
}

function updateStatusItem(docId, data) {
    const statusItem = document.getElementById(`status-${docId}`);
    if (!statusItem) return;

    const badge = statusItem.querySelector('.status-badge');
    const progressBar = statusItem.querySelector('.upload-item-progress-bar');

    badge.textContent = data.status.replace('_', ' ').toUpperCase();
    badge.className = `status-badge ${data.status}`;
    progressBar.style.width = `${data.progress}%`;
}

// ==================== Chat Functionality ====================
elements.sendBtn.addEventListener('click', sendMessage);
elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

elements.exampleQuestions.forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.dataset.q;
        elements.chatInput.value = question;
        sendMessage();
    });
});

async function sendMessage() {
    const question = elements.chatInput.value.trim();
    if (!question) return;

    // Clear input
    elements.chatInput.value = '';

    // Remove welcome message if present
    const welcomeMsg = elements.chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message
    addMessage('user', question);

    // Disable input while processing
    elements.chatInput.disabled = true;
    elements.sendBtn.disabled = true;

    // Add loading message
    const loadingId = addMessage('assistant', 'Thinking...', null, true);

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...auth.getHeaders()
            },
            body: JSON.stringify({
                question: question,
                top_k: 5
            })
        });

        if (!response.ok) {
            throw new Error('Query failed');
        }

        const data = await response.json();

        // Remove loading message
        document.getElementById(loadingId).remove();

        // Add assistant response
        addMessage('assistant', data.answer, data.sources);

    } catch (error) {
        console.error('Query error:', error);
        document.getElementById(loadingId).remove();
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        showToast('Query failed: ' + error.message, 'error');
    } finally {
        elements.chatInput.disabled = false;
        elements.sendBtn.disabled = false;
        elements.chatInput.focus();
    }
}

function addMessage(role, text, sources = null, isLoading = false) {
    const messageId = `msg-${Date.now()}-${Math.random()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;

    const avatar = role === 'user' ? '👤' : '🤖';

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                <h4>📄 Sources:</h4>
                ${sources.map((source, idx) => `
                    <div class="source-item">
                        <div>${source.text.substring(0, 150)}${source.text.length > 150 ? '...' : ''}</div>
                        <div class="source-meta">
                            ${source.filename} ${source.page_number ? `(Page ${source.page_number})` : ''} 
                            • Relevance: ${(source.similarity_score * 100).toFixed(0)}%
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${text}</div>
            ${sourcesHtml}
        </div>
    `;

    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return messageId;
}

// ==================== Documents List ====================
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`, {
            headers: auth.getHeaders()
        });
        const data = await response.json();

        uploadedDocuments = data.documents;
        renderDocuments();

    } catch (error) {
        console.error('Load documents error:', error);
        showToast('Failed to load documents', 'error');
    }
}

function renderDocuments() {
    if (uploadedDocuments.length === 0) {
        elements.documentsList.innerHTML = `
            <div class="empty-state">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                    <rect x="15" y="10" width="50" height="60" rx="4" stroke="currentColor" stroke-width="2"/>
                    <line x1="25" y1="25" x2="55" y2="25" stroke="currentColor" stroke-width="2"/>
                    <line x1="25" y1="35" x2="55" y2="35" stroke="currentColor" stroke-width="2"/>
                    <line x1="25" y1="45" x2="45" y2="45" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>No Documents Yet</h3>
                <p>Upload documents to get started</p>
            </div>
        `;
        return;
    }

    elements.documentsList.innerHTML = uploadedDocuments.map(doc => {
        const icon = getDocumentIcon(doc.doc_type);
        const statusColor = doc.status === 'completed' ? 'var(--success)' :
            doc.status === 'failed' ? 'var(--error)' : 'var(--info)';

        return `
            <div class="document-card" data-doc-id="${doc.doc_id}">
                <div class="document-card-header">
                    <div class="document-icon">${icon}</div>
                    <div class="document-actions">
                        <button class="icon-btn" onclick="deleteDocument('${doc.doc_id}')" title="Delete">
                            🗑️
                        </button>
                    </div>
                </div>
                <div class="document-name">${doc.filename}</div>
                <div class="document-meta">
                    <div style="color: ${statusColor}">● ${doc.status.replace('_', ' ').toUpperCase()}</div>
                    <div>${new Date(doc.upload_time).toLocaleString()}</div>
                </div>
                <div class="document-stats">
                    <div class="stat">
                        <div class="stat-label">Pages</div>
                        <div class="stat-value">${doc.page_count || 'N/A'}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Entities</div>
                        <div class="stat-value">${doc.entity_count || 0}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Type</div>
                        <div class="stat-value">${doc.doc_type}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getDocumentIcon(docType) {
    const icons = {
        'policy': '📋',
        'claim_form': '📝',
        'hospital_bill': '🏥',
        'surveyor_report': '🔍',
        'discharge_summary': '📄',
        'fir': '🚔',
        'photo': '📷',
        'other': '📎'
    };
    return icons[docType] || '📄';
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
            method: 'DELETE',
            headers: auth.getHeaders()
        });

        if (!response.ok) {
            throw new Error('Delete failed');
        }

        showToast('Document deleted successfully', 'success');
        loadDocuments();

    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete document', 'error');
    }
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('Insurance Claims Processing System initialized');

    // Check authentication
    if (!auth.isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }

    // Load initial data
    loadDocuments();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopPolling();
});
