# web_server.py

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running', 200

def run_web_server():
    app.run(host='0.0.0.0', port=8000)