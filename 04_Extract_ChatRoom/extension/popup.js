// Popup Script
const API_URL = 'https://ho-dev-ai:3000';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize popup
    updateStatus();
    checkServerConnection();

    // Event listeners
    document.getElementById('toggle-btn').addEventListener('click', toggleExtension);
    document.getElementById('extract-btn').addEventListener('click', extractDataNow);
    document.getElementById('test-server-btn').addEventListener('click', testServerConnection);
    document.getElementById('view-data-btn').addEventListener('click', viewCollectedData);
    document.getElementById('server-link').addEventListener('click', () => {
        chrome.tabs.create({ url: API_URL });
    });
    document.getElementById('dashboard-link').addEventListener('click', () => {
        chrome.tabs.create({ url: `${API_URL}/index.html` });
    });

    // Auto refresh status every 5 seconds
    setInterval(updateStatus, 5000);
});

async function updateStatus() {
    try {
        // Get active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab || !tab.url.includes('messenger.refinitiv.com')) {
            showError('Please navigate to messenger.refinitiv.com to use this extension');
            return;
        }

        // Hide error if we're on the right page
        hideError();

        // Send message to content script
        chrome.tabs.sendMessage(tab.id, { action: 'getStatus' }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error getting status:', chrome.runtime.lastError);
                updateStatusDisplay(false, 0, tab.url, 'Content script not loaded');
                return;
            }

            if (response) {
                updateStatusDisplay(response.active, response.bufferSize, response.url, 'Connected');
            } else {
                updateStatusDisplay(false, 0, tab.url, 'No response');
            }
        });
    } catch (error) {
        console.error('Error updating status:', error);
        showError('Error updating status: ' + error.message);
    }
}

function updateStatusDisplay(active, bufferSize, url, connectionStatus) {
    const statusDiv = document.getElementById('status');
    const extensionStatus = document.getElementById('extension-status');
    const bufferSizeSpan = document.getElementById('buffer-size');
    const currentUrlSpan = document.getElementById('current-url');
    const toggleBtn = document.getElementById('toggle-btn');

    if (active) {
        statusDiv.className = 'status active';
        statusDiv.textContent = '✅ Extension is ACTIVE';
        toggleBtn.textContent = 'Pause Extension';
        toggleBtn.className = 'btn-warning';
        extensionStatus.textContent = 'Active';
    } else {
        statusDiv.className = 'status inactive';
        statusDiv.textContent = '⏸️ Extension is PAUSED';
        toggleBtn.textContent = 'Start Extension';
        toggleBtn.className = 'btn-success';
        extensionStatus.textContent = 'Paused';
    }

    bufferSizeSpan.textContent = bufferSize || 0;
    currentUrlSpan.textContent = url ? url.substring(0, 30) + '...' : 'Unknown';
}

async function toggleExtension() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab || !tab.url.includes('messenger.refinitiv.com')) {
            showError('Please navigate to messenger.refinitiv.com first');
            return;
        }

        chrome.tabs.sendMessage(tab.id, { action: 'toggleExtension' }, (response) => {
            if (chrome.runtime.lastError) {
                showError('Failed to toggle extension: ' + chrome.runtime.lastError.message);
                return;
            }

            if (response) {
                updateStatus();
                showMessage(response.active ? 'Extension started' : 'Extension paused');
            }
        });
    } catch (error) {
        showError('Error toggling extension: ' + error.message);
    }
}

async function extractDataNow() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab || !tab.url.includes('messenger.refinitiv.com')) {
            showError('Please navigate to messenger.refinitiv.com first');
            return;
        }

        chrome.tabs.sendMessage(tab.id, { action: 'extractNow' }, (response) => {
            if (chrome.runtime.lastError) {
                showError('Failed to extract data: ' + chrome.runtime.lastError.message);
                return;
            }

            if (response && response.success) {
                showMessage('Data extraction completed and sent to server');
                updateStatus();
            } else {
                showError('Failed to extract data');
            }
        });
    } catch (error) {
        showError('Error extracting data: ' + error.message);
    }
}

async function testServerConnection() {
    const serverStatus = document.getElementById('server-status');
    serverStatus.textContent = 'Testing...';
    serverStatus.style.color = '#ffc107';

    try {
        const response = await fetch(`${API_URL}/health`);
        
        if (response.ok) {
            const data = await response.json();
            serverStatus.textContent = 'Connected ✅';
            serverStatus.style.color = '#28a745';
            showMessage(`Server is running. Uptime: ${Math.floor(data.uptime)}s`);
        } else {
            serverStatus.textContent = 'Error ❌';
            serverStatus.style.color = '#dc3545';
            showError(`Server responded with status: ${response.status}`);
        }
    } catch (error) {
        serverStatus.textContent = 'Offline ❌';
        serverStatus.style.color = '#dc3545';
        showError('Cannot connect to server. Make sure the server is running on https://ho-dev-ai:3000');
    }
}

async function viewCollectedData() {
    chrome.tabs.create({ url: `${API_URL}/index.html` });
}

async function checkServerConnection() {
    const serverStatus = document.getElementById('server-status');
    
    try {
        const response = await fetch(`${API_URL}/health`, { 
            method: 'GET',
            mode: 'cors'
        });
        
        if (response.ok) {
            serverStatus.textContent = 'Online ✅';
            serverStatus.style.color = '#28a745';
        } else {
            serverStatus.textContent = 'Error ❌';
            serverStatus.style.color = '#dc3545';
        }
    } catch (error) {
        serverStatus.textContent = 'Offline ❌';
        serverStatus.style.color = '#dc3545';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function hideError() {
    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none';
}

function showMessage(message) {
    // Create temporary message element
    const messageDiv = document.createElement('div');
    messageDiv.className = 'status active';
    messageDiv.textContent = '✅ ' + message;
    messageDiv.style.marginBottom = '10px';
    
    const statusDiv = document.getElementById('status');
    statusDiv.parentNode.insertBefore(messageDiv, statusDiv.nextSibling);
    
    // Remove after 3 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}