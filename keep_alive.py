from threading import Thread
import logging
import os
from main import app

# Disable Flask's default logging to avoid cluttering the console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def run():
    """Run the Flask server on port 8080"""
    # Use port 8080 for the keep-alive server
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start the Flask server in a separate thread"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("Keep alive server started at http://localhost:8080!")
    print("Use this URL with UptimeRobot to keep your forwarder running 24/7.")
