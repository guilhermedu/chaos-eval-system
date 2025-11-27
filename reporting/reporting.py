import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple, List


LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = LOG_DIR / "metrics.log"
SUMMARY_LOG_FILE = LOG_DIR / "rtt_summary.log"


def load_metrics(log_path: Path = DEFAULT_LOG_FILE):
    """
    Lê o ficheiro de métricas (JSON por linha) e devolve uma lista de registos.
    Só considera métricas rtt_ms com value != None.
    """
    records = []
    if not log_path.exists():
        print(f"[REPORT] Log file {log_path} not found.")
        return records

    with log_path.open() as f:
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

            node_id = msg.get("nodeId")
            peer_id = msg.get("peerId")
            if not node_id or not peer_id:
                continue

            records.append(
                (node_id, peer_id, float(value), msg.get("timestamp"))
            )
    return records


def aggregate_stats(records):
    """
    Calcula min/max/média por (nodeId, peerId).
    """
    groups: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    for node_id, peer_id, value, _ts in records:
        groups[(node_id, peer_id)].append(value)

    stats = {}
    for (node_id, peer_id), vals in groups.items():
        cnt = len(vals)
        vmin = min(vals)
        vmax = max(vals)
        avg = sum(vals) / cnt if cnt > 0 else 0.0
        stats[(node_id, peer_id)] = {
            "from": node_id,
            "to": peer_id,
            "count": cnt,
            "min_ms": vmin,
            "max_ms": vmax,
            "avg_ms": avg,
        }
    return stats


def format_table(stats) -> str:
    """
    Devolve a tabela como string (para imprimir e gravar em ficheiro).
    """
    lines = []
    lines.append("=== RTT Stats por (nodeId -> peerId) ===")
    header = f"{'From':<6} {'To':<6} {'Count':>6} {'Min(ms)':>10} {'Max(ms)':>10} {'Avg(ms)':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    for key, st in sorted(stats.items(), key=lambda x: (x[0][0], x[0][1])):
        line = (
            f"{st['from']:<6} {st['to']:<6} "
            f"{st['count']:>6} {st['min_ms']:>10.2f} {st['max_ms']:>10.2f} {st['avg_ms']:>10.2f}"
        )
        lines.append(line)

    return "\n".join(lines)


def save_table_log(table_str: str, out_path: Path = SUMMARY_LOG_FILE):
    """
    Guarda a tabela num ficheiro .log (substitui conteúdo anterior).
    """
    out_path.parent.mkdir(exist_ok=True)
    with out_path.open("w") as f:
        f.write(table_str + "\n")
    print(f"[REPORT] Saved summary to {out_path}")


def main():
    records = load_metrics()
    if not records:
        print("[REPORT] No metrics loaded.")
        return
    stats = aggregate_stats(records)
    table_str = format_table(stats)

    # mostra no terminal
    print()
    print(table_str)

    # guarda em ficheiro .log
    save_table_log(table_str, SUMMARY_LOG_FILE)


if __name__ == "__main__":
    main()
