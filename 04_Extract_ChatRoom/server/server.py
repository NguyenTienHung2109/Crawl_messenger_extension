from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import time
from pathlib import Path
import shutil
import argparse

app = Flask(__name__, static_folder='public')
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "OPTIONS"]}})
PORT = 3000

# Server configuration (set via command line args)
server_config = {
    'crawl_account': 'Bạn'  # Default to Vietnamese "You"
}

# Statistics tracking
stats = {
    'totalRequests': 0,
    'totalMessages': 0,
    'lastActivity': None,
    'startTime': datetime.now()
}

# Create data directory
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)

# Notification queue file (for email service)
notification_queue_file = os.path.join(data_dir, 'notification_queue.jsonl')

# Message deduplication cache file
seen_messages_cache_file = os.path.join(data_dir, 'seen_messages_cache.json')

# Configure Flask to handle large JSON payloads
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB


def format_datetime(dt):
    """Format datetime object to ISO string"""
    return dt.isoformat()


def get_current_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def format_time(dt):
    """Format datetime for logging"""
    return dt.strftime('%H:%M:%S')


def format_date():
    """Format current date as YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')


def humanize_duration(seconds):
    """Convert seconds to human readable duration"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''}"


def load_seen_messages_cache():
    """Load the cache of seen messages from file"""
    try:
        if os.path.exists(seen_messages_cache_file):
            with open(seen_messages_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # Convert list back to set for fast lookup
                return set(cache_data.get('message_hashes', []))
        return set()
    except Exception as e:
        print(f"⚠️ Error loading seen messages cache: {e}")
        return set()


def save_seen_messages_cache(cache_set, max_size=1000):
    """Save the cache of seen messages to file (keep only last max_size entries)"""
    try:
        # Convert set to list and keep only last max_size entries
        cache_list = list(cache_set)
        if len(cache_list) > max_size:
            cache_list = cache_list[-max_size:]  # Keep only most recent

        cache_data = {
            'message_hashes': cache_list,
            'last_updated': get_current_timestamp(),
            'total_cached': len(cache_list)
        }

        with open(seen_messages_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error saving seen messages cache: {e}")


def get_message_hash(message):
    """Generate a unique hash for a message"""
    date = message.get('date', '')
    time = message.get('time', '')
    sender = message.get('sender', '')
    content = message.get('content', '')
    return f"{date}|{time}|{sender}|{content}"


def filter_new_messages(messages, cache):
    """Filter out messages that have been seen before, return only new messages"""
    new_messages = []
    new_hashes = []

    for msg in messages:
        msg_hash = get_message_hash(msg)
        if msg_hash not in cache:
            new_messages.append(msg)
            new_hashes.append(msg_hash)
            cache.add(msg_hash)  # Add to cache immediately

    return new_messages, new_hashes


def write_notification_to_queue(notification_data):
    """Write a notification to the queue file for email service to process"""
    try:
        with open(notification_queue_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(notification_data, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"⚠️ Error writing to notification queue: {e}")


# Endpoint to receive data from extension
@app.route('/api/messenger/data', methods=['POST'])
def receive_messenger_data():
    try:
        body = request.get_json()
        data_type = body.get('type', 'unknown')
        data = body.get('data')
        timestamp = body.get('timestamp', get_current_timestamp())
        url = body.get('url', 'unknown')

        log_entry = {
            'timestamp': timestamp,
            'type': data_type,
            'url': url,
            'data': data,
            'receivedAt': get_current_timestamp()
        }

        # Save to file by date
        date_str = format_date()
        file_name = f'messenger_data_{date_str}.json'
        file_path = os.path.join(data_dir, file_name)

        # Read existing file or create new
        existing_data = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        existing_data = json.loads(content)
            except json.JSONDecodeError as parse_error:
                print(f'JSON parse error, creating new file: {parse_error}')
                # Backup corrupted file
                corrupted_path = f'{file_path}.corrupted.{int(time.time() * 1000)}'
                shutil.move(file_path, corrupted_path)
                existing_data = []

        # Add new data
        existing_data.append(log_entry)

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

        # Update statistics
        stats['totalRequests'] += 1
        stats['lastActivity'] = get_current_timestamp()

        # Deduplication: Load cache and filter new messages
        original_message_count = 0
        new_message_count = 0
        new_messages = []

        if data and 'messages' in data and isinstance(data['messages'], list):
            original_message_count = len(data['messages'])

            # Load cache
            cache = load_seen_messages_cache()

            # Filter to get only new messages
            new_messages, new_hashes = filter_new_messages(data['messages'], cache)
            new_message_count = len(new_messages)

            # Save updated cache
            if new_message_count > 0:
                save_seen_messages_cache(cache)

        stats['totalMessages'] += new_message_count

        # Write notification to queue for email service (ONLY if there are NEW messages)
        if new_message_count > 0:
            write_notification_to_queue({
                'timestamp': timestamp,
                'type': data_type,
                'data': {'messages': new_messages},  # Only new messages
                'message_count': new_message_count,
                'received_at': log_entry['receivedAt']
            })

        # Short log
        current_time = format_time(datetime.now())
        if original_message_count > 0:
            print(f"[{current_time}] 📨 {data_type} | {original_message_count} total | {new_message_count} new | Total unique: {stats['totalMessages']}")
        else:
            print(f"[{current_time}] 📨 {data_type} | No messages")

        # Display new messages (only last 3)
        if new_message_count > 0:
            display_count = min(3, new_message_count)
            for msg in new_messages[-display_count:]:
                display = msg.get('raw', f"{msg.get('sender', 'Unknown')}: {msg.get('content', '')}")
                print(f"  └─ {display}")

        return jsonify({
            'success': True,
            'message': 'Data received successfully',
            'timestamp': log_entry['receivedAt']
        }), 200

    except Exception as error:
        print(f'Error processing data: {error}')
        return jsonify({
            'success': False,
            'error': str(error)
        }), 500


# Endpoint to view collected data
@app.route('/api/messenger/data', methods=['GET'])
def get_messenger_data():
    try:
        date = request.args.get('date', format_date())
        file_name = f'messenger_data_{date}.json'
        file_path = os.path.join(data_dir, file_name)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data), 200
        else:
            return jsonify({'message': f'No data found for date: {date}'}), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 500


# Endpoint to list available data files
@app.route('/api/messenger/files', methods=['GET'])
def get_messenger_files():
    try:
        files = os.listdir(data_dir)
        data_files = [f for f in files if f.startswith('messenger_data_') and f.endswith('.json')]
        return jsonify({'files': data_files}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 500


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'timestamp': get_current_timestamp(),
        'uptime': time.time() - stats['startTime'].timestamp()
    }), 200


# Stats endpoint
@app.route('/api/stats', methods=['GET'])
def get_stats():
    uptime_seconds = (datetime.now() - stats['startTime']).total_seconds()

    return jsonify({
        'totalRequests': stats['totalRequests'],
        'totalMessages': stats['totalMessages'],
        'lastActivity': stats['lastActivity'],
        'startTime': format_datetime(stats['startTime']),
        'uptime': uptime_seconds,
        'uptimeFormatted': humanize_duration(uptime_seconds)
    }), 200


# Config endpoint for extension
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'crawl_account': server_config['crawl_account']
    }), 200


# Serve static files for dashboard
@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Refinitiv Messenger Data Extraction Server')
    parser.add_argument('--crawl_account', type=str, default='Bạn',
                       help='Account name to use for outgoing messages (default: Bạn)')
    args = parser.parse_args()

    # Update server config
    server_config['crawl_account'] = args.crawl_account

    # Check for SSL certificates
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.pem')

    ssl_context = None
    protocol = 'http'
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
        protocol = 'https'
        print(f"🔒 SSL certificates found - using HTTPS")
    else:
        print(f"⚠️  No SSL certificates found - using HTTP (insecure)")
        print(f"   To generate certificates, run: python create_ssl.py")

    print(f"🚀 Server started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Listening on {protocol}://localhost:{PORT}")
    print(f"📊 Data: {data_dir}")
    print(f"📈 Stats: {protocol}://localhost:{PORT}/api/stats")
    print(f"📬 Notification Queue: {notification_queue_file}")
    print(f"👤 Crawl Account: {server_config['crawl_account']}")
    print(f"")
    print(f"ℹ️  Email notifications are handled by email_service.py (run separately)")
    print(f"   To start email service: python email_service.py")
    print(f"\n⏳ Waiting for messages...")

    app.run(host='0.0.0.0', port=PORT, debug=False, ssl_context=ssl_context)
