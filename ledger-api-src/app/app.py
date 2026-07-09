import os
import hashlib
import requests
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# PAN data hardcoded ledu — env/db nundi vayyali
# Task 4 finding: PAN data exposure
LEDGER = [
    {"id": "txn_1001", "pan": "424242******4242", "amount": 4200, "currency": "USD", "status": "captured"},
    {"id": "txn_1002", "pan": "555555******4444", "amount": 1899, "currency": "EUR", "status": "refunded"},
]

@app.route("/health")
def health():
    return jsonify(status="ok")

@app.route("/tokenize", methods=["POST"])
def tokenize():
    payload = request.get_json(silent=True) or {}
    pan = payload.get("pan", "")
    if not pan:
        return jsonify(error="pan required"), 400
    token = "tok_" + hashlib.sha256(pan.encode()).hexdigest()[:24]
    return jsonify(token=token, last4=pan[-4:])

@app.route("/transactions")
def transactions():
    return jsonify(transactions=LEDGER)

@app.route("/import", methods=["POST"])
def import_config():
    # Fix: yaml.safe_load instead of yaml.load (YAML injection fix)
    config = yaml.safe_load(request.data)
    return jsonify(loaded=str(config))

@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    # Fix: SSRF — only allow internal URLs
    allowed_prefixes = ("http://audit-logger", "http://localhost")
    if not url.startswith(allowed_prefixes):
        return jsonify(error="URL not allowed"), 403
    resp = requests.get(url, timeout=5)
    return jsonify(status_code=resp.status_code, body=resp.text[:2048])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)