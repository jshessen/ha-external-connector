// Main JavaScript for HA External Connector Web Interface

class HAConnectorWebApp {
    constructor() {
        this.baseUrl = window.location.origin;
        this.apiUrl = `${this.baseUrl}/api`;

        // Initialize event listeners
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.showNotification('An unexpected error occurred', 'error');
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('ajax-form')) {
                e.preventDefault();
                this.handleFormSubmission(e.target);
            }
        });
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                throw new Error(`API call failed: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call error:', error);
            this.showNotification(`API Error: ${error.message}`, 'error');
            throw error;
        }
    }

    async handleFormSubmission(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;

        // Show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';

        try {
            const endpoint = form.getAttribute('data-endpoint');
            const method = form.getAttribute('data-method') || 'POST';

            const response = await this.apiCall(endpoint, {
                method: method,
                body: JSON.stringify(data)
            });

            this.showNotification(response.message || 'Operation completed successfully', 'success');

            // Check for redirect
            if (response.redirect) {
                window.location.href = response.redirect;
            }

        } catch (error) {  // eslint-disable-line no-unused-vars
            this.showNotification('Operation failed. Please try again.', 'error');
        } finally {
            // Restore button state
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';

        const icon = {
            'success': 'check-circle-fill',
            'error': 'exclamation-circle-fill',
            'warning': 'exclamation-triangle-fill',
            'info': 'info-circle-fill'
        }[type] || 'info-circle-fill';

        notification.innerHTML = `
            <i class="bi bi-${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    async loadIntegrationStatus(integrationName) {
        try {
            const status = await this.apiCall(`/integrations/${integrationName}`);
            return status;
        } catch (error) {
            console.error(`Failed to load status for ${integrationName}:`, error);
            return null;
        }
    }

    async toggleIntegration(integrationName, enable = true) {
        const action = enable ? 'enable' : 'disable';

        try {
            const response = await this.apiCall(`/integrations/${integrationName}/${action}`, {
                method: 'POST'
            });

            this.showNotification(response.message, 'success');

            // Refresh the page or update the UI
            window.location.reload();

        } catch (error) {  // eslint-disable-line no-unused-vars
            this.showNotification(`Failed to ${action} integration`, 'error');
        }
    }

    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    getStatusIcon(status) {
        const icons = {
            'healthy': 'check-circle-fill text-success',
            'enabled': 'check-circle-fill text-success',
            'disabled': 'x-circle-fill text-secondary',
            'warning': 'exclamation-triangle-fill text-warning',
            'error': 'exclamation-circle-fill text-danger'
        };
        return icons[status] || 'question-circle-fill text-muted';
    }

    // WebSocket connection for real-time updates
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
        case 'status_update':
            this.updateStatusDisplay(data.payload);
            break;
        case 'log_entry':
            this.addLogEntry(data.payload);
            break;
        case 'notification':
            this.showNotification(data.payload.message, data.payload.type);
            break;
        }
    }

    updateStatusDisplay(statusData) {
        // Update status indicators on the page
        const statusElements = document.querySelectorAll(`[data-status="${statusData.service}"]`);
        statusElements.forEach(element => {
            element.textContent = statusData.status;
            element.className = `badge bg-${this.getStatusColor(statusData.status)}`;
        });
    }

    getStatusColor(status) {
        const colors = {
            'healthy': 'success',
            'enabled': 'success',
            'disabled': 'secondary',
            'warning': 'warning',
            'error': 'danger'
        };
        return colors[status] || 'secondary';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.haApp = new HAConnectorWebApp();

    // Connect WebSocket for real-time updates if supported
    if ('WebSocket' in window) {
        window.haApp.connectWebSocket();
    }
});

// Global utility functions
function _confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function _copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.haApp.showNotification('Copied to clipboard', 'success');
    }).catch(() => {
        window.haApp.showNotification('Failed to copy to clipboard', 'error');
    });
}
