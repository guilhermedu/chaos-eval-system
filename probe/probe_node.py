import socket
import json
import time
import argparse
import threading
from pathlib import Path
from typing import Optional

import yaml  # pip install pyyaml


def load_nodes_config(path: str = "config/nodes.yaml") -> dict:
    cfg_path = Path(path)
    with cfg_path.open() as f:
        data = yaml.safe_load(f)
    return data["nodes"]


def echo_server(bind_ip: str, bind_port: int) -> None:
    """
    Pequeno servidor UDP que apenas ecoa de volta o que recebe.
    Serve para outros nodes medirem RTT.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, bind_port))
    print(f"[ECHO] Listening on {bind_ip}:{bind_port}")

    while True:
        data, addr = sock.recvfrom(2048)
        # devolve exatamente o que recebeu
        sock.sendto(data, addr)


def measure_rtt_to_peer(sock: socket.socket,
                        peer_id: str,
                        peer_info: dict,
                        timeout: float = 1.0) -> Optional[float]:
    """
    Envia um PING UDP para o peer e mede o RTT (ms).
    Se não houver resposta no timeout, devolve None (perda).
    """
    msg = {
        "type": "PING",
        "to": peer_id,
        "ts": time.time(),
    }
    payload = json.dumps(msg).encode()

    start = time.time()
    sock.settimeout(timeout)
    try:
        sock.sendto(payload, (peer_info["ip"], peer_info["port"]))
        _data, _addr = sock.recvfrom(2048)
    except socket.timeout:
        return None
    end = time.time()

    rtt_ms = (end - start) * 1000.0
    return rtt_ms


def send_metric(metrics_sock: socket.socket,
                collector_ip: str,
                collector_port: int,
                node_id: str,
                peer_id: str,
                metric_name: str,
                value: Optional[float]) -> None:
    msg = {
        "nodeId": node_id,
        "peerId": peer_id,
        "metric": metric_name,
        "value": value,
        "timestamp": time.time(),
    }
    metrics_sock.sendto(json.dumps(msg).encode(),
                        (collector_ip, collector_port))
    print(f"[PROBE {node_id}] Sent metric: {msg}")


def run_probe(node_id: str,
              collector_ip: str = "127.0.0.1",
              collector_port: int = 5000,
              nodes_cfg_path: str = "config/nodes.yaml",
              interval: float = 1.0) -> None:
    # Carregar configuração dos nodes
    nodes = load_nodes_config(nodes_cfg_path)
    if node_id not in nodes:
        raise SystemExit(f"NodeId '{node_id}' não existe em {nodes_cfg_path}")

    my_info = nodes[node_id]

    # Lançar echo server numa thread separada
    echo_thread = threading.Thread(
        target=echo_server,
        args=(my_info["ip"], my_info["port"]),
        daemon=True,
    )
    echo_thread.start()

    # Socket para medir RTT para os peers
    ping_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Socket separado para enviar métricas ao collector
    metrics_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Lista de peers (todos menos eu)
    peers = {nid: info for nid, info in nodes.items() if nid != node_id}

    print(f"[PROBE {node_id}] Peers: {list(peers.keys())}")
    print(f"[PROBE {node_id}] Collector: {collector_ip}:{collector_port}")

    while True:
        # para cada peer, medir RTT e enviar métrica
        for peer_id, peer_info in peers.items():
            rtt = measure_rtt_to_peer(ping_sock, peer_id, peer_info)
            # rtt=None significa perda/timeout
            send_metric(
                metrics_sock,
                collector_ip,
                collector_port,
                node_id,
                peer_id,
                "rtt_ms",
                rtt,
            )
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", required=True, help="ID deste node (ex: N1)")
    parser.add_argument("--collector-ip", default="127.0.0.1")
    parser.add_argument("--collector-port", type=int, default=5000)
    parser.add_argument("--nodes-cfg", default="config/nodes.yaml")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Intervalo entre rondas de medição (s)")
    args = parser.parse_args()

    run_probe(
        node_id=args.node_id,
        collector_ip=args.collector_ip,
        collector_port=args.collector_port,
        nodes_cfg_path=args.nodes_cfg,
        interval=args.interval,
    )
