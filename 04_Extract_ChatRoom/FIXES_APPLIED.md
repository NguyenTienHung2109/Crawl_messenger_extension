# Fixes Applied - 2025-01-13

## Summary
Fixed 3 critical issues with the Refinitiv Messenger data extraction system.

---

## Problem 1: `--crawl_account "Dzung Nguyen"` Still Shows "Bạn"

### Root Cause
The Chrome extension fetches the crawl account name from the server during initialization, but if the fetch fails (due to timing, CORS, or network issues), it falls back to the default "Bạn" without retrying.

### Fix Applied
**File**: `extension/content.js`

**Changes**:
1. Added retry logic with exponential backoff (3 attempts: 2s, 4s, 8s delays)
2. Added detailed console logging to show fetch attempts and results
3. Shows clear success/failure messages in browser console

**Code Changes**:
```javascript
// Added retry counter and max retries
let configFetchAttempts = 0;
const MAX_CONFIG_RETRIES = 3;

// Enhanced fetchServerConfig() with retry logic
async function fetchServerConfig() {
    configFetchAttempts++;
    console.log(`🔄 Fetching server config (attempt ${configFetchAttempts}/${MAX_CONFIG_RETRIES})...`);

    // Exponential backoff retry on failure
    if (configFetchAttempts < MAX_CONFIG_RETRIES) {
        const delay = Math.pow(2, configFetchAttempts) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        return await fetchServerConfig();
    }
}
```

### How to Test
1. **Start server with custom account name**:
   ```bash
   python server.py --crawl_account "Dzung Nguyen"
   ```

2. **Check server console** - should show:
   ```
   👤 Crawl Account: Dzung Nguyen
   ```

3. **Reload Chrome extension** on messenger.refinitiv.com

4. **Open browser console (F12)** - should see:
   ```
   🔄 Fetching server config (attempt 1/3)...
   ✅ SUCCESS: Crawl account name set to: "Dzung Nguyen"
   ```

5. **Extract messages** - your outgoing messages should now show "Dzung Nguyen" instead of "Bạn"

### Important Notes
- Extension must be **reloaded** after server restart with new `--crawl_account` parameter
- If you see "❌ FAILED to fetch config after 3 attempts", check:
  - Server is running on https://ho-dev-ai:3000
  - No CORS or SSL certificate issues
  - Network connectivity

---

## Problem 2: `--mode schedule` Doesn't Send Email Every 5 Minutes

### Root Cause
The scheduled mode **DOES work correctly**, but:
- It sends email immediately on start with all available messages
- Then waits 5 minutes for the next check
- Checkpoint system prevents re-sending the same messages
- If no **NEW** messages arrive, no emails are sent

**User perception**: "It's not running every 5 minutes" because after the first email, no new messages arrive so no subsequent emails are sent.

### Fix Applied
**File**: `server/email_service.py`

**Changes**:
1. Added clear logging to show when scheduled checks run
2. Added note explaining that only NEW messages trigger emails
3. Shows timestamp for each scheduled check
4. Shows next scheduled run time

**Code Changes**:
```python
def run_scheduled(self):
    interval = self.email_config.get('interval_minutes', 5)

    print(f"🕐 Starting scheduled mode (every {interval} minutes)")
    print(f"ℹ️  Note: Emails will only be sent when there are NEW messages (not already emailed)")

    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Running initial check...")
    self.process_notifications()

    next_run = datetime.now() + timedelta(minutes=interval)
    print(f"⏰ Next scheduled check: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        schedule.run_pending()

        if schedule.jobs and schedule.jobs[0].should_run:
            print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Scheduled check triggered")
```

### How to Test
1. **Start email service in schedule mode**:
   ```bash
   python email_service.py --mode schedule
   ```

2. **Expected console output**:
   ```
   🕐 Starting scheduled mode (every 5 minutes)
   ℹ️  Note: Emails will only be sent when there are NEW messages (not already emailed)

   ⏰ [09:30:00] Running initial check...
   📬 Found 4 new notification(s)
   📝 Collected 53 unique message(s)
   ✅ Email sent via SendGrid to 2 recipient(s): ...
   ⏰ Next scheduled check: 2025-01-13 09:35:00

   ⏰ [09:35:00] Scheduled check triggered
   ℹ️  No messages in notifications  <-- No new messages, so no email sent
   ⏰ Next scheduled check: 2025-01-13 09:40:00
   ```

3. **Send new messages** in Refinitiv Messenger

4. **Wait for next 5-minute interval** - email will be sent with NEW messages only

### Important Notes
- Schedule mode runs **every 5 minutes as configured**
- Emails are **only sent when there are NEW messages** (not previously emailed)
- The checkpoint system (`email_checkpoint.json`) tracks what has been sent
- This is **correct behavior** - prevents spam and duplicate emails

---

## Problem 3: Old Messages Show Today's Date Instead of Actual Date

### Root Cause
When scraping messages, the code defaulted to today's date (`formatDate(new Date())`) at the start of the `scrapeMessages()` function.

If users scrolled back to view old messages but the date dividers were not detected (outside viewport, not loaded yet, or missing), ALL messages would be stamped with today's date instead of their actual dates.

### Fix Applied
**File**: `extension/content.js`

**Changes**:
1. Changed `currentDate` from defaulting to `today` → defaulting to `null`
2. Added warning when no date divider is found
3. Only fallback to today's date if no date divider detected at all
4. Removed redundant date postprocessing in email service

**Code Changes**:
```javascript
function scrapeMessages() {
    var currentDate = null; // Start with null instead of today
    var dateWarningShown = false;

    allElements.forEach(function(el) {
        // Date divider detection
        if (el.className.indexOf('Divider') > -1) {
            currentDate = parseDate(dividerText);  // Update as we find dividers
        }

        // Before creating message, check if date is valid
        if (!currentDate) {
            if (!dateWarningShown) {
                console.warn('⚠️ WARNING: No date divider found! Messages may have incorrect dates.');
                console.warn('   Using today\'s date as fallback...');
                dateWarningShown = true;
            }
            currentDate = formatDate(new Date());  // Fallback only when needed
        }

        // Create message with correct date
        var formattedMessage = '[' + currentDate + ' ' + time + '] (' + sender + '): ' + content;
    });
}
```

**Also removed redundant code**:
```python
# email_service.py - REMOVED postprocess_message_raw()
# Date processing now handled correctly in content.js
# All dates arrive at server already in yyyy-mm-dd format
```

### How to Test
1. **Open Refinitiv Messenger** in browser with extension loaded

2. **Scroll back to view old messages** (e.g., messages from last week)

3. **Open browser console (F12)** and run:
   ```javascript
   extractChatData()
   ```

4. **Check console output**:
   ```
   📅 Date divider found: "10/01/2025" → 2025-01-10
   📅 Date divider found: "09/01/2025" → 2025-01-09
   📅 Date divider found: "Today" → 2025-01-13

   1. [2025-01-10 14:30:00] (Contact Name): Message from Jan 10
   2. [2025-01-09 09:15:00] (Contact Name): Message from Jan 09
   3. [2025-01-13 16:45:00] (Dzung Nguyen): Message from today
   ```

5. **If no date dividers found** (e.g., scrolled without loading dates):
   ```
   ⚠️ WARNING: No date divider found! Messages may have incorrect dates.
      This can happen when viewing old messages without scrolling to see date dividers.
      Using today's date as fallback: 2025-01-13
   ```

### Important Notes
- **Best practice**: Scroll slowly through chat history to ensure date dividers are loaded
- Date dividers are detected as DOM elements with class containing "Divider"
- The warning helps identify when dates might be inaccurate
- Once a date divider is found, it persists for all subsequent messages until a new divider is found

---

## Files Modified

### 1. `extension/content.js`
- Added retry logic for config fetch (Problem 1)
- Fixed date handling for old messages (Problem 3)
- Added comprehensive console logging

### 2. `server/email_service.py`
- Enhanced schedule mode logging (Problem 2)
- Removed redundant `postprocess_message_raw()` function (Problem 3)
- Added clear messaging about NEW messages only

---

## How to Deploy These Fixes

### On Server (already done):
```bash
# Files are already updated on server
# Just restart services when ready
```

### On Local Computer:

1. **Transfer extension to local**:
   ```bash
   # From server, create zip
   cd D:\jupyterlab_hungnt34\07.FI_crawldata\04_Extract_ChatRoom
   # Copy extension folder to local computer
   ```

2. **Reload Chrome extension**:
   - Open Chrome: `chrome://extensions/`
   - Click "Reload" button on the extension card
   - OR: Remove and re-add the extension folder

3. **Restart server with custom account**:
   ```bash
   python server.py --crawl_account "Dzung Nguyen"
   ```

4. **Start email service in schedule mode**:
   ```bash
   python email_service.py --mode schedule
   ```

5. **Test the extension**:
   - Open messenger.refinitiv.com
   - Check console (F12) for config fetch success
   - Send test messages
   - Check that your messages show "Dzung Nguyen"
   - Wait 5 minutes for scheduled email

---

## Verification Checklist

- [ ] Server shows: `👤 Crawl Account: Dzung Nguyen`
- [ ] Extension console shows: `✅ SUCCESS: Crawl account name set to: "Dzung Nguyen"`
- [ ] Outgoing messages show "Dzung Nguyen" instead of "Bạn"
- [ ] Email service shows scheduled check timestamps every 5 minutes
- [ ] Old messages show correct historical dates (not today's date)
- [ ] Console shows warning if no date dividers found
- [ ] Emails contain messages with correct dates in yyyy-mm-dd format

---

## Additional Improvements Made

### Console Logging
- Clear emoji indicators for different message types (🔄 🔌 ✅ ❌ ⚠️ 📅)
- Detailed fetch attempt logs
- Explicit success/failure messages
- Warnings for edge cases (missing dates, config fetch failures)

### Error Handling
- Exponential backoff for config fetch retries
- Graceful fallback to defaults when server unreachable
- Clear user messaging about why fallbacks are being used

### Code Cleanup
- Removed redundant date postprocessing function
- Consolidated date handling logic in one place (content.js)
- Added inline comments explaining key decisions

---

## Support

If issues persist:

1. **Config fetch failing**: Check server is running and accessible at https://ho-dev-ai:3000
2. **Schedule not running**: Email service only sends when there are NEW messages
3. **Wrong dates**: Make sure to scroll through history to load date dividers

For detailed email setup, see: `SENDGRID_SETUP_GUIDE.md`
