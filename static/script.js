const API_BASE = "/api/v1";

// Page Management
const pages = {
    home: document.getElementById('home-page'),
    documents: document.getElementById('documents-page'),
    about: document.getElementById('about-page'),
    'how-it-works': document.getElementById('how-it-works-page'),
    features: document.getElementById('features-page')
};

// Section Management (for home page)
const sections = {
    input: document.getElementById('input-section'),
    progress: document.getElementById('progress-section'),
    result: document.getElementById('result-section')
};

// Navigation
function showPage(pageName) {
    // Hide all pages
    Object.values(pages).forEach(page => {
        if (page) {
            page.classList.remove('active-page');
        }
    });

    // Show selected page
    if (pages[pageName]) {
        pages[pageName].classList.add('active-page');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = Array.from(document.querySelectorAll('.nav-link')).find(link => {
        const href = link.getAttribute('onclick') || '';
        return href.includes(`'${pageName}'`);
    });
    
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Section Management (for research flow)
function showSection(name) {
    Object.values(sections).forEach(sec => {
        if (sec) {
            sec.classList.add('hidden');
        }
    });
    if (sections[name]) {
        sections[name].classList.remove('hidden');
    }
}

// Form Elements
const form = document.getElementById('research-form');
const topicInput = document.getElementById('topic-input');
const logsContainer = document.getElementById('logs-container');
const statusTitle = document.getElementById('current-status');
const reportContent = document.getElementById('report-content');
const backBtn = document.getElementById('back-btn');

let pollInterval;

// Log Management
function addLog(log) {
    if (!logsContainer) return;
    
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="log-step">${log.step || 'INFO'}</span> ${log.details || log.status || ''}`;
    logsContainer.prepend(div); // Newest top
    
    // Auto-scroll to top
    logsContainer.scrollTop = 0;
}

// Research Functions
async function startResearch(e) {
    e.preventDefault();
    const topic = topicInput ? topicInput.value.trim() : '';
    if (!topic) return;

    // Ensure we're on home page
    showPage('home');

    // UI Reset
    if (logsContainer) logsContainer.innerHTML = '';
    showSection('progress');
    if (statusTitle) statusTitle.textContent = "Initiating Research...";

    try {
        const res = await fetch(`${API_BASE}/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to start research');
        }
        
        const data = await res.json();
        pollProgress(data.task_id);

    } catch (err) {
        console.error("Research error:", err);
        alert("Error: " + err.message);
        showSection('input');
    }
}

function pollProgress(taskId) {
    if (pollInterval) clearInterval(pollInterval);
    
    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/stream/${taskId}`);
            if (!res.ok) throw new Error('Failed to fetch progress');
            
            const logs = await res.json();
            
            // Clear and rebuild logs
            if (logsContainer) {
                logsContainer.innerHTML = '';
                logs.forEach(addLog);
            }

            // Update status
            const lastLog = logs[logs.length - 1];
            if (lastLog) {
                if (statusTitle) {
                    statusTitle.textContent = lastLog.status + "...";
                }
                
                // Check if completed
                if (lastLog.status === 'Completed') {
                    clearInterval(pollInterval);
                    fetchResult(taskId);
                }
            }

        } catch (err) {
            console.error("Polling error", err);
            // Continue polling even on error
        }
    }, 1000);
}

async function fetchResult(taskId) {
    try {
        const res = await fetch(`${API_BASE}/result/${taskId}`);
        if (!res.ok) throw new Error('Failed to fetch result');
        
        const data = await res.json();
        
        if (reportContent) {
            reportContent.innerHTML = data.content_html || '<p>Report content not available.</p>';
        }
        showSection('result');
        
        // Scroll to result
        setTimeout(() => {
            reportContent?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
        
    } catch (err) {
        console.error("Fetch result error:", err);
        alert("Failed to load report: " + err.message);
    }
}

// Event Listeners
if (form) {
    form.addEventListener('submit', startResearch);
}

if (backBtn) {
    backBtn.addEventListener('click', () => {
        if (topicInput) topicInput.value = '';
        showSection('input');
        showPage('home');
    });
}

// Initialize - show home page
document.addEventListener('DOMContentLoaded', () => {
    showPage('home');
    
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (e) => {
        const page = e.state?.page || 'home';
        showPage(page);
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape to go back to input
    if (e.key === 'Escape' && sections.progress && !sections.progress.classList.contains('hidden')) {
        showSection('input');
    }
    
    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (topicInput) {
            topicInput.focus();
            showPage('home');
        }
    }
});

// Add loading state management
function setLoading(isLoading) {
    const btn = document.getElementById('start-btn');
    if (btn) {
        btn.disabled = isLoading;
        if (isLoading) {
            btn.innerHTML = '<span>Processing...</span>';
        } else {
            btn.innerHTML = '<span>Start Research</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        }
    }
}

// Enhanced error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});

// Document Upload & Q&A Functionality
let currentSessionId = null;
let uploadedFiles = [];

// File Upload
const fileInput = document.getElementById('file-input');
const fileUploadArea = document.getElementById('file-upload-area');
const fileList = document.getElementById('file-list');
const uploadForm = document.getElementById('upload-form');
const uploadBtn = document.getElementById('upload-btn');
const uploadStatus = document.getElementById('upload-status');
const qaSection = document.getElementById('qa-section');
const qaForm = document.getElementById('qa-form');
const questionInput = document.getElementById('question-input');
const qaResults = document.getElementById('qa-results');
const sessionInfo = document.getElementById('session-info');

if (fileUploadArea && fileInput) {
    // Click to upload
    fileUploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag and drop
    fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadArea.classList.add('dragover');
    });
    
    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.classList.remove('dragover');
    });
    
    fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });
    
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });
}

function handleFiles(files) {
    const validFiles = files.filter(f => {
        const ext = f.name.split('.').pop().toLowerCase();
        return ['pdf', 'txt', 'md'].includes(ext) && f.size <= 10 * 1024 * 1024; // 10MB
    });
    
    validFiles.forEach(file => {
        if (!uploadedFiles.find(f => f.name === file.name)) {
            uploadedFiles.push(file);
        }
    });
    
    updateFileList();
    updateUploadButton();
}

function updateFileList() {
    if (!fileList) return;
    
    fileList.innerHTML = '';
    uploadedFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <div class="file-item-info">
                <div>
                    <div class="file-item-name">${file.name}</div>
                    <div class="file-item-size">${(file.size / 1024).toFixed(2)} KB</div>
                </div>
            </div>
            <button type="button" class="file-item-remove" onclick="removeFile(${index})">×</button>
        `;
        fileList.appendChild(div);
    });
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    updateFileList();
    updateUploadButton();
}

