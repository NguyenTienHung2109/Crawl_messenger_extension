# Refinitiv Messenger Data Extraction Server

This server collects data from the Refinitiv Messenger Chrome extension and sends email notifications.

## Prerequisites

- Python 3.7+
- Gmail account with App Password enabled

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure email settings in `email_config.json`:
```json
{
  "enabled": true,
  "gmail_user": "your-email@gmail.com",
  "gmail_app_password": "your-app-password",
  "recipient_emails": ["recipient@gmail.com"],
  "interval_minutes": 30,
  "subject_prefix": "Refinitiv Messenger Data Summary",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

### How to Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Generate an app password for "Mail"
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
6. Use it in `email_config.json` (with or without spaces)

## Usage

### Start the Data Collection Server

**Default (uses "Bạn" for your messages):**
```bash
python server.py
```

**Custom account name:**
```bash
python server.py --crawl_account "Your Name"
```

**With bank name:**
```bash
python server.py --crawl_account "Your Name - Your Bank"
```

The server will run on `http://localhost:3000`

### Start the Email Service

**Option 1: Polling Mode (Recommended)**
```bash
python email_service.py
```
- Checks for new messages every 10 seconds
- Sends email immediately when new messages are found

**Option 2: Scheduled Mode**
```bash
python email_service.py --mode schedule
```
- Sends emails at fixed intervals (configured in `email_config.json`)
- Default: every 30 minutes

**Option 3: Event-Driven Mode**
```bash
python email_service.py --mode event
```
- Watches for file changes and sends email immediately

### Running Both Services

Open two terminal windows:

**Terminal 1 - Data Server:**
```bash
cd "D:\07.FI_crawldata\04_Extract_ChatRoom\server"
python server.py --crawl_account "Dzung Nguyen"
```

**Terminal 2 - Email Service:**
```bash
cd "D:\07.FI_crawldata\04_Extract_ChatRoom\server"
python email_service.py
```

## Data Storage

All collected data is stored in the `data/` folder:

- `notification_queue.jsonl` - Message queue for email service
- `seen_messages_cache.json` - Tracks processed messages (prevents duplicates)
- `email_checkpoint.json` - Tracks last email sent
- `messenger_data_YYYY-MM-DD.json` - Daily message archives

## API Endpoints

- `GET /health` - Server health check
- `GET /api/stats` - View statistics
- `GET /api/config` - Get server configuration (crawl account name)
- `POST /api/messenger/data` - Receive data from extension (used by extension)
- `GET /api/messenger/data?date=YYYY-MM-DD` - Get messages by date
- `GET /api/messenger/files` - List available data files

## Troubleshooting

### Email Not Sending

1. **Check email service is running:**
   - Look for: `✅ Email enabled (interval: 30 min)`

2. **SMTP connection errors:**
   - Port 587 blocked → Try port 465 (SSL)
   - Firewall blocking → Check Windows Firewall settings
   - Wrong password → Verify Gmail App Password

3. **Test email manually:**
   ```bash
   python test_email.py
   ```

### No Messages Received

1. **Check Chrome extension is loaded:**
   - Navigate to `chrome://extensions/`
   - Verify extension is enabled

2. **Check server is running:**
   - Visit `http://localhost:3000/health`
   - Should return `{"status": "OK"}`

3. **Check console logs:**
   - Open DevTools (F12) on Refinitiv Messenger
   - Look for: `👤 Crawl account name set to: ...`

### Duplicate Messages

1. **Clear cache to start fresh:**
   ```bash
   rm data/seen_messages_cache.json
   ```

2. **Clear email checkpoint to re-send:**
   ```bash
   rm data/email_checkpoint.json
   ```

## Command Line Options

### server.py
```bash
python server.py --help

Options:
  --crawl_account CRAWL_ACCOUNT
                        Account name to use for outgoing messages (default: Bạn)
```

### email_service.py
```bash
python email_service.py --help

Options:
  --mode {schedule,polling,event}
                        Run mode (default: polling)
  --dir DIR            Server directory (default: script directory)
```

## File Structure

```
server/
├── server.py                    # Main data collection server
├── email_service.py             # Email notification service
├── email_config.json            # Email configuration
├── requirements.txt             # Python dependencies
├── test_email.py               # Email testing utility
├── data/                       # Data storage
│   ├── notification_queue.jsonl
│   ├── seen_messages_cache.json
│   ├── email_checkpoint.json
│   └── messenger_data_*.json
└── public/                     # Dashboard files (optional)
```

## Support

For issues or questions, check the logs in both terminal windows for error messages.
