// Main JavaScript functionality for EIP Sentiment Analyzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (100MB limit)
                const maxSize = 100 * 1024 * 1024; // 100MB in bytes
                if (file.size > maxSize) {
                    alert('File size exceeds 100MB limit. Please choose a smaller file.');
                    fileInput.value = '';
                    return;
                }

                // Check file type
                if (!file.name.toLowerCase().endsWith('.csv')) {
                    alert('Please select a CSV file.');
                    fileInput.value = '';
                    return;
                }

                // Display file info
                displayFileInfo(file);
            }
        });
    }

    // Auto-refresh functionality for job status pages
    if (window.location.pathname.includes('/job/')) {
        const jobId = window.location.pathname.split('/job/')[1];
        if (jobId && !jobId.includes('?')) {
            // Check if job is still processing
            const statusBadge = document.getElementById('statusBadge');
            if (statusBadge && (statusBadge.textContent.includes('Processing') || statusBadge.textContent.includes('Queued'))) {
                startStatusPolling(jobId);
            }
        }
    }
});

function displayFileInfo(file) {
    const fileSize = (file.size / 1024 / 1024).toFixed(2); // Convert to MB
    const lastModified = new Date(file.lastModified).toLocaleDateString();
    
    // Create or update file info display
    let fileInfoDiv = document.getElementById('fileInfo');
    if (!fileInfoDiv) {
        fileInfoDiv = document.createElement('div');
        fileInfoDiv.id = 'fileInfo';
        fileInfoDiv.className = 'alert alert-info mt-3';
        document.getElementById('file').parentNode.appendChild(fileInfoDiv);
    }
    
    fileInfoDiv.innerHTML = `
        <h6 class="alert-heading">
            <i class="fas fa-info-circle me-2"></i>File Information
        </h6>
        <div class="row">
            <div class="col-md-6">
                <strong>Name:</strong> ${file.name}<br>
                <strong>Size:</strong> ${fileSize} MB
            </div>
            <div class="col-md-6">
                <strong>Type:</strong> ${file.type || 'text/csv'}<br>
                <strong>Modified:</strong> ${lastModified}
            </div>
        </div>
    `;
}

function startStatusPolling(jobId) {
    const pollInterval = setInterval(function() {
        fetch(`/api/job/${jobId}/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                updateJobStatus(data);
                
                // Stop polling if job is completed or failed
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(pollInterval);
                    // Reload page to show final results
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Error fetching job status:', error);
                // Stop polling on error
                clearInterval(pollInterval);
            });
    }, 3000); // Poll every 3 seconds
}

function updateJobStatus(data) {
    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = data.progress + '%';
        progressBar.textContent = data.progress + '%';
        
        // Add animation classes based on status
        if (data.status === 'processing') {
            progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        } else if (data.status === 'completed') {
            progressBar.className = 'progress-bar bg-success';
        } else if (data.status === 'error') {
            progressBar.className = 'progress-bar bg-danger';
        }
    }
    
    // Update status badge
    const statusBadge = document.getElementById('statusBadge');
    if (statusBadge) {
        let badgeHtml = '';
        switch (data.status) {
            case 'completed':
                badgeHtml = '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Completed</span>';
                break;
            case 'error':
                badgeHtml = '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle me-1"></i>Error</span>';
                break;
            case 'processing':
                badgeHtml = '<span class="badge bg-primary"><i class="fas fa-spinner fa-spin me-1"></i>Processing</span>';
                break;
            default:
                badgeHtml = '<span class="badge bg-secondary"><i class="fas fa-clock me-1"></i>Queued</span>';
        }
        statusBadge.innerHTML = badgeHtml;
    }
    
    // Update current stage
    const currentStage = document.getElementById('currentStage');
    if (currentStage && data.stage) {
        currentStage.textContent = data.stage;
    }
}

// Utility function to format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Add smooth scrolling to anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading states to buttons
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            submitBtn.disabled = true;
            
            // Re-enable button after 30 seconds as fallback
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 30000);
        }
    });
});
