import subprocess
from typing import Dict, Any, Optional


def run_scenario_remote(
    node_id: str,
    node_info: Dict[str, Any],
    scenario: str,
    duration: Optional[float] = None,
) -> None:
    """
    Executa o cenário num node remoto via SSH.

    Espera que node_info tenha:
      - host: IP ou hostname do node
      - user: utilizador para SSH (opcional, pode ser string vazia)
      - project_path: diretório onde está o chaos-eval-system (opcional)

    No remoto, corre:
      cd project_path && sudo python3 -m chaos_manager.manager --scenario ... [--duration ...]
    """
    host = node_info.get("host")
    user = node_info.get("user", "")
    project_path = node_info.get("project_path", "")

    if not host:
        print(f"[CHAOS][SSH] Node '{node_id}' não tem 'host' definido em nodes.yaml.")
        return

    # comando base que queremos executar no node remoto
    cmd = f"python3 -m chaos_manager.manager --scenario {scenario}"
    if duration is not None and duration > 0:
        cmd += f" --duration {duration}"

    # garantir que estamos no diretório correto no remoto
    if project_path:
        remote_cmd = f"cd {project_path} && sudo {cmd}"
    else:
        remote_cmd = f"sudo {cmd}"

    # alvo ssh: user@host ou só host
    ssh_target = f"{user}@{host}" if user else host

    ssh_cmd = ["ssh", ssh_target, remote_cmd]

    print(f"[CHAOS][SSH] Executing on {ssh_target}: {remote_cmd}")
    result = subprocess.run(ssh_cmd)
    if result.returncode != 0:
        print(
            f"[CHAOS][SSH] Remote scenario '{scenario}' on node '{node_id}' "
            f"failed with code {result.returncode}"
        )
    else:
        print(f"[CHAOS][SSH] Scenario '{scenario}' completed on node '{node_id}'.")
