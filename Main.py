from flask import Flask, request, Response, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

CATALOG_BASE = "https://catalog.roblox.com"
TIMEOUT = 5.0
RETRIES = 3

session = requests.Session()
retry = Retry(
    total=RETRIES,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET"])
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

@app.after_request
def add_cors(resp):
    for k, v in cors_headers().items():
        resp.headers[k] = v
    return resp

@app.route("/v1/<path:path>", methods=["GET"])
def proxy(path):
    qs = request.que
