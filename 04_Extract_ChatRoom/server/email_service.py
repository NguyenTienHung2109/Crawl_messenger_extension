#!/usr/bin/env python3
"""
Email Notification Service
--------------------------
Standalone service that monitors for new messenger data and sends email notifications.

This service:
1. Monitors notification_queue.jsonl for new data events
2. Tracks what has been emailed via email_checkpoint.json
3. Sends email summaries at configured intervals or on events
4. Runs independently from the web server

Usage:
    python email_service.py                    # Run in polling mode (default)
    python email_service.py --mode schedule    # Run in scheduled mode (time-based)
    python email_service.py --mode event       # Run in event-driven mode
"""

import os
import json
import time
import argparse
from datetime import datetime, timedelta
import threading
import schedule
from pathlib import Path

# Email providers
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False


class EmailService:
    def __init__(self, server_dir=None):
        """Initialize the email service"""
        self.server_dir = server_dir or os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.server_dir, 'data')
        self.queue_file = os.path.join(self.data_dir, 'notification_queue.jsonl')
        self.checkpoint_file = os.path.join(self.data_dir, 'email_checkpoint.json')

        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        # Load email configuration
        self.email_config = self.load_email_config()

        # Load checkpoint
        self.checkpoint = self.load_checkpoint()

        # Statistics
        self.stats = {
            'emails_sent': 0,
            'messages_processed': 0,
            'service_start_time': datetime.now(),
            'last_email_sent': None
        }

        print(f"📧 Email Service initialized")
        print(f"📂 Data directory: {self.data_dir}")
        print(f"📋 Queue file: {self.queue_file}")
        print(f"📌 Checkpoint file: {self.checkpoint_file}")

    def load_email_config(self):
        """Load email configuration from email_config.json"""
        config_path = os.path.join(self.server_dir, 'email_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if config.get('enabled'):
                        print(f"✅ Email enabled (interval: {config.get('interval_minutes', 5)} min)")
                        return config
                    else:
                        print("⚠️  Email disabled in config")
                        return config
            else:
                print(f"⚠️  Config not found: {config_path}")
                return {'enabled': False}
        except Exception as e:
            print(f"❌ Error loading email config: {e}")
            return {'enabled': False}

    def load_checkpoint(self):
        """Load the checkpoint tracking what has been emailed"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    print(f"📌 Loaded checkpoint: {checkpoint.get('last_notification_id', 0)} notifications processed")
                    return checkpoint
            else:
                print("📌 No checkpoint found, starting fresh")
                return {
                    'last_notification_id': 0,
                    'last_email_timestamp': None,
                    'created_at': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"⚠️  Error loading checkpoint: {e}")
            return {'last_notification_id': 0, 'last_email_timestamp': None}

    def save_checkpoint(self):
        """Save the checkpoint to disk"""
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving checkpoint: {e}")

    def read_new_notifications(self):
        """Read new notifications from the queue since last checkpoint"""
        if not os.path.exists(self.queue_file):
            return []

        try:
            notifications = []
            last_id = self.checkpoint.get('last_notification_id', 0)

            with open(self.queue_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num <= last_id:
                        continue

                    try:
                        notification = json.loads(line.strip())
                        notifications.append({
                            'id': line_num,
                            'notification': notification
                        })
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Skipping malformed notification at line {line_num}: {e}")

            return notifications
        except Exception as e:
            print(f"❌ Error reading notifications: {e}")
            return []

    # REMOVED: postprocess_message_raw() is no longer needed
    # Date processing is now handled correctly in content.js during extraction
    # All dates are already in yyyy-mm-dd format when they arrive at the server

    def collect_messages_from_notifications(self, notifications):
        """Collect unique messages from a list of notifications"""
        seen_messages = set()
        unique_messages = []

        for notif_entry in notifications:
            notification = notif_entry['notification']
            data = notification.get('data', {})

            if data and isinstance(data, dict):
                messages = data.get('messages', [])

                for msg in messages:
                    msg_key = f"{msg.get('date', '')}|{msg.get('time', '')}|{msg.get('sender', '')}|{msg.get('content', '')}"
                    if msg_key not in seen_messages:
                        seen_messages.add(msg_key)
                        unique_messages.append(msg)

        return unique_messages

    def send_email(self, messages):
        """Send email with collected messages"""
        if not self.email_config.get('enabled'):
            print("📧 Email disabled, skipping send")
            return False

        provider = self.email_config.get('provider', 'smtp').lower()

        if provider == 'sendgrid':
            return self._send_email_sendgrid(messages)
        else:
            return self._send_email_smtp(messages)

    def _send_email_sendgrid(self, messages):
        """Send email using SendGrid API"""
        if not SENDGRID_AVAILABLE:
            print("❌ SendGrid library not installed. Run: pip install sendgrid")
            return False

        try:
            # Get SendGrid settings
            api_key = self.email_config.get('sendgrid_api_key')
            from_email = self.email_config.get('from_email')
            from_name = self.email_config.get('from_name', 'Refinitiv Messenger Bot')
            recipients = self.email_config.get('recipient_emails', [])

            if not api_key or api_key == 'PASTE_YOUR_SENDGRID_API_KEY_HERE':
                print("⚠️  SendGrid API key not configured. Update email_config.json")
                return False

            if not from_email or not recipients:
                print("⚠️  Email config incomplete (from_email or recipient_emails missing)")
                return False

            # Build email body
            message_count = len(messages)
            subject = self.email_config.get('subject_prefix', 'Refinitiv Messenger Data')

            body_parts = []
            body_parts.append(f"📊 Data Summary Report")
            body_parts.append(f"=" * 50)
            body_parts.append(f"")
            body_parts.append(f"🕒 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            body_parts.append(f"")
            body_parts.append(f"📈 New Messages: {message_count}")
            body_parts.append(f"📧 Emails Sent (session): {self.stats['emails_sent']}")
            body_parts.append(f"📊 Messages Processed (session): {self.stats['messages_processed']}")
            body_parts.append(f"")

            if messages:
                body_parts.append(f"📝 New Messages:")
                body_parts.append(f"-" * 50)

                messages_sorted = sorted(messages, key=lambda m: f"{m.get('date', '')}|{m.get('time', '')}")

                for msg in messages_sorted:
                    raw_message = msg.get('raw', '')
                    if raw_message:
                        # Raw message already has correct date format from content.js
                        body_parts.append(raw_message)
                    else:
                        sender = msg.get('sender', 'Unknown')
                        content = msg.get('content', '')
                        time_str = msg.get('time', '')
                        date_str = msg.get('date', '')
                        body_parts.append(f"[{date_str} {time_str}] ({sender}): {content[:200]}{'...' if len(content) > 200 else ''}")
            else:
                body_parts.append(f"ℹ️  No new messages")

            body = "\n".join(body_parts)

            # Create SendGrid message
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=[To(email) for email in recipients],
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )

            # Send via SendGrid
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)

            # Update stats
            self.stats['emails_sent'] += 1
            self.stats['last_email_sent'] = datetime.now().isoformat()

            recipient_list = ', '.join(recipients)
            print(f"✅ Email sent via SendGrid to {len(recipients)} recipient(s): {recipient_list}")
            print(f"   Status: {response.status_code}")
            return True

        except Exception as e:
            print(f"❌ Error sending email via SendGrid: {e}")
            return False

    def _send_email_smtp(self, messages):
        """Send email using SMTP (Gmail)"""
        if not SMTP_AVAILABLE:
            print("❌ SMTP libraries not available")
            return False

        try:
            # Get email settings
            gmail_user = self.email_config.get('gmail_user')
            gmail_password = self.email_config.get('gmail_app_password')
            recipients = self.email_config.get('recipient_emails', [])

            if not isinstance(recipients, list):
                recipients = [recipients]

            recipients = [r for r in recipients if r]

            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)

            if not all([gmail_user, gmail_password]) or not recipients:
                print("⚠️  Email config incomplete")
                return False

            # Build email body
            message_count = len(messages)
            subject = self.email_config.get('subject_prefix', 'Refinitiv Messenger Data')

            body_parts = []
            body_parts.append(f"📊 Data Summary Report")
            body_parts.append(f"=" * 50)
            body_parts.append(f"")
            body_parts.append(f"🕒 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            body_parts.append(f"")
            body_parts.append(f"📈 New Messages: {message_count}")
            body_parts.append(f"📧 Emails Sent (session): {self.stats['emails_sent']}")
            body_parts.append(f"📊 Messages Processed (session): {self.stats['messages_processed']}")
            body_parts.append(f"")

            if messages:
                body_parts.append(f"📝 New Messages:")
                body_parts.append(f"-" * 50)

                messages_sorted = sorted(messages, key=lambda m: f"{m.get('date', '')}|{m.get('time', '')}")

                for msg in messages_sorted:
                    raw_message = msg.get('raw', '')
                    if raw_message:
                        # Raw message already has correct date format from content.js
                        body_parts.append(raw_message)
                    else:
                        sender = msg.get('sender', 'Unknown')
                        content = msg.get('content', '')
                        time_str = msg.get('time', '')
                        date_str = msg.get('date', '')
                        body_parts.append(f"[{date_str} {time_str}] ({sender}): {content[:200]}{'...' if len(content) > 200 else ''}")
            else:
                body_parts.append(f"ℹ️  No new messages")

            body = "\n".join(body_parts)

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.send_message(msg, from_addr=gmail_user, to_addrs=recipients)

            # Update stats
            self.stats['emails_sent'] += 1
            self.stats['last_email_sent'] = datetime.now().isoformat()

            recipient_list = ', '.join(recipients)
            print(f"✅ Email sent via SMTP to {len(recipients)} recipient(s): {recipient_list}")
            return True

        except Exception as e:
            print(f"❌ Error sending email via SMTP: {e}")
            return False

    def process_notifications(self):
        """Process new notifications and send email if needed"""
        notifications = self.read_new_notifications()

        if not notifications:
            return 0

        print(f"📬 Found {len(notifications)} new notification(s)")

        # Collect messages
        messages = self.collect_messages_from_notifications(notifications)

        if messages:
            print(f"📝 Collected {len(messages)} unique message(s)")

            # Send email
            if self.send_email(messages):
                # Update checkpoint only after successful email
                last_notif_id = notifications[-1]['id']
                self.checkpoint['last_notification_id'] = last_notif_id
                self.checkpoint['last_email_timestamp'] = datetime.now().isoformat()
                self.save_checkpoint()

                self.stats['messages_processed'] += len(messages)
                print(f"📌 Checkpoint updated: {last_notif_id}")
        else:
            print("ℹ️  No messages in notifications")

        return len(messages)

    def run_scheduled(self):
        """Run in scheduled mode (time-based, like the original server)"""
        interval = self.email_config.get('interval_minutes', 5)

        print(f"🕐 Starting scheduled mode (every {interval} minutes)")
        print(f"ℹ️  Note: Emails will only be sent when there are NEW messages (not already emailed)")
        schedule.every(interval).minutes.do(self.process_notifications)

        # Run immediately on start
        print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Running initial check...")
        self.process_notifications()

        next_run = datetime.now() + timedelta(minutes=interval)
        print(f"⏰ Next scheduled check: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        while True:
            schedule.run_pending()

            # Show next run time when a job completes
            if schedule.jobs and schedule.jobs[0].should_run:
                next_run = datetime.now() + timedelta(minutes=interval)
                print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Scheduled check triggered")

            time.sleep(1)

    def run_polling(self):
        """Run in polling mode (check for new notifications periodically)"""
        poll_interval = 10  # seconds

        print(f"🔄 Starting polling mode (check every {poll_interval}s)")

        while True:
            try:
                self.process_notifications()
                time.sleep(poll_interval)
            except KeyboardInterrupt:
                print("\n👋 Shutting down email service...")
                break
            except Exception as e:
                print(f"❌ Error in polling loop: {e}")
                time.sleep(poll_interval)

    def run_event_driven(self):
        """Run in event-driven mode (process immediately when notifications arrive)"""
        print(f"⚡ Starting event-driven mode")
        print(f"⚠️  Note: This mode polls every 5 seconds (true file watching requires additional deps)")

        last_size = 0
        if os.path.exists(self.queue_file):
            last_size = os.path.getsize(self.queue_file)

        while True:
            try:
                if os.path.exists(self.queue_file):
                    current_size = os.path.getsize(self.queue_file)
                    if current_size > last_size:
                        print("📬 New data detected!")
                        self.process_notifications()
                        last_size = current_size

                time.sleep(5)
            except KeyboardInterrupt:
                print("\n👋 Shutting down email service...")
                break
            except Exception as e:
                print(f"❌ Error in event loop: {e}")
                time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description='Email Notification Service')
    parser.add_argument('--mode', choices=['schedule', 'polling', 'event'], default='polling',
                       help='Run mode: schedule (time-based), polling (check periodically), event (on new data)')
    parser.add_argument('--dir', help='Server directory (default: script directory)')

    args = parser.parse_args()

    print("=" * 60)
    print("📧 Email Notification Service")
    print("=" * 60)
    print(f"🚀 Starting in {args.mode} mode")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    service = EmailService(server_dir=args.dir)

    if not service.email_config.get('enabled'):
        print("⚠️  Email is disabled in config. Enable it in email_config.json to use this service.")
        return

    try:
        if args.mode == 'schedule':
            service.run_scheduled()
        elif args.mode == 'polling':
            service.run_polling()
        elif args.mode == 'event':
            service.run_event_driven()
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")


if __name__ == '__main__':
    main()
