from flask import Flask, jsonify
import sys
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "MT Fitness API - Minimal Boot Success",
        "python": sys.version,
        "env": "Production" if os.environ.get('VERCEL') else "Development"
    })

@app.route('/api/test')
def test():
    return jsonify({"status": "ok"})
