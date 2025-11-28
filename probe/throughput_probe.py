# probe/throughput_probe.py
import socket
import time
import argparse
from typing import Optional

from pathlib import Path
import yaml

from .probe_node import send_metric  # reaproveitar função existente


def load_nodes_config(path: str = "config/nodes.yaml") -> dict:
    cfg_path = Path(path)
    with cfg_path.open() as f:
        data = yaml.safe_load(f)
    return data["nodes"]


def measure_udp_throughput(node_id: str,
                           peer_id: str,
                           nodes_cfg_path: str,
                           duration: float = 2.0,
                           payload_size: int = 1200,
                           timeout: float = 0.5) -> float:
    """
    Mede throughput (kbps) entre node_id e peer_id usando o servidor UDP de eco.
    Envia pacotes durante 'duration' segundos e conta os que voltam.
    """

    nodes = load_nodes_config(nodes_cfg_path)
    if node_id not in nodes:
        raise SystemExit(f"NodeId '{node_id}' não existe em {nodes_cfg_path}")
    if peer_id not in nodes:
        raise SystemExit(f"PeerId '{peer_id}' não existe em {nodes_cfg_path}")

    peer_info = nodes[peer_id]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    payload = b"x" * payload_size
    start = time.time()
    bytes_ok = 0

    while True:
        now = time.time()
        if now - start >= duration:
            break

        try:
            sock.sendto(payload, (peer_info["ip"], peer_info["port"]))
            data, _ = sock.recvfrom(4096)
            if data:
                bytes_ok += len(payload)
        except socket.timeout:
            # pacote perdido
            continue

    elapsed = time.time() - start
    if elapsed <= 0 or bytes_ok == 0:
        return 0.0

    throughput_kbps = (bytes_ok * 8) / elapsed / 1000.0
    return throughput_kbps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", required=True,
                        help="ID deste node (ex: N1)")
    parser.add_argument("--peer-id", required=True,
                        help="ID do peer (ex: N2)")
    parser.add_argument("--collector-ip", default="127.0.0.1")
    parser.add_argument("--collector-port", type=int, default=5000)
    parser.add_argument("--nodes-cfg", default="config/nodes.yaml")
    parser.add_argument("--duration", type=float, default=2.0,
                        help="Janela de medição de throughput (s)")
    parser.add_argument("--payload-size", type=int, default=1200,
                        help="Tamanho do payload UDP (bytes)")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Intervalo entre medições consecutivas (s)")
    args = parser.parse_args()

    metrics_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        t_kbps = measure_udp_throughput(
            node_id=args.node_id,
            peer_id=args.peer_id,
            nodes_cfg_path=args.nodes_cfg,
            duration=args.duration,
            payload_size=args.payload_size,
        )

        send_metric(
            metrics_sock,
            args.collector_ip,
            args.collector_port,
            node_id=args.node_id,
            peer_id=args.peer_id,
            metric_name="throughput_kbps",
            value=t_kbps,
        )

        print(f"[THROUGHPUT] {args.node_id}->{args.peer_id} = {t_kbps:.2f} kbps")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
