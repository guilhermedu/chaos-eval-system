import os


class FaultEngine:
    """
    Engine simples para injeção de falhas na rede usando `tc` e, opcionalmente, `iptables`.
    Suporta:
      - delay           (tc netem delay)
      - loss            (tc netem loss)
      - jitter          (tc netem delay + jitter)
      - rate            (tc tbf – throttling)
      - netem (composite: delay + jitter + loss)
      - partition       (isolar node/serviço via DROP UDP numa porta específica)
    """

    def __init__(self):
        # Para sabermos em que portas aplicámos partition e conseguir limpar depois
        self.partition_ports = set()

    def apply_rule(self, rule: dict) -> None:
        rtype = rule.get("type")
        if rtype == "delay":
            self._apply_delay(rule)
        elif rtype == "loss":
            self._apply_loss(rule)
        elif rtype == "jitter":
            self._apply_jitter(rule)
        elif rtype == "rate":
            self._apply_rate(rule)
        elif rtype == "netem":
            # regra mais geral: combina delay/loss/jitter numa só
            self._apply_netem(rule)
        elif rtype == "partition":
            # simula network partition (DROP tráfego numa porta)
            self._apply_partition(rule)
        else:
            print(f"[FAULT] Tipo de regra desconhecido: {rtype} / regra={rule}")

    # --------- Handlers específicos ---------

    def _apply_delay(self, rule: dict) -> None:
        iface = rule.get("iface", "lo")
        delay_ms = rule.get("delay_ms", 100)

        cmd = f"tc qdisc replace dev {iface} root netem delay {delay_ms}ms"
        print(f"[FAULT] Applying delay: {delay_ms}ms on {iface}")
        print(f"[FAULT] Executing: {cmd}")
        os.system(cmd)

    def _apply_loss(self, rule: dict) -> None:
        iface = rule.get("iface", "lo")
        loss_pct = rule.get("loss_pct", 10)  # %
        cmd = f"tc qdisc replace dev {iface} root netem loss {loss_pct}%"
        print(f"[FAULT] Applying loss: {loss_pct}% on {iface}")
        print(f"[FAULT] Executing: {cmd}")
        os.system(cmd)

    def _apply_jitter(self, rule: dict) -> None:
        iface = rule.get("iface", "lo")
        delay_ms = rule.get("delay_ms", 50)
        jitter_ms = rule.get("jitter_ms", 20)
        cmd = (
            f"tc qdisc replace dev {iface} root netem "
            f"delay {delay_ms}ms {jitter_ms}ms"
        )
        print(f"[FAULT] Applying jitter: base={delay_ms}ms jitter={jitter_ms}ms on {iface}")
        print(f"[FAULT] Executing: {cmd}")
        os.system(cmd)

    def _apply_rate(self, rule: dict) -> None:
        """
        Throttling simples: usamos 'tbf' em vez de netem.
        Compatível com cenários T5 (rate_lo_5mbit, rate_lo_1mbit, etc.).
        """
        iface = rule.get("iface", "lo")
        rate = rule.get("rate", "1mbit")      # ex: "1mbit"
        burst = rule.get("burst", "32kbit")   # ex: "32kbit"
        latency_ms = rule.get("latency_ms", 400)

        # primeiro limpamos qualquer netem/tbf anterior
        os.system(f"tc qdisc del dev {iface} root 2>/dev/null")

        cmd = (
            f"tc qdisc add dev {iface} root tbf "
            f"rate {rate} burst {burst} latency {latency_ms}ms"
        )
        print(f"[FAULT] Applying rate limit: {rate}, burst={burst}, latency={latency_ms}ms on {iface}")
        print(f"[FAULT] Executing: {cmd}")
        os.system(cmd)

    def _apply_netem(self, rule: dict) -> None:
        """
        Regra 'genérica' que combina delay, loss e jitter numa só linha netem.
        Compatível com T4 (composite_*) e perfis mobile.
        Campos opcionais: delay_ms, jitter_ms, loss_pct.
        """
        iface = rule.get("iface", "lo")
        parts = ["tc", "qdisc", "replace", "dev", iface, "root", "netem"]

        delay_ms = rule.get("delay_ms")
        jitter_ms = rule.get("jitter_ms")
        loss_pct = rule.get("loss_pct")

        if delay_ms is not None:
            if jitter_ms is not None:
                parts.extend(["delay", f"{delay_ms}ms", f"{jitter_ms}ms"])
            else:
                parts.extend(["delay", f"{delay_ms}ms"])

        if loss_pct is not None:
            parts.extend(["loss", f"{loss_pct}%"])

        cmd = " ".join(parts)
        print(f"[FAULT] Applying netem composite on {iface}: {cmd}")
        os.system(cmd)

    def _apply_partition(self, rule: dict) -> None:
        """
        Simula network partition para um node/serviço, fazendo DROP ao tráfego UDP
        numa determinada porta (usado em T6: partition_probe_N2, partition_service_9000, etc.).
        """
        port = rule.get("port")
        if port is None:
            print("[FAULT] partition rule sem 'port' definido")
            return

        self.partition_ports.add(port)

        # Aqui assumimos UDP (probes e muitos serviços simples). Se precisares de TCP também,
        # podemos duplicar regras com -p tcp.
        cmd_in = f"iptables -A INPUT -p udp --dport {port} -j DROP"
        cmd_out = f"iptables -A OUTPUT -p udp --dport {port} -j DROP"

        print(f"[FAULT] Applying partition: DROP UDP porta {port} (INPUT/OUTPUT)")
        print(f"[FAULT] Executing: {cmd_in}")
        os.system(cmd_in)
        print(f"[FAULT] Executing: {cmd_out}")
        os.system(cmd_out)

    # --------- Reset ---------

    def reset_all(self) -> None:
        """
        Remove qdisc de root e reverte regras de partition (iptables).
        Neste protótipo, tratamos 'lo' e as portas usadas em cenários de partition.
        """
        # Limpar qdisc na lo (podes acrescentar eth0/wlan0 se fizer sentido)
        for iface in ["lo"]:
            cmd = f"tc qdisc del dev {iface} root 2>/dev/null"
            print(f"[FAULT] Reset qdisc on {iface}: {cmd}")
            os.system(cmd)

        # Limpar regras iptables criadas para partition
        for port in list(self.partition_ports):
            cmd_in = f"iptables -D INPUT -p udp --dport {port} -j DROP"
            cmd_out = f"iptables -D OUTPUT -p udp --dport {port} -j DROP"
            print(f"[FAULT] Reset partition INPUT porta {port}: {cmd_in}")
            os.system(cmd_in)
            print(f"[FAULT] Reset partition OUTPUT porta {port}: {cmd_out}")
            os.system(cmd_out)

        self.partition_ports.clear()
