// Content Script - Chạy trong context của trang web
console.log('🔌🔌🔌 VERSION 3.2.0 LOADED - CUSTOM ACCOUNT NAME 🔌🔌🔌');
console.log('🔌 Refinitiv Messenger Data Extractor - v3.2.0 - Custom account name support');

// IMPORTANT: Save original fetch before page scripts can override it
const nativeFetch = window.fetch.bind(window);

let isExtensionActive = true;
let dataBuffer = [];
const API_URL = 'https://ho-dev-ai:3000/api/messenger/data';
const CONFIG_URL = 'https://ho-dev-ai:3000/api/config';

// Crawl account name (fetched from server)
let crawlAccountName = 'Bạn'; // Default fallback
let configFetchAttempts = 0;
const MAX_CONFIG_RETRIES = 3;

// Configuration
const CONFIG = {
    sendInterval: 5000, // Gửi dữ liệu mỗi 5 giây
    maxBufferSize: 50,  // Tối đa 50 items trong buffer
    enableDOMMonitoring: true,
    enableNetworkMonitoring: true,
    enableWebSocketMonitoring: true
};

// Inject script để monitor network requests và WebSocket
function injectScript() {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected.js');
    script.onload = function() {
        this.remove();
    };
    (document.head || document.documentElement).appendChild(script);
}

// Fetch server configuration (crawl account name) with retry logic
async function fetchServerConfig() {
    configFetchAttempts++;
    console.log(`🔄 Fetching server config (attempt ${configFetchAttempts}/${MAX_CONFIG_RETRIES})...`);

    try {
        const response = await nativeFetch(CONFIG_URL, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            const config = await response.json();
            crawlAccountName = config.crawl_account || 'Bạn';
            console.log(`✅ SUCCESS: Crawl account name set to: "${crawlAccountName}"`);
            return true;
        } else {
            console.warn(`⚠️ Server returned ${response.status}, using default: Bạn`);

            // Retry if not max attempts
            if (configFetchAttempts < MAX_CONFIG_RETRIES) {
                const delay = Math.pow(2, configFetchAttempts) * 1000; // Exponential backoff
                console.log(`🔄 Retrying in ${delay/1000} seconds...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return await fetchServerConfig();
            }
            return false;
        }
    } catch (error) {
        console.warn(`❌ Cannot connect to server: ${error.message}`);

        // Retry if not max attempts
        if (configFetchAttempts < MAX_CONFIG_RETRIES) {
            const delay = Math.pow(2, configFetchAttempts) * 1000; // Exponential backoff
            console.log(`🔄 Retrying in ${delay/1000} seconds...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return await fetchServerConfig();
        }

        console.error(`❌ FAILED to fetch config after ${MAX_CONFIG_RETRIES} attempts. Using default: "Bạn"`);
        console.error(`   Make sure server is running: https://ho-dev-ai:3000`);
        return false;
    }
}

// Gửi dữ liệu lên server
async function sendDataToServer(data) {
    try {
        const response = await nativeFetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: data.type,
                data: data.payload,
                timestamp: new Date().toISOString(),
                url: window.location.href
            })
        });

        if (response.ok) {
            console.log(`✅ Sent ${data.type} data to server`);
        } else {
            console.error('❌ Failed to send data:', response.status);
        }
    } catch (error) {
        console.error('❌ Network error sending data:', error);
    }
}

// Buffer và gửi dữ liệu
function addToBuffer(type, payload) {
    if (!isExtensionActive) {
        console.log('⚠️ Extension is not active, skipping data');
        return;
    }

    const dataItem = {
        type: type,
        payload: payload,
        timestamp: new Date().toISOString()
    };

    dataBuffer.push(dataItem);
    console.log(`📊 Added ${type} data to buffer (${dataBuffer.length} items)`, dataItem);

    // Gửi ngay nếu buffer đầy
    if (dataBuffer.length >= CONFIG.maxBufferSize) {
        console.log('🚀 Buffer full, flushing now');
        flushBuffer();
    }
}