function updateUploadButton() {
    if (uploadBtn) {
        uploadBtn.disabled = uploadedFiles.length === 0;
    }
}

if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (uploadedFiles.length === 0) return;
        
        const formData = new FormData();
        uploadedFiles.forEach(file => {
            formData.append('files', file);
        });
        if (currentSessionId) {
            formData.append('session_id', currentSessionId);
        }
        
        // Show processing status
        uploadStatus.className = 'upload-status processing';
        uploadStatus.textContent = 'Processing documents...';
        uploadStatus.classList.remove('hidden');
        uploadBtn.disabled = true;
        
        try {
            const res = await fetch(`${API_BASE}/documents/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            const data = await res.json();
            currentSessionId = data.session_id;
            
            // Show success
            uploadStatus.className = 'upload-status success';
            uploadStatus.textContent = `Success: ${data.message}. ${data.total_documents} document(s) ready for questions.`;
            
            // Clear files
            uploadedFiles = [];
            updateFileList();
            updateUploadButton();
            fileInput.value = '';
            
            // Show Q&A section
            if (qaSection) {
                qaSection.classList.remove('hidden');
                updateSessionInfo(data);
            }
            
        } catch (err) {
            uploadStatus.className = 'upload-status error';
            uploadStatus.textContent = `Error: ${err.message}`;
        } finally {
            uploadBtn.disabled = false;
        }
    });
}

function updateSessionInfo(data) {
    if (!sessionInfo) return;
    
    const deleteBtn = document.getElementById('delete-session-btn');
    if (deleteBtn) {
        deleteBtn.classList.remove('hidden');
    }
    
    sessionInfo.innerHTML = `
        <h3>Your Documents</h3>
        <p><strong>Session ID:</strong> <code>${data.session_id}</code></p>
        <p><strong>Documents:</strong> ${data.total_documents}</p>
        <p><strong>Files:</strong> ${data.files_uploaded.join(', ')}</p>
        <div class="delete-btn-wrapper">
            <img src="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=100&h=100&fit=crop" alt="Delete" class="delete-image-large">
            <button id="delete-session-btn" class="delete-session-btn" onclick="deleteSession()">
                Delete All Documents
            </button>
        </div>
    `;
}

async function deleteSession() {
    if (!currentSessionId) {
        alert('No session to delete');
        return;
    }
    
    if (!confirm('Are you sure you want to delete all uploaded documents? This action cannot be undone.')) {
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/documents/session/${currentSessionId}`, {
            method: 'DELETE'
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to delete session');
        }
        
        // Clear session data
        currentSessionId = null;
        uploadedFiles = [];
        
        // Reset UI
        if (sessionInfo) {
            sessionInfo.innerHTML = '';
        }
        if (qaResults) {
            qaResults.innerHTML = '';
        }
        if (qaSection) {
            qaSection.classList.add('hidden');
        }
        if (fileList) {
            fileList.innerHTML = '';
        }
        if (uploadStatus) {
            uploadStatus.classList.add('hidden');
        }
        
        alert('All documents and session data have been deleted successfully.');
        
    } catch (err) {
        alert('Error deleting session: ' + err.message);
    }
}

// Q&A Functionality
if (qaForm) {
    qaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!currentSessionId) {
            alert('Please upload documents first');
            return;
        }
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        const askBtn = document.getElementById('ask-btn');
        if (askBtn) {
            askBtn.disabled = true;
            askBtn.innerHTML = '<span>Processing...</span>';
        }
        
        try {
            const res = await fetch(`${API_BASE}/documents/qa`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    question: question
                })
            });
            
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to get answer');
            }
            
            const data = await res.json();
            
            // Display result
            const resultDiv = document.createElement('div');
            resultDiv.className = 'qa-result';
            resultDiv.innerHTML = `
                <div class="qa-result-question">
                    <span>${question}</span>
                </div>
                <div class="qa-result-answer">${data.answer}</div>
                ${data.sources && data.sources.length > 0 ? `
                    <div class="qa-result-sources">
                        <h4>Sources:</h4>
                        ${data.sources.map(src => `<span class="source-tag">${src}</span>`).join('')}
                    </div>
                ` : ''}
            `;
            
            if (qaResults) {
                qaResults.insertBefore(resultDiv, qaResults.firstChild);
            }
            
            questionInput.value = '';
            
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            if (askBtn) {
                askBtn.disabled = false;
                askBtn.innerHTML = '<span>Ask</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2"/></svg>';
            }
        }
    });
}
