from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Simple HTML template for the status page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Auto Forwarder</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f5f5f5;
        }
        .container {
            text-align: center;
            padding: 30px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .status {
            color: #28a745;
            font-weight: bold;
        }
        .subtitle {
            color: #6c757d;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Telegram Auto Forwarder</h1>
        <p>Status: <span class="status">Running</span></p>
        <p class="subtitle">Replit Status Page - UptimeRobot Monitor</p>
        <p>This page confirms the forwarder service is active.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Return a nice status page
    return render_template_string(HTML)

@app.route('/status')
def status():
    # Return a simple "OK" for status checks
    return "OK"

if __name__ == '__main__':
    # This runs when the script is executed directly
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
