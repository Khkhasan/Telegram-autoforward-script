from flask import Flask
from threading import Thread
import logging

# Create a very simple Flask app
app = Flask(__name__)

# Disable Flask's default logging to avoid cluttering the console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Telegram Forwarder is running!"

def run():
    """Run the Flask server on port 8080"""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start the Flask server in a separate thread"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("Keep alive server started on port 8080!")
    print("Use your Replit URL with UptimeRobot to keep your forwarder running 24/7.")
