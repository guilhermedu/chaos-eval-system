# probe/app_latency_probe.py
import socket
import time
import argparse
from typing import Optional

from .probe_node import send_metric


def measure_app_latency_ms(host: str,
                           port: int,
                           timeout: float = 1.0,
                           payload: bytes = b"PING\n") -> Optional[float]:
    """
    Mede a latência de aplicação (ms) abrindo uma ligação TCP, enviando
    'PING\\n' e esperando 'PONG\\n'.
    """
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(payload)
            data = s.recv(1024)
            if not data:
                return None
    except (socket.timeout, OSError):
        return None
    end = time.time()
    return (end - start) * 1000.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", required=True,
                        help="ID deste node (ex: N1)")
    parser.add_argument("--peer-id", required=True,
                        help="ID lógico do serviço (ex: APP1)")
    parser.add_argument("--service-host", default="127.0.0.1",
                        help="IP/hostname do serviço de aplicação")
    parser.add_argument("--service-port", type=int, default=9000,
                        help="Porta TCP do serviço de aplicação")
    parser.add_argument("--collector-ip", default="127.0.0.1")
    parser.add_argument("--collector-port", type=int, default=5000)
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Intervalo entre medições (s)")
    args = parser.parse_args()

    metrics_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        latency_ms = measure_app_latency_ms(
            host=args.service_host,
            port=args.service_port,
        )

        send_metric(
            metrics_sock,
            args.collector_ip,
            args.collector_port,
            node_id=args.node_id,
            peer_id=args.peer_id,
            metric_name="app_latency_ms",
            value=latency_ms,
        )

        print(f"[APP-LATENCY] {args.node_id}->{args.peer_id} "
              f"= {latency_ms if latency_ms is not None else 'TIMEOUT'} ms")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