// Gửi tất cả dữ liệu trong buffer
async function flushBuffer() {
    if (dataBuffer.length === 0) return;

    const itemsToSend = [...dataBuffer];
    dataBuffer = [];

    for (const item of itemsToSend) {
        await sendDataToServer(item);
        await new Promise(resolve => setTimeout(resolve, 100)); // Delay nhỏ giữa các request
    }
}

// Monitor DOM changes
function setupDOMMonitoring() {
    if (!CONFIG.enableDOMMonitoring) return;

    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            // Monitor message containers
            if (mutation.target.classList && mutation.target.classList.contains('message')) {
                addToBuffer('dom_message', {
                    type: 'message_change',
                    element: mutation.target.outerHTML.substring(0, 1000), // Limit size
                    timestamp: Date.now()
                });
            }

            // Monitor chat room changes
            if (mutation.target.id && mutation.target.id.includes('chat')) {
                addToBuffer('dom_chat', {
                    type: 'chat_change',
                    elementId: mutation.target.id,
                    content: mutation.target.textContent?.substring(0, 500),
                    timestamp: Date.now()
                });
            }

            // Monitor user list changes
            if (mutation.target.classList && (
                mutation.target.classList.contains('user') || 
                mutation.target.classList.contains('contact') ||
                mutation.target.classList.contains('participant')
            )) {
                addToBuffer('dom_user', {
                    type: 'user_change',
                    element: mutation.target.outerHTML.substring(0, 500),
                    timestamp: Date.now()
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'id', 'data-*']
    });

    console.log('👁️ DOM monitoring started');
}

// Monitor custom events từ injected script
function setupCustomEventMonitoring() {
    // Listen for network requests
    window.addEventListener('refinitivMessengerNetworkRequest', (event) => {
        addToBuffer('network_request', event.detail);
    });

    // Listen for WebSocket messages
    window.addEventListener('refinitivMessengerWebSocket', (event) => {
        addToBuffer('websocket_message', event.detail);
    });

    console.log('📡 Custom event monitoring started');
}

// Extract current page data
function extractCurrentPageData() {
    console.log('🔍 Starting data extraction...');

    // Use the improved extraction method
    extractMessagesImproved();
}

