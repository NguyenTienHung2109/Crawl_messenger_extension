# 🚀 Hướng dẫn cài đặt chi tiết

## Bước 1: Chuẩn bị môi trường

### Yêu cầu hệ thống:
- **Node.js** version 14+ ([Download](https://nodejs.org/))
- **Chrome Browser** (hoặc Edge, Firefox)
- **Windows/macOS/Linux**

### Kiểm tra Node.js:
```bash
node --version
npm --version
```

## Bước 2: Cài đặt API Server

### 2.1. Mở Terminal/Command Prompt

```bash
# Windows: Win + R, gõ "cmd"
# macOS: Cmd + Space, gõ "Terminal"
# Linux: Ctrl + Alt + T
```

### 2.2. Di chuyển vào thư mục project

```bash
cd "D:\OneDrive - NGAN HANG TMCP HANG HAI VIET NAM (MSB)\01_Projects\03.FI_crawldata\04_Extract_ChatRoom"
cd server
```

### 2.3. Cài đặt dependencies

```bash
npm install
```

Bạn sẽ thấy output như:
```
npm notice created a lockfile as package-lock.json
npm WARN refinitiv-messenger-api@1.0.0 No repository field.

added 57 packages from 42 contributors and audited 57 packages in 3.2s
found 0 vulnerabilities
```

### 2.4. Khởi chạy server

```bash
npm start
```

**Output thành công:**
```
🚀 Refinitiv Messenger API Server running on http://localhost:3000
📊 Data will be saved to: D:\...\server\data
🔍 View data at: http://localhost:3000/api/messenger/data
```

### 2.5. Kiểm tra server

Mở browser và vào: **http://localhost:3000/health**

Sẽ thấy:
```json
{
  "status": "OK",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "uptime": 1.234
}
```

## Bước 3: Cài đặt Browser Extension

### 3.1. Mở Chrome Extensions

1. Mở **Google Chrome**
2. Gõ `chrome://extensions/` vào address bar
3. Nhấn Enter

### 3.2. Bật Developer Mode

1. Tìm toggle **"Developer mode"** ở góc trên bên phải
2. Click để bật (màu xanh)

### 3.3. Load Extension

1. Click nút **"Load unpacked"**
2. Navigate đến thư mục project
3. Chọn thư mục `extension/`
4. Click **"Select Folder"**

### 3.4. Verify Extension

Extension sẽ xuất hiện với:
- **Name**: "Refinitiv Messenger Data Extractor"
- **Version**: "1.0.0"
- **Status**: "Enabled"
- **Icon**: 📊 trên thanh toolbar

## Bước 4: Sử dụng Extension

### 4.1. Truy cập Refinitiv Messenger

1. Mở tab mới
2. Vào **https://messenger.refinitiv.com/messenger/**
3. Đăng nhập tài khoản của bạn

### 4.2. Kích hoạt Extension

1. Click vào icon 📊 trên toolbar
2. Popup sẽ hiện:
   ```
   📊 Refinitiv Messenger
   Data Extractor
   
   ⏸️ Extension is PAUSED
   
   Status: Paused
   Buffer Size: 0
   Current URL: https://messenger.refinitiv.com...
   Server: Online ✅
   ```

3. Click **"Start Extension"**

### 4.3. Verify hoạt động

Popup sẽ chuyển thành:
```
✅ Extension is ACTIVE

Status: Active
Buffer Size: 5
Current URL: https://messenger.refinitiv.com...
Server: Online ✅
```

## Bước 5: Monitor dữ liệu

### 5.1. Mở Dashboard

1. Vào **http://localhost:3000**
2. Hoặc click **"Open Dashboard"** trong extension popup

### 5.2. Dashboard sẽ hiển thị:

```
📊 Refinitiv Messenger Data Monitor

✅ Server is running. Extension data will appear here in real-time.

Total Entries: 25
Last Update: 10:30:45
Data Types: 4

[Load Data] [Refresh] [Clear Display] [Auto Refresh (5s)]
```

### 5.3. Kiểm tra dữ liệu

Trong vài phút, bạn sẽ thấy dữ liệu xuất hiện:
```
2024-01-01 10:30:45
Type: page_snapshot
URL: https://messenger.refinitiv.com/messenger/
{
  "timestamp": 1704103845000,
  "userInfo": [...],
  "chatRooms": [...],
  "messages": [...]
}
```

## ❗ Troubleshooting

### Server không start được

**Lỗi: `EADDRINUSE :::3000`**
```bash
# Port 3000 đang được sử dụng, kill process:
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F

# Hoặc đổi port trong server.js:
const PORT = 3001;
```

**Lỗi: `MODULE_NOT_FOUND`**
```bash
# Cài đặt lại dependencies:
rm -rf node_modules package-lock.json
npm install
```

### Extension không load được

**Lỗi: "Manifest file is missing or unreadable"**
- Đảm bảo chọn đúng thư mục `extension/`
- Kiểm tra file `manifest.json` tồn tại

**Lỗi: "This extension may have been corrupted"**
1. Remove extension
2. Restart Chrome
3. Load lại extension

### Extension không hoạt động

**Popup hiện "Content script not loaded"**
1. Refresh trang messenger.refinitiv.com
2. Restart extension trong chrome://extensions
3. Check Console (F12) cho error messages

**Server status hiện "Offline ❌"**
1. Kiểm tra server đang chạy
2. Check firewall/antivirus blocking port 3000
3. Try disable browser security extensions

### Không nhận được dữ liệu

**Buffer Size luôn = 0**
1. Check network requests trong DevTools (F12 → Network)
2. Verify trang đã load hoàn toàn
3. Try click "Extract Data Now"

**Dashboard không hiển thị dữ liệu**
1. Check file trong `server/data/`
2. Verify date picker đúng ngày
3. Check server console logs

## 🔄 Khởi động lại sau khi reboot

### Tự động (Recommended):

**Windows - Tạo batch file:**
```batch
# start_server.bat
@echo off
cd /d "D:\OneDrive - NGAN HANG TMCP HANG HAI VIET NAM (MSB)\01_Projects\03.FI_crawldata\04_Extract_ChatRoom\server"
npm start
pause
```

**macOS/Linux - Tạo shell script:**
```bash
#!/bin/bash
cd "/path/to/04_Extract_ChatRoom/server"
npm start
```

### Thủ công:
1. Mở terminal
2. `cd server`
3. `npm start`
4. Extension tự động hoạt động khi vào trang messenger

## 📞 Hỗ trợ

Nếu gặp vấn đề:

1. **Check logs**:
   - Browser Console (F12)
   - Server terminal output
   
2. **Verify setup**:
   - Node.js version
   - Port availability
   - File permissions

3. **Common solutions**:
   - Restart browser
   - Restart server
   - Clear browser cache
   - Reinstall extension