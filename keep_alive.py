import time
import subprocess
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def forwarder_loop():
    """
    This will run start_forwarding.py in a loop.
    If it ever exits/crashes, it waits 5s and restarts.
    """
    while True:
        try:
            # run your headless launcher
            subprocess.run(["python3", "start_forwarding.py"], check=True)
        except Exception as e:
            print(f"[forwarder crashed] {e}")
            time.sleep(5)

if __name__ == "__main__":
    # 1) start the forwarder subprocess in the background
    Thread(target=forwarder_loop, daemon=True).start()
    # 2) run Flask so Replit (or any host) can ping "/"
    app.run(host="0.0.0.0", port=3000)
