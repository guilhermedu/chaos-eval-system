from flask import Flask, jsonify, render_template, request
from pathlib import Path
import json
import time

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "metrics.log"

app = Flask(__name__, template_folder="templates")


def load_recent_metrics(metric_name: str = "rtt_ms",
                        window_seconds: float = 10.0):
    """
    Lê o metrics.log e devolve apenas as métricas do tipo 'metric_name'
    dos últimos N segundos.
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

            if msg.get("metric") != metric_name:
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
    # métrica pedida pelo frontend (default: rtt_ms)
    metric_name = request.args.get("metric", "rtt_ms")
    data = load_recent_metrics(metric_name=metric_name, window_seconds=20.0)
    return jsonify(data)


if __name__ == "__main__":
    # Ex: python3 -m reporting.dashboard
    app.run(host="0.0.0.0", port=8000, debug=True)
