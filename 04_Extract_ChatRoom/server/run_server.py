#!/usr/bin/env python3
"""
Helper script to run the server with different configurations.
This is the Python equivalent of npm scripts in package.json.
"""

import sys
import subprocess
import os

def run_dev():
    """Run server in development mode with auto-reload"""
    print("Starting server in development mode with auto-reload...")
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = '1'

    # Use Flask's built-in reloader
    subprocess.run([sys.executable, 'server.py'], env=env)

def run_prod():
    """Run server in production mode"""
    print("Starting server in production mode...")
    try:
        # Try to use gunicorn if available
        subprocess.run([
            'gunicorn',
            '-w', '4',
            '-b', '0.0.0.0:3000',
            '--timeout', '120',
            'server:app'
        ])
    except FileNotFoundError:
        print("Gunicorn not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'gunicorn'])
        print("Please run this script again.")

def run_simple():
    """Run server in simple mode (default)"""
    print("Starting server...")
    subprocess.run([sys.executable, 'server.py'])

def run_email_service():
    """Run email notification service"""
    print("Starting email notification service...")
    subprocess.run([sys.executable, 'email_service.py'])

def run_email_scheduled():
    """Run email service in scheduled mode"""
    print("Starting email service in scheduled mode...")
    subprocess.run([sys.executable, 'email_service.py', '--mode', 'schedule'])

def run_email_event():
    """Run email service in event-driven mode"""
    print("Starting email service in event-driven mode...")
    subprocess.run([sys.executable, 'email_service.py', '--mode', 'event'])

def install_deps():
    """Install Python dependencies"""
    print("Installing dependencies from requirements.txt...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def show_help():
    """Show available commands"""
    print("""
Usage: python run_server.py [command]

Commands:
  start           Start web server in normal mode (default)
  dev             Start web server in development mode with auto-reload
  prod            Start web server in production mode with gunicorn
  email           Start email notification service (polling mode)
  email-schedule  Start email service in scheduled/time-based mode
  email-event     Start email service in event-driven mode
  install         Install dependencies from requirements.txt
  help            Show this help message

Examples:
  python run_server.py                  # Start web server
  python run_server.py dev              # Start web server (dev mode)
  python run_server.py email            # Start email service (polling)
  python run_server.py email-schedule   # Start email service (scheduled)
  python run_server.py install          # Install dependencies

Note: Web server and email service are separate processes.
      Run them in separate terminals for full functionality.
    """)

if __name__ == '__main__':
    # Get command from arguments or default to 'start'
    command = sys.argv[1] if len(sys.argv) > 1 else 'start'

    commands = {
        'start': run_simple,
        'dev': run_dev,
        'prod': run_prod,
        'email': run_email_service,
        'email-schedule': run_email_scheduled,
        'email-event': run_email_event,
        'install': install_deps,
        'help': show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)
