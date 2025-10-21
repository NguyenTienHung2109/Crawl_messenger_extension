// Injected Script - Chạy trong context của trang web để monitor network và WebSocket

(function() {
    'use strict';

    console.log('🔍 Refinitiv Messenger Network Monitor injected');

    // Monitor XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        this._method = method;
        this._url = url;
        return originalXHROpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(data) {
        const xhr = this;
        
        // Monitor response
        xhr.addEventListener('load', function() {
            try {
                if (xhr._url && xhr._url.includes('refinitiv') || xhr._url.includes('messenger')) {
                    let responseData = '';
                    try {
                        responseData = JSON.parse(xhr.responseText);
                    } catch (e) {
                        responseData = xhr.responseText?.substring(0, 1000);
                    }

                    window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
                        detail: {
                            type: 'xhr_response',
                            method: xhr._method,
                            url: xhr._url,
                            status: xhr.status,
                            response: responseData,
                            timestamp: Date.now()
                        }
                    }));
                }
            } catch (error) {
                console.error('Error monitoring XHR:', error);
            }
        });

        return originalXHRSend.apply(this, arguments);
    };

    // Monitor Fetch API
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const [input, init] = args;
        const url = typeof input === 'string' ? input : input.url;
        
        return originalFetch.apply(this, arguments)
            .then(response => {
                if (url && (url.includes('refinitiv') || url.includes('messenger'))) {
                    // Clone response để không ảnh hưởng đến original
                    const clonedResponse = response.clone();
                    
                    clonedResponse.text().then(text => {
                        let responseData = '';
                        try {
                            responseData = JSON.parse(text);
                        } catch (e) {
                            responseData = text?.substring(0, 1000);
                        }

                        window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
                            detail: {
                                type: 'fetch_response',
                                method: init?.method || 'GET',
                                url: url,
                                status: response.status,
                                response: responseData,
                                timestamp: Date.now()
                            }
                        }));
                    }).catch(console.error);
                }
                
                return response;
            });
    };

    // Monitor WebSocket
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);
        
        ws.addEventListener('open', function(event) {
            window.dispatchEvent(new CustomEvent('refinitivMessengerWebSocket', {
                detail: {
                    type: 'websocket_open',
                    url: url,
                    timestamp: Date.now()
                }
            }));
        });

        ws.addEventListener('message', function(event) {
            let messageData = '';
            try {
                messageData = JSON.parse(event.data);
            } catch (e) {
                messageData = event.data?.substring(0, 1000);
            }

            window.dispatchEvent(new CustomEvent('refinitivMessengerWebSocket', {
                detail: {
                    type: 'websocket_message',
                    url: url,
                    data: messageData,
                    timestamp: Date.now()
                }
            }));
        });

        ws.addEventListener('close', function(event) {
            window.dispatchEvent(new CustomEvent('refinitivMessengerWebSocket', {
                detail: {
                    type: 'websocket_close',
                    url: url,
                    code: event.code,
                    reason: event.reason,
                    timestamp: Date.now()
                }
            }));
        });

        ws.addEventListener('error', function(event) {
            window.dispatchEvent(new CustomEvent('refinitivMessengerWebSocket', {
                detail: {
                    type: 'websocket_error',
                    url: url,
                    error: event.error?.toString() || 'Unknown error',
                    timestamp: Date.now()
                }
            }));
        });

        return ws;
    };

    // Monitor localStorage changes (if messenger uses it)
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {
        if (key.toLowerCase().includes('messenger') || key.toLowerCase().includes('refinitiv')) {
            window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
                detail: {
                    type: 'localstorage_set',
                    key: key,
                    value: value?.substring(0, 500),
                    timestamp: Date.now()
                }
            }));
        }
        return originalSetItem.apply(this, arguments);
    };

    // Monitor sessionStorage changes
    const originalSessionSetItem = Storage.prototype.setItem;
    if (window.sessionStorage) {
        window.sessionStorage.setItem = function(key, value) {
            if (key.toLowerCase().includes('messenger') || key.toLowerCase().includes('refinitiv')) {
                window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
                    detail: {
                        type: 'sessionstorage_set',
                        key: key,
                        value: value?.substring(0, 500),
                        timestamp: Date.now()
                    }
                }));
            }
            return originalSessionSetItem.apply(this, arguments);
        };
    }

    // Monitor console.log for debugging (optional)
    const originalConsoleLog = console.log;
    console.log = function(...args) {
        // Check if any argument contains messenger-related keywords
        const messageStr = args.join(' ').toLowerCase();
        if (messageStr.includes('messenger') || messageStr.includes('chat') || messageStr.includes('message')) {
            window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
                detail: {
                    type: 'console_log',
                    message: args.join(' ').substring(0, 500),
                    timestamp: Date.now()
                }
            }));
        }
        return originalConsoleLog.apply(this, arguments);
    };

    console.log('✅ Network monitoring hooks installed');

})();