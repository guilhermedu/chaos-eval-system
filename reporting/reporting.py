import json
from pathlib import Path
from statistics import mean, pstdev

LOG_FILE = Path("logs/metrics.log")


def load_metrics():
    metrics = []
    if not LOG_FILE.exists():
        print(f"[REPORT] Log file {LOG_FILE} not found.")
        return metrics

    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            metrics.append(obj)
    return metrics


def build_stats(metrics):
    """
    Agrupa por metricName e (nodeId, peerId) e calcula:
      - total samples
      - nº com valor válido
      - nº perdidos (value == None)
      - perda %
      - min / max / média / stddev do value
    Devolve:
      stats[metric_name][(nodeId, peerId)] = {...}
    """
    groups = {}

    for m in metrics:
        metric_name = m.get("metric")
        if not metric_name:
            continue

        node = m.get("nodeId")
        peer = m.get("peerId")
        key = (node, peer)

        if metric_name not in groups:
            groups[metric_name] = {}

        if key not in groups[metric_name]:
            groups[metric_name][key] = {
                "values": [],
                "lost": 0,
                "total": 0,
            }

        g = groups[metric_name][key]
        g["total"] += 1

        v = m.get("value")
        if v is None:
            g["lost"] += 1
        else:
            g["values"].append(float(v))

    # calcular estatísticas
    stats = {}
    for metric_name, by_link in groups.items():
        stats[metric_name] = {}
        for (node, peer), g in by_link.items():
            vals = g["values"]
            total = g["total"]
            lost = g["lost"]
            ok = len(vals)

            if ok > 0:
                min_v = min(vals)
                max_v = max(vals)
                avg_v = mean(vals)
                std_v = pstdev(vals) if ok > 1 else 0.0
            else:
                min_v = max_v = avg_v = std_v = None

            loss_pct = (lost / total * 100.0) if total > 0 else 0.0

            stats[metric_name][(node, peer)] = {
                "total": total,
                "ok": ok,
                "lost": lost,
                "loss_pct": loss_pct,
                "min": min_v,
                "max": max_v,
                "avg": avg_v,
                "std": std_v,
            }

    return stats


def _print_one_metric(metric_name, stats_for_metric):
    print(f"\n=== Stats para métrica: {metric_name} (nodeId -> peerId) ===")
    print("From   To   Total  OK   Lost  Loss%   Min     Max     Avg     Std")
    print("-" * 78)

    for (node, peer), s in sorted(stats_for_metric.items()):
        def fmt(x):
            return f"{x:7.2f}" if isinstance(x, (float, int)) else "   n/a "

        line = (
            f"{node:5} {peer:5} "
            f"{s['total']:6d} {s['ok']:4d} {s['lost']:5d} "
            f"{fmt(s['loss_pct'])} "
            f"{fmt(s['min'])} {fmt(s['max'])} {fmt(s['avg'])} {fmt(s['std'])}"
        )
        print(line)


if __name__ == "__main__":
    metrics = load_metrics()
    stats = build_stats(metrics)

    if not stats:
        print("[REPORT] Sem métricas para apresentar.")
    else:
        # Imprime cada métrica separadamente (ex: rtt_ms, throughput_kbps, app_latency_ms)
        for metric_name in sorted(stats.keys()):
            _print_one_metric(metric_name, stats[metric_name])