// Date parsing utilities
function formatDate(date) {
    // Returns yyyy-mm-dd format
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function convertToISODate(dateString) {
    // Handle various date formats and convert to yyyy-mm-dd
    dateString = dateString.trim();

    // Try DD/MM/YYYY format
    const ddmmyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const match = dateString.match(ddmmyyyyPattern);
    if (match) {
        const day = match[1].padStart(2, '0');
        const month = match[2].padStart(2, '0');
        const year = match[3];
        return `${year}-${month}-${day}`;
    }

    // Try MM/DD/YYYY format
    const mmddyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const matchUS = dateString.match(mmddyyyyPattern);
    if (matchUS) {
        const month = matchUS[1].padStart(2, '0');
        const day = matchUS[2].padStart(2, '0');
        const year = matchUS[3];
        return `${year}-${month}-${day}`;
    }

    // If can't parse, use today
    return formatDate(new Date());
}

function parseDate(dateString) {
    // Parse date strings like "Today", "Yesterday", "Unread messages" to yyyy-mm-dd
    const today = new Date();

    if (dateString === 'Today' || dateString === 'Hôm nay') {
        return formatDate(today);
    } else if (dateString === 'Yesterday' || dateString === 'Hôm qua') {
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return formatDate(yesterday);
    } else if (dateString.includes('Unread messages') || dateString.includes('Tin nhắn chưa đọc')) {
        return formatDate(today);
    } else if (dateString.includes('/')) {
        // Date with slashes (DD/MM/YYYY or MM/DD/YYYY)
        return convertToISODate(dateString);
    } else {
        // Unknown format, use today
        return formatDate(today);
    }
}

// Improved message extraction based on refined script
function extractMessagesImproved() {
    console.log('🔍 Extracting all visible messages...');

    // DON'T click "View History" button - only scrape visible messages
    // This prevents loading old historical data from previous days
    const messages = scrapeMessages(); // Get all visible messages
    sendExtractedData(messages);
}

// Send extracted data to buffer
function sendExtractedData(messages) {
    console.log('📊 Extracted:', {
        messages: messages.length
    });

    const data = {
        timestamp: Date.now(),
        url: window.location.href,
        title: document.title,
        messages: messages
    };

    console.log('📦 Adding to buffer:', data);
    addToBuffer('page_snapshot', data);
}

function scrapeMessages(maxMessages) {
    if (maxMessages) {
        console.log(`📝 Scraping messages (max: ${maxMessages})...`);
    } else {
        console.log(`📝 Scraping all messages...`);
    }

    var results = [];
    var currentName = '';  // Global state - persists across messages
    var currentBank = '';  // Global state - persists across messages
    var currentDate = null; // Start with null to detect if date was found
    var dateWarningShown = false;

    // Get all elements including dividers
    var allElements = document.querySelectorAll('[class*="Divider"], [class*="MessageWithContact"], [class*="OutgoingMessage"], [class*="IncomingMessage"]');

    console.log(`📋 Found ${allElements.length} total elements`);

    allElements.forEach(function(el) {
        // Check for date dividers
        if (el.className.indexOf('Divider') > -1) {
            var dividerText = el.textContent.trim();
            if (dividerText) {
                // Use parseDate to convert "Today", "Yesterday", etc. to yyyy-mm-dd
                currentDate = parseDate(dividerText);
                console.log('📅 Date divider found: "' + dividerText + '" → ' + currentDate);
            }
            return; // Skip to next element
        }

        // Lấy message
        var msgBody = el.querySelector('.message-body');
        if (!msgBody) return;

        var content = msgBody.textContent.trim();
        var time = '';
        var sender = '';

        var timeEl = el.querySelector('[class*="Timestamp"]');
        if (timeEl) {
            time = timeEl.textContent.trim();
        }

        // Check if this is an outgoing message (from current user) or incoming (from other person)
        var isOutgoing = el.className.indexOf('OutgoingMessage') > -1;

        if (isOutgoing) {
            // This is YOUR message - use crawl account name
            sender = crawlAccountName;
            console.log('📤 Outgoing message from: ' + crawlAccountName);
        } else {
            // This is an incoming message - try to find/update contact info
            var nameEl = el.querySelector('[class*="ContactName"] [data-testid="tooltip-container"]');
            var bankEl = el.querySelector('[class*="Company"] [data-testid="tooltip-container"]');

            // If found in this element, update global state
            if (nameEl || bankEl) {
                if (nameEl) {
                    currentName = nameEl.textContent.trim();
                    console.log('👤 Sender updated: ' + currentName);
                }
                if (bankEl) {
                    currentBank = bankEl.textContent.trim();
                }
            }
            // If not found, try parent element
            else if (el.parentElement) {
                nameEl = el.parentElement.querySelector('[class*="ContactName"] [data-testid="tooltip-container"]');
                bankEl = el.parentElement.querySelector('[class*="Company"] [data-testid="tooltip-container"]');

                if (nameEl || bankEl) {
                    if (nameEl) {
                        currentName = nameEl.textContent.trim();
                        console.log('👤 Sender updated (from parent): ' + currentName);
                    }
                    if (bankEl) {
                        currentBank = bankEl.textContent.trim();
                    }
                }
            }
            // Otherwise, keep using the current global state (from previous incoming message)

            sender = currentName + ' - ' + currentBank;
            console.log('📥 Incoming message from: ' + sender);
        }

        // Check if we have a valid date
        if (!currentDate) {
            if (!dateWarningShown) {
                console.warn('⚠️ WARNING: No date divider found! Messages may have incorrect dates.');
                console.warn('   This can happen when viewing old messages without scrolling to see date dividers.');
                console.warn('   Using today\'s date as fallback: ' + formatDate(new Date()));
                dateWarningShown = true;
            }
            // Fallback to today ONLY if no date found
            currentDate = formatDate(new Date());
        }

        // Format: [yyyy-mm-dd HH:MM:SS] (Người gửi): Nội dung
        // Use currentDate from most recent divider
        var formattedMessage = '[' + currentDate + ' ' + time + '] (' + sender + '): ' + content;
        results.push({
            raw: formattedMessage,
            date: currentDate,
            time: time,
            sender: sender,
            content: content,
            name: currentName,
            bank: currentBank
        });
    });

    // Limit to last N messages (only if maxMessages specified)
    if (maxMessages && results.length > maxMessages) {
        var totalFound = results.length;
        results = results.slice(-maxMessages); // Get last N messages
        console.log(`✂️ Limited from ${totalFound} to last ${maxMessages} messages`);
    } else if (!maxMessages) {
        console.log(`✅ No limit applied - keeping all ${results.length} messages`);
    }

    results.forEach(function(msg, i) {
        console.log((i+1) + '. ' + msg.raw);
    });

    console.log('\n✅ Đã scrape ' + results.length + ' tin nhắn!');

    // Copy to clipboard if available (for manual use)
    if (typeof copy === 'function') {
        const textToCopy = results.map(msg => msg.raw).join('\n');
        copy(textToCopy);
        console.log('\n📋 Đã copy ' + results.length + ' tin nhắn vào clipboard!');
    }

    return results;
}

// Manual extraction function for console use
window.extractChatData = function(maxMessages) {
    console.clear();
    if (maxMessages) {
        console.log(`🔍 Extracting last ${maxMessages} messages...`);
        const messages = scrapeMessages(maxMessages);
        console.log('\n📊 Extraction complete!');
        return messages;
    } else {
        console.log('🔍 Extracting with automatic limit (10 messages)...');
        extractMessagesImproved();
    }
}


// Initialize extension
async function initialize() {
    console.log('🚀 Initializing Refinitiv Messenger Data Extractor');

    // Fetch server configuration (crawl account name)
    await fetchServerConfig();

    // Inject monitoring script
    injectScript();

    // Setup monitoring
    setupCustomEventMonitoring();
    
    // Wait for page load then setup DOM monitoring
    // NOTE: We DON'T extract data immediately - only from periodic checks
    // This ensures we only capture NEW messages after server starts
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                setupDOMMonitoring();
                console.log('⏸️ Skipping initial extraction - will start on first periodic check (30s)');
            }, 2000);
        });
    } else {
        setTimeout(() => {
            setupDOMMonitoring();
            console.log('⏸️ Skipping initial extraction - will start on first periodic check (30s)');
        }, 2000);
    }

    // Periodic data extraction
    setInterval(() => {
        if (isExtensionActive) {
            extractCurrentPageData();
        }
    }, 30000); // Every 30 seconds

    // Periodic buffer flush
    setInterval(() => {
        if (isExtensionActive) {
            flushBuffer();
        }
    }, CONFIG.sendInterval);

    // Extract data when page changes
    let lastUrl = window.location.href;
    setInterval(() => {
        if (window.location.href !== lastUrl) {
            lastUrl = window.location.href;
            setTimeout(() => extractCurrentPageData(), 1000);
        }
    }, 1000);
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggleExtension') {
        isExtensionActive = !isExtensionActive;
        sendResponse({ active: isExtensionActive });
        
        if (isExtensionActive) {
            console.log('✅ Extension activated');
            extractCurrentPageData();
        } else {
            console.log('⏸️ Extension paused');
        }
    } else if (request.action === 'extractNow') {
        extractCurrentPageData();
        flushBuffer();
        sendResponse({ success: true });
    } else if (request.action === 'getStatus') {
        sendResponse({ 
            active: isExtensionActive, 
            bufferSize: dataBuffer.length,
            url: window.location.href
        });
    }
});

// Start the extension
initialize();