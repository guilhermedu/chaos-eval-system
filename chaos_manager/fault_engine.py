import os


class FaultEngine:
    """
    Engine simples para injeção de falhas na rede usando `tc netem`.
    Suporta:
      - delay
      - loss
      - jitter
      - rate (throttling)
      - combinações (delay + loss + jitter)
    """

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
            # regra mais geral: combina delay/loss/jitter/rate numa só
            self._apply_netem(rule)
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
        Implementar throttling simples: usamos 'tbf' em vez de netem.
        Isto já é um bocadinho mais avançado, mas fica um exemplo.
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
        Campos opcionais: delay_ms, jitter_ms, loss_pct, rate.
        """
        iface = rule.get("iface", "lo")
        parts = ["tc qdisc replace dev", iface, "root netem"]

        delay_ms = rule.get("delay_ms")
        jitter_ms = rule.get("jitter_ms")
        loss_pct = rule.get("loss_pct")

        if delay_ms is not None:
            if jitter_ms is not None:
                parts.append(f"delay {delay_ms}ms {jitter_ms}ms")
            else:
                parts.append(f"delay {delay_ms}ms")

        if loss_pct is not None:
            parts.append(f"loss {loss_pct}%")

        cmd = " ".join(parts)
        print(f"[FAULT] Applying netem composite on {iface}: {cmd}")
        os.system(cmd)

    # --------- Reset ---------

    def reset_all(self) -> None:
        """
        Remove qdisc de root em interfaces típicas (podes ajustar conforme precisares).
        Neste protótipo só tratamos 'lo', mas podes adicionar 'eth0', 'wlan0', etc.
        """
        for iface in ["lo"]:
            cmd = f"tc qdisc del dev {iface} root 2>/dev/null"
            print(f"[FAULT] Reset on {iface}: {cmd}")
            os.system(cmd)
