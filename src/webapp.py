"""
Lightweight Flask web application that serves a pre-computed news digest
from a static JSON file.
"""
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template

PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
CACHE_FILE = STATIC_DIR / "digest_cache.json"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)

TIMEFRAME_OPTIONS = [
    {"value": "24h", "label": "Past 24 Hours"},
    {"value": "3d", "label": "Past 3 Days"},
    {"value": "7d", "label": "Past Week"},
    {"value": "all", "label": "All Available"},
]


@app.route("/")
def index():
    """Serve the main HTML page."""
    digest = None
    last_updated = None
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as handle:
            digest = json.load(handle)
        last_updated = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)

    return render_template(
        "index.html",
        digest=digest,
        last_updated=last_updated,
        is_generating=False,
        current_timeframe="7d",
        rank_by_relevance=True,
        timeframe_options=TIMEFRAME_OPTIONS,
        now=datetime.now(),
    )


@app.route("/api/digest")
def get_digest():
    """Return the pre-computed digest as JSON."""
    if not CACHE_FILE.exists():
        return jsonify({"error": "Digest cache not found. Run the generator script."}), 404

    with open(CACHE_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    return jsonify(data)


@app.route("/api/status")
def get_status():
    """Return a minimal status payload for the frontend."""
    return jsonify({"is_generating": False, "status": "ready" if CACHE_FILE.exists() else "missing"})


@app.route("/api/refresh", methods=["POST"])
def refresh_digest():
    """No-op refresh endpoint for frontend compatibility."""
    return jsonify({"status": "ok", "message": "Digest is pre-computed."}), 202


if __name__ == "__main__":
    app.run(debug=True)
