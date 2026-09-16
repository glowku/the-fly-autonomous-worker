"""Service Render : garde l'état, ping les workflows GitHub."""
import os, requests
from flask import Flask, jsonify, request
from bot.state import load as load_state

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("TARGET_REPO", "glowku/the-fly-autonomous-worker")

@app.route("/")
def index():
    return jsonify({
        "service": "the-fly-autonomous-worker",
        "status": "buzzing",
        "repo": REPO,
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "ts": __import__("time").time()}), 200

@app.route("/state")
def state():
    return jsonify(load_state())

@app.route("/trigger", methods=["POST"])
def trigger():
    """Déclenche un workflow GitHub."""
    wf = request.json.get("workflow", "fly-commit.yml")
    payload = request.json.get("payload", {})
    r = requests.post(
        f"https://api.github.com/repos/{REPO}/actions/workflows/{wf}/dispatches",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json={"ref": "main", "inputs": payload},
        timeout=15,
    )
    return jsonify({"status": r.status_code, "workflow": wf}), r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))