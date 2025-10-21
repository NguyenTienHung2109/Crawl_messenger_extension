// Background Service Worker
console.log('🔧 Refinitiv Messenger Extension Background Script loaded');

// Extension installation/update handler
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Extension installed/updated:', details.reason);
    
    // Set default settings
    chrome.storage.local.set({
        extensionEnabled: true,
        serverUrl: 'https://ho-dev-ai:3000',
        extractionInterval: 30000, // 30 seconds
        maxBufferSize: 50
    });
});

// Note: chrome.action.onClicked is disabled because we have a popup defined in manifest.json
// If you need to handle clicks, remove the popup from manifest.json

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request.action, 'from:', sender.tab?.url || 'popup');
    
    switch (request.action) {
        case 'backgroundTest':
            sendResponse({ success: true, message: 'Background script is working' });
            break;
            
        case 'getSettings':
            chrome.storage.local.get([
                'extensionEnabled',
                'serverUrl',
                'extractionInterval',
                'maxBufferSize'
            ], (result) => {
                sendResponse(result);
            });
            return true; // Keep message channel open for async response
            
        case 'saveSettings':
            chrome.storage.local.set(request.settings, () => {
                sendResponse({ success: true });
            });
            return true;
            
        case 'logData':
            // Log data to console for debugging
            console.log('Data received from content script:', request.data);
            sendResponse({ success: true });
            break;
            
        default:
            console.log('Unknown action:', request.action);
            sendResponse({ success: false, error: 'Unknown action' });
    }
});

// Monitor tab changes to reinject content script if needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes('messenger.refinitiv.com')) {
        console.log('Refinitiv Messenger tab updated:', tab.url);
        
        // Optionally inject content script manually if needed
        // chrome.scripting.executeScript({
        //     target: { tabId: tabId },
        //     files: ['content.js']
        // });
    }
});

// Handle extension unload
chrome.runtime.onSuspend.addListener(() => {
    console.log('Extension is being suspended');
});

// Periodic cleanup (if needed)
chrome.alarms.create('cleanup', { periodInMinutes: 60 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'cleanup') {
        console.log('Running periodic cleanup');
        // Add any cleanup logic here
    }
});

console.log('✅ Background script initialization complete');