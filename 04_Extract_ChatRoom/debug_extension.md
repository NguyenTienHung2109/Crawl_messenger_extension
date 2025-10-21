# Debug Extension - Step by Step

## Bước 1: Kiểm tra Extension có load không

1. Mở trang messenger.refinitiv.com
2. Nhấn F12 (Developer Tools)  
3. Vào tab Console
4. Tìm messages:
   ```
   🔌 Refinitiv Messenger Data Extractor loaded
   🔍 Refinitiv Messenger Network Monitor injected
   🚀 Initializing Refinitiv Messenger Data Extractor
   👁️ DOM monitoring started
   📡 Custom event monitoring started
   ```

## Bước 2: Kiểm tra Extension Status

1. Click vào icon extension 📊
2. Popup phải hiển thị:
   - Status: Active (không phải Paused)
   - Buffer Size: > 0 (có dữ liệu chờ gửi)
   - Current URL: messenger.refinitiv.com
   - Server: Online ✅

## Bước 3: Kiểm tra Network Requests

Trong DevTools:
1. Tab Network
2. Tìm requests đến localhost:3000/api/messenger/data
3. Nếu không có → Extension không gửi data
4. Nếu có nhưng 500 error → Server issue

## Bước 4: Kiểm tra Console Errors

Tìm các error messages:
- "Content script not loaded"
- Network errors (CORS, connection refused)
- JavaScript errors trong content.js

## Bước 5: Manual Testing

Trong Console, test manual:
```javascript
// Test content script có load không
window.dispatchEvent(new CustomEvent('refinitivMessengerNetworkRequest', {
    detail: { type: 'test', data: 'manual test' }
}));

// Test DOM extraction
document.querySelectorAll('[class*="message"]').length
document.querySelectorAll('[class*="chat"]').length
```

## Bước 6: Server Logs

Kiểm tra server console có messages:
- `[HH:mm:ss] Received [type] data:`
- Nếu không có → Extension không gửi
- Nếu có error → JSON parsing issue

## Common Issues:

1. **Extension chưa Start**: Click "Start Extension"
2. **CORS Error**: Server cần enable CORS (đã config)
3. **Wrong selectors**: Trang web thay đổi structure
4. **Network blocked**: Firewall/antivirus block localhost:3000
5. **Multiple instances**: Nhiều tabs cùng chạy extension

## Solutions:

1. **Restart Extension**: chrome://extensions → reload
2. **Restart Server**: Ctrl+C và npm start lại  
3. **Clear cache**: Hard reload (Ctrl+Shift+R)
4. **Check permissions**: Extension needs activeTab permission