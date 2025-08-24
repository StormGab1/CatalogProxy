from flask import Flask, request, Response, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

app = Flask(__name__)

CATALOG_BASE = "https://catalog.roblox.com"
TIMEOUT = 5.0
RETRIES = 3
CACHE_TTL = 60  # segundos

# Session com retries
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

# Cache simples: {url: (timestamp, response_content)}
cache = {}

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
    qs = request.query_string.decode()
    url = f"{CATALOG_BASE}/v1/{path}"
    if qs:
        url += f"?{qs}"

    # Verifica cache
    now = time.time()
    if url in cache:
        ts, content = cache[url]
        if now - ts <= CACHE_TTL:
            return Response(content, status=200, content_type="application/json")

    headers = {
        "Accept": "application/json",
        "User-Agent": "Roblox-Catalog-Proxy/Flask"
    }

    try:
        upstream = session.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        return jsonify({"ok": False, "error": str(e)}), 502

    cache[url] = (now, upstream.content)

    return Response(upstream.content, status=upstream.status_code, content_type="application/json")

@app.route("/health")
def health():
    return jsonify(ok=True)
