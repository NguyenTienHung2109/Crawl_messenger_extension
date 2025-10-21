# Refinitiv Messenger Data Extractor

📊 **Hệ thống tự động thu thập và theo dõi dữ liệu từ Refinitiv Messenger**

## 🎯 Mục đích

Giải pháp này bao gồm:
- **Browser Extension**: Thu thập dữ liệu real-time từ trang messenger.refinitiv.com
- **API Server**: Nhận và lưu trữ dữ liệu từ extension
- **Dashboard**: Giao diện web để monitor và xem dữ liệu đã thu thập

## 🏗️ Kiến trúc

```
Browser Extension → HTTP API → Local Server → JSON Files
        ↓
    Web Dashboard (Real-time Monitor)
```

## 📁 Cấu trúc thư mục

```
04_Extract_ChatRoom/
├── extension/              # Browser Extension
│   ├── manifest.json      # Extension configuration
│   ├── content.js         # Main content script
│   ├── injected.js        # Network monitoring script
│   ├── popup.html         # Extension popup UI
│   ├── popup.js           # Popup functionality
│   └── background.js      # Background service worker
├── server/                # API Server
│   ├── server.js          # Express.js server
│   ├── package.json       # Dependencies
│   ├── data/              # Data storage (auto-created)
│   └── public/
│       └── index.html     # Dashboard UI
├── sample_data/           # Sample HTML files for reference
└── README.md             # This file
```

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt API Server

```bash
# Di chuyển vào thư mục server
cd server

# Cài đặt dependencies
npm install

# Khởi chạy server
npm start

# Hoặc chạy trong development mode
npm run dev
```

Server sẽ chạy tại: **http://localhost:3000**

### 2. Cài đặt Browser Extension

1. Mở Chrome và vào `chrome://extensions/`
2. Bật **Developer mode** (góc trên bên phải)
3. Click **Load unpacked**
4. Chọn thư mục `extension/`
5. Extension sẽ xuất hiện trong danh sách

### 3. Sử dụng Extension

1. Mở trang **https://messenger.refinitiv.com/messenger/**
2. Đăng nhập vào tài khoản
3. Click vào icon extension trên thanh công cụ
4. Click **Start Extension** để bắt đầu thu thập dữ liệu

## 📊 Các loại dữ liệu thu thập

### 1. **DOM Changes** 
- Tin nhắn mới
- Thay đổi chat room
- Cập nhật danh sách người dùng

### 2. **Network Requests**
- API calls (XHR/Fetch)
- WebSocket messages
- Authentication requests

### 3. **Page Data**
- User information
- Chat rooms list
- Visible messages
- Contact list

### 4. **Storage Events**
- LocalStorage changes
- SessionStorage updates

## 🖥️ Dashboard

Truy cập dashboard tại: **http://localhost:3000**

**Tính năng:**
- ✅ Real-time data monitoring
- 📈 Statistics và metrics
- 📅 Filter theo ngày
- 🔄 Auto-refresh
- 📋 Export dữ liệu

## 📡 API Endpoints

### POST `/api/messenger/data`
Nhận dữ liệu từ extension
```json
{
  "type": "dom_message",
  "data": { ... },
  "timestamp": "2024-01-01T10:00:00Z",
  "url": "https://messenger.refinitiv.com/messenger/"
}
```

### GET `/api/messenger/data?date=2024-01-01`
Lấy dữ liệu theo ngày

### GET `/api/messenger/files`
Danh sách các file dữ liệu

### GET `/health`
Kiểm tra trạng thái server

## 🔧 Configuration

### Extension Settings
Extension tự động cấu hình với:
- **Server URL**: http://localhost:3000
- **Send Interval**: 5 giây
- **Buffer Size**: 50 items
- **Extraction Interval**: 30 giây

### Server Settings
Trong `server/server.js`:
```javascript
const PORT = 3000;           // Server port
const dataDir = './data';    // Data storage directory
```

## 📝 Dữ liệu lưu trữ

Dữ liệu được lưu trong `server/data/` theo format:
```
messenger_data_2024-01-01.json
messenger_data_2024-01-02.json
...
```

Mỗi entry có format:
```json
{
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "dom_message",
  "url": "https://messenger.refinitiv.com/messenger/",
  "data": { ... },
  "receivedAt": "2024-01-01T10:00:01.000Z"
}
```

## 🛠️ Troubleshooting

### Extension không hoạt động
1. Kiểm tra Console trong DevTools (F12)
2. Đảm bảo đang trên trang messenger.refinitiv.com
3. Restart extension trong chrome://extensions

### Server không kết nối được
1. Kiểm tra server đang chạy: `http://localhost:3000/health`
2. Kiểm tra CORS settings
3. Đảm bảo port 3000 không bị blocked

### Không nhận được dữ liệu
1. Kiểm tra network requests trong DevTools
2. Verify extension popup shows "Active" status
3. Check server logs trong console

## 🔒 Bảo mật

- Extension chỉ hoạt động trên domain messenger.refinitiv.com
- Dữ liệu được lưu local, không gửi ra ngoài
- API server chỉ listen trên localhost
- Sensitive data được truncate để tránh leak

## 🎯 Các tình huống sử dụng

1. **Monitor Chat Activity**: Theo dõi hoạt động chat real-time
2. **Data Analysis**: Phân tích pattern và xu hướng
3. **Compliance**: Audit trail cho các communication
4. **Research**: Thu thập dữ liệu cho nghiên cứu

## 📈 Performance

- **Memory Usage**: ~10-20MB cho extension
- **CPU Usage**: Minimal, chỉ khi có thay đổi
- **Network**: ~1-5KB/minute data transfer
- **Storage**: ~1-10MB/ngày tùy hoạt động

## 🔄 Updates

Để update extension:
1. Sửa code trong thư mục extension/
2. Vào chrome://extensions/
3. Click nút reload cho extension

## 📞 Support

Nếu gặp vấn đề:
1. Check logs trong browser console
2. Check server logs
3. Verify network connectivity
4. Restart cả extension và server

---

**⚠️ Lưu ý quan trọng:**
- Chỉ sử dụng cho mục đích hợp pháp và tuân thủ terms of service
- Không thu thập thông tin nhạy cảm của người khác
- Đảm bảo tuân thủ quy định về privacy và data protection