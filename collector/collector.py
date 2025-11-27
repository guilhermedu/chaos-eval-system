import socket
import json
import time
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "metrics.log"


def _rotate_log_if_exists() -> None:
    if LOG_FILE.exists():
        ts = time.strftime("%Y%m%d-%H%M%S")
        backup = LOG_DIR / f"metrics-{ts}.log"
        print(f"[COLLECTOR] Rotating old log to {backup.name}")
        LOG_FILE.rename(backup)


def run_collector(host: str = "0.0.0.0", port: int = 5000) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    _rotate_log_if_exists()

    print(f"[COLLECTOR] Listening on {host}:{port}")
    print(f"[COLLECTOR] Logging to {LOG_FILE}")

    with LOG_FILE.open("a") as f:
        while True:
            data, addr = sock.recvfrom(4096)
            ts = time.time()
            try:
                msg = json.loads(data.decode())
            except json.JSONDecodeError:
                print(f"[WARN] Invalid JSON from {addr}: {data!r}")
                continue

            msg["recv_timestamp"] = ts

            print(f"[METRIC] from {addr} -> {msg}")
            f.write(json.dumps(msg) + "\n")
            f.flush()


if __name__ == "__main__":
    run_collector()
