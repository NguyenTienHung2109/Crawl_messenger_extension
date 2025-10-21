#!/usr/bin/env python3
"""
Cleanup Notification Queue
---------------------------
Removes duplicate messages from notification_queue.jsonl

This script:
1. Reads all notifications from notification_queue.jsonl
2. Deduplicates messages across all notifications
3. Creates a clean version with only unique messages
4. Backs up the original file

Usage:
    python cleanup_queue.py
"""

import os
import json
from datetime import datetime
import shutil


def get_message_hash(message):
    """Generate a unique hash for a message"""
    date = message.get('date', '')
    time = message.get('time', '')
    sender = message.get('sender', '')
    content = message.get('content', '')
    return f"{date}|{time}|{sender}|{content}"


def cleanup_notification_queue():
    """Clean up the notification queue file by removing duplicates"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    queue_file = os.path.join(data_dir, 'notification_queue.jsonl')

    print("=" * 60)
    print("🧹 Notification Queue Cleanup")
    print("=" * 60)
    print()

    # Check if file exists
    if not os.path.exists(queue_file):
        print(f"⚠️  Queue file not found: {queue_file}")
        print("Nothing to clean up.")
        return

    # Get file size
    file_size = os.path.getsize(queue_file)
    print(f"📁 Original file: {queue_file}")
    print(f"📊 Original size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print()

    # Read all notifications
    print("1️⃣  Reading notifications...")
    notifications = []
    try:
        with open(queue_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    notification = json.loads(line.strip())
                    notifications.append(notification)
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Skipping malformed line {line_num}: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"✅ Read {len(notifications)} notifications")
    print()

    # Count original messages
    original_message_count = 0
    for notif in notifications:
        if notif.get('data') and isinstance(notif['data'], dict):
            messages = notif['data'].get('messages', [])
            original_message_count += len(messages)

    print(f"📊 Original message count: {original_message_count:,}")
    print()

    # Deduplicate messages
    print("2️⃣  Deduplicating messages...")
    seen_messages = set()
    unique_messages = []
    duplicate_count = 0

    for notif in notifications:
        if notif.get('data') and isinstance(notif['data'], dict):
            messages = notif['data'].get('messages', [])

            for msg in messages:
                msg_hash = get_message_hash(msg)
                if msg_hash not in seen_messages:
                    seen_messages.add(msg_hash)
                    unique_messages.append(msg)
                else:
                    duplicate_count += 1

    new_message_count = len(unique_messages)
    print(f"✅ Found {new_message_count:,} unique messages")
    print(f"🗑️  Removed {duplicate_count:,} duplicates")
    print()

    # Calculate reduction
    reduction_percent = (1 - new_message_count / original_message_count) * 100 if original_message_count > 0 else 0
    print(f"📉 Reduction: {reduction_percent:.1f}%")
    print()

    # Create new cleaned notification
    print("3️⃣  Creating cleaned notification...")
    cleaned_notification = {
        'timestamp': datetime.now().isoformat(),
        'type': 'cleanup',
        'data': {
            'messages': unique_messages
        },
        'message_count': new_message_count,
        'received_at': datetime.now().isoformat(),
        'cleanup_info': {
            'original_notifications': len(notifications),
            'original_messages': original_message_count,
            'unique_messages': new_message_count,
            'duplicates_removed': duplicate_count,
            'cleaned_at': datetime.now().isoformat()
        }
    }

    # Backup original file
    print("4️⃣  Backing up original file...")
    backup_path = f"{queue_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(queue_file, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return

    print()

    # Write cleaned version
    print("5️⃣  Writing cleaned version...")
    try:
        with open(queue_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(cleaned_notification, ensure_ascii=False) + '\n')
        print(f"✅ Cleaned file written")
    except Exception as e:
        print(f"❌ Error writing cleaned file: {e}")
        print(f"💡 Restoring from backup...")
        shutil.copy2(backup_path, queue_file)
        return

    # Get new file size
    new_file_size = os.path.getsize(queue_file)
    size_reduction = (1 - new_file_size / file_size) * 100 if file_size > 0 else 0

    print()
    print("=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)
    print()
    print(f"📊 Results:")
    print(f"   Original size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print(f"   New size: {new_file_size:,} bytes ({new_file_size / 1024:.2f} KB)")
    print(f"   Size reduction: {size_reduction:.1f}%")
    print()
    print(f"   Original notifications: {len(notifications)}")
    print(f"   New notifications: 1 (consolidated)")
    print()
    print(f"   Original messages: {original_message_count:,}")
    print(f"   Unique messages: {new_message_count:,}")
    print(f"   Duplicates removed: {duplicate_count:,}")
    print()
    print(f"💾 Backup saved to: {backup_path}")
    print()

    # Also create a seen_messages_cache.json with all the unique messages
    print("6️⃣  Creating seen messages cache...")
    cache_file = os.path.join(data_dir, 'seen_messages_cache.json')
    try:
        message_hashes = [get_message_hash(msg) for msg in unique_messages]
        cache_data = {
            'message_hashes': message_hashes,
            'last_updated': datetime.now().isoformat(),
            'total_cached': len(message_hashes),
            'created_by': 'cleanup_queue.py'
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Cache file created: {cache_file}")
        print(f"   Cached {len(message_hashes)} message hashes")
    except Exception as e:
        print(f"⚠️  Could not create cache file: {e}")

    print()
    print("🎉 All done! Your notification queue is now clean and deduplicated.")
    print()


if __name__ == '__main__':
    cleanup_notification_queue()
