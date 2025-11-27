from flask import Flask, jsonify, render_template
from pathlib import Path
import json
import time

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "metrics.log"

app = Flask(__name__, template_folder="templates")


def load_recent_metrics(window_seconds: float = 10.0):
    """
    Lê o metrics.log e devolve apenas as métricas dos últimos N segundos.
    Isto é suficiente para um dashboard simples.
    """
    now = time.time()
    cutoff = now - window_seconds
    points = []

    if not LOG_FILE.exists():
        return points

    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if msg.get("metric") != "rtt_ms":
                continue
            value = msg.get("value")
            if value is None:
                continue

            ts = msg.get("timestamp") or msg.get("recv_timestamp")
            if ts is None or ts < cutoff:
                continue

            points.append(
                {
                    "nodeId": msg.get("nodeId"),
                    "peerId": msg.get("peerId"),
                    "value": float(value),
                    "timestamp": ts,
                }
            )

    return points


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/latest")
def api_latest():
    data = load_recent_metrics(window_seconds=20.0)
    return jsonify(data)


if __name__ == "__main__":
    # Ex: python3 -m reporting.dashboard
    app.run(host="0.0.0.0", port=8000, debug=True)
