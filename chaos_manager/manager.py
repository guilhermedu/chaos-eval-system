import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

from .fault_engine import FaultEngine
from .remote_executor import run_scenario_remote


class ChaosManager:
    def __init__(
        self,
        scenarios_path: str = "config/scenarios.yaml",
        nodes_path: str = "config/nodes.yaml",
    ):
        # Cenários (o que é que vamos aplicar)
        self.scenarios_path = Path(scenarios_path)
        with self.scenarios_path.open() as f:
            data = yaml.safe_load(f) or {}
        self.scenarios = data.get("scenarios", {})
        self.engine = FaultEngine()

        # Nodes (onde é que vamos aplicar)
        self.nodes_path = Path(nodes_path)
        if self.nodes_path.exists():
            with self.nodes_path.open() as f:
                ndata = yaml.safe_load(f) or {}
            self.nodes: Dict[str, Dict[str, Any]] = ndata.get("nodes", {})
        else:
            self.nodes = {}

        print(f"[CHAOS] Loaded {len(self.scenarios)} scenarios from {self.scenarios_path}")
        print(f"[CHAOS] Loaded {len(self.nodes)} nodes from {self.nodes_path}")

    def list_scenarios(self) -> None:
        print("[CHAOS] Available scenarios:")
        for name, sc in self.scenarios.items():
            desc = sc.get("description", "")
            print(f"  - {name}: {desc}")

    def list_nodes(self) -> None:
        print("[CHAOS] Known nodes (for SSH orchestration):")
        if not self.nodes:
            print("  (none)")
            return
        for nid, info in self.nodes.items():
            host = info.get("host", "?")
            user = info.get("user", "?")
            print(f"  - {nid}: {user}@{host}")

    def run_scenario_local(self, name: str, duration: Optional[float] = None) -> None:
        """Aplica o cenário localmente (usa FaultEngine / tc / iptables neste host)."""
        if name not in self.scenarios:
            raise SystemExit(f"[CHAOS] Scenario '{name}' not found.")

        scenario = self.scenarios[name]
        rules = scenario.get("rules", [])
        reset_after = scenario.get("reset_after", False)

        print(f"[CHAOS] Running scenario locally: {name}")
        print(f"[CHAOS] Rules: {rules}")

        # aplicar todas as regras localmente
        for rule in rules:
            self.engine.apply_rule(rule)

        if duration is not None and duration > 0:
            print(f"[CHAOS] Holding scenario for {duration} seconds...")
            time.sleep(duration)

        if reset_after:
            print("[CHAOS] Resetting faults after scenario.")
            self.engine.reset_all()
        else:
            print("[CHAOS] Leaving faults active (no reset).")

    def run_scenario_remote(
        self,
        name: str,
        target_node: str,
        duration: Optional[float] = None,
    ) -> None:
        """Orquestra o cenário via SSH num node remoto (N1, N2, N3...)."""
        if name not in self.scenarios:
            raise SystemExit(f"[CHAOS] Scenario '{name}' not found.")

        if target_node == "ALL":
            # aplica o mesmo cenário em todos os nodes definidos no nodes.yaml
            if not self.nodes:
                raise SystemExit("[CHAOS] No nodes defined in nodes.yaml, cannot target ALL.")
            print(f"[CHAOS] Running scenario '{name}' remotely on ALL nodes...")
            for nid, info in self.nodes.items():
                run_scenario_remote(nid, info, name, duration=duration)
            return

        # alvo específico (N1, N2, N3, ...)
        if target_node not in self.nodes:
            raise SystemExit(
                f"[CHAOS] Target node '{target_node}' not found in {self.nodes_path}."
            )

        info = self.nodes[target_node]
        print(f"[CHAOS] Running scenario '{name}' remotely on node '{target_node}'...")
        run_scenario_remote(target_node, info, name, duration=duration)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        required=False,
        help="Nome do cenário a correr",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar cenários disponíveis",
    )
    parser.add_argument(
        "--list-nodes",
        action="store_true",
        help="Listar nodes conhecidos em nodes.yaml",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Quanto tempo manter o cenário antes de reset (s)",
    )
    parser.add_argument(
        "--scenarios-cfg",
        default="config/scenarios.yaml",
        help="Caminho para o ficheiro de cenários YAML",
    )
    parser.add_argument(
        "--nodes-cfg",
        default="config/nodes.yaml",
        help="Caminho para o ficheiro de nodes (para SSH remotos)",
    )
    parser.add_argument(
        "--target-node",
        default=None,
        help=(
            "Se definido, aplica o cenário via SSH nesse node (ex: N1, N2, N3, ALL). "
            "Se não for definido, aplica localmente neste host."
        ),
    )
    args = parser.parse_args()

    cm = ChaosManager(
        scenarios_path=args.scenarios_cfg,
        nodes_path=args.nodes_cfg,
    )

    if args.list or (not args.scenario and not args.list_nodes):
        cm.list_scenarios()
        # não sai ainda, porque o utilizador pode querer também --list-nodes

    if args.list_nodes:
        cm.list_nodes()
        if not args.scenario:
            # se não há cenário pedido, terminamos aqui
            return

    if not args.scenario:
        # sem cenário → já listámos, nada mais a fazer
        return

    # decidir se corre localmente ou remoto
    if args.target_node:
        cm.run_scenario_remote(
            name=args.scenario,
            target_node=args.target_node,
            duration=args.duration,
        )
    else:
        cm.run_scenario_local(
            name=args.scenario,
            duration=args.duration,
        )


if __name__ == "__main__":
    main()
