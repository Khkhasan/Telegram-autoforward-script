import time
from threading import Thread
from flask import Flask
from start_forwarding import start_forwarding

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def forwarder_loop():
    while True:
        try:
            start_forwarding()
        except Exception as e:
            print(f"[error] {e}")
            time.sleep(5)

if __name__ == "__main__":
    # 1) start your forwarder in a background thread
    Thread(target=forwarder_loop, daemon=True).start()
    # 2) run Flask so Replit (or any host) can ping "/"
    app.run(host="0.0.0.0", port=3000)
