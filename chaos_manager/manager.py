import time
import argparse
from pathlib import Path
from typing import Optional

import yaml

from .fault_engine import FaultEngine


class ChaosManager:
    def __init__(self, scenarios_path: str = "config/scenarios.yaml"):
        self.scenarios_path = Path(scenarios_path)
        with self.scenarios_path.open() as f:
            data = yaml.safe_load(f)
        self.scenarios = data.get("scenarios", {})
        self.engine = FaultEngine()

    def list_scenarios(self) -> None:
        print("[CHAOS] Available scenarios:")
        for name, sc in self.scenarios.items():
            desc = sc.get("description", "")
            print(f"  - {name}: {desc}")

    def run_scenario(self, name: str, duration: Optional[float] = None) -> None:
        if name not in self.scenarios:
            raise SystemExit(f"[CHAOS] Scenario '{name}' not found.")

        scenario = self.scenarios[name]
        rules = scenario.get("rules", [])
        reset_after = scenario.get("reset_after", False)

        print(f"[CHAOS] Running scenario: {name}")
        print(f"[CHAOS] Rules: {rules}")

        # aplicar todas as regras
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=False,
                        help="Nome do cenário a correr")
    parser.add_argument("--list", action="store_true",
                        help="Listar cenários disponíveis")
    parser.add_argument("--duration", type=float, default=None,
                        help="Quanto tempo manter o cenário antes de reset (s)")
    parser.add_argument("--scenarios-cfg", default="config/scenarios.yaml")
    args = parser.parse_args()

    cm = ChaosManager(scenarios_path=args.scenarios_cfg)

    if args.list or not args.scenario:
        cm.list_scenarios()
        if not args.scenario:
            return

    cm.run_scenario(args.scenario, duration=args.duration)


if __name__ == "__main__":
    main()
