"""
GoPro API Server — Proxy leggero verso GoPro Hero 4
Usa bottle (single file) per esporre API REST.

Avvio: python gopro_api.py
Porta: 8081
"""

from bottle import route, run, request, response, error
import urllib.request
import urllib.error
import json
import os

GOPRO_IP = os.environ.get("GOPRO_IP", "10.5.5.9")
GOPRO_BASE = f"http://{GOPRO_IP}/gp/gpControl"


def gopro_request(path, timeout=3):
    """Chiama la GoPro e restituisce la risposta."""
    url = f"{GOPRO_BASE}{path}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return {"ok": True, "data": json.loads(data) if data else {}}
    except urllib.error.URLError as e:
        return {"ok": False, "error": str(e.reason)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@route("/api/status")
def api_status():
    """Restituisce lo status completo della GoPro."""
    response.content_type = "application/json"
    result = gopro_request("/status")
    if result["ok"]:
        return result["data"]
    else:
        response.status = 502
        return {"error": result["error"]}


@route("/api/cmd", method="POST")
def api_cmd():
    """Esegue un comando sulla GoPro.
    
    Body JSON: { "path": "/command/shutter?p=1" }
    """
    response.content_type = "application/json"
    try:
        body = request.json
    except Exception:
        response.status = 400
        return {"error": "Invalid JSON body"}

    if not body or "path" not in body:
        response.status = 400
        return {"error": "Missing 'path' field"}

    path = body["path"]
    if not path.startswith("/"):
        path = "/" + path

    # Sicurezza: accetta solo percorsi GoPro
    allowed_prefixes = ["/command/", "/setting/"]
    if not any(path.startswith(p) for p in allowed_prefixes):
        response.status = 403
        return {"error": "Path not allowed"}

    result = gopro_request(path)
    if result["ok"]:
        return result["data"]
    else:
        response.status = 502
        return {"error": result["error"]}


@error(404)
def not_found(error):
    response.content_type = "application/json"
    return {"error": "Not found"}


@error(500)
def server_error(error):
    response.content_type = "application/json"
    return {"error": "Internal server error"}


if __name__ == "__main__":
    print(f"GoPro API Server — {GOPRO_BASE}")
    print("Listening on 0.0.0.0:8081")
    run(host="0.0.0.0", port=8081, quiet=False)
