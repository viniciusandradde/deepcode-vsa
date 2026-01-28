#!/usr/bin/env python
"""
Gerenciador de ambiente do DeepCode VSA.

Fornece uma interface única para:
- Ver status dos containers
- Ver/seguir logs
- Reiniciar serviços
- Rodar limpeza de checkpoints
- Checar saúde da API

Uso rápido:
    python scripts/env_manager.py status
    python scripts/env_manager.py logs --service backend --tail 50
    python scripts/env_manager.py restart --service frontend
    python scripts/env_manager.py cleanup-checkpoints --dry-run
    python scripts/env_manager.py health
"""

import argparse
import subprocess
import sys
from typing import List


PROJECT_ROOT = "/home/projects/agentes-ai/deepcode-vsa"
BACKEND_CONTAINER = "ai_agent_backend"
FRONTEND_CONTAINER = "ai_agent_frontend"
POSTGRES_CONTAINER = "ai_agent_postgres"


def run(cmd: List[str]) -> int:
    """Executa um comando de forma simples, herdando stdin/stdout/stderr."""
    return subprocess.call(cmd)


def cmd_status(_args: argparse.Namespace) -> None:
    """Mostra status dos containers do projeto."""
    print("=== Status dos containers Docker ===")
    run(
        [
            "docker",
            "ps",
            "--format",
            "table {{.Names}}\t{{.Status}}\t{{.Ports}}",
        ]
    )


def cmd_logs(args: argparse.Namespace) -> None:
    """Mostra logs de um serviço."""
    service = args.service
    tail = args.tail
    follow = args.follow

    container = {
        "backend": BACKEND_CONTAINER,
        "frontend": FRONTEND_CONTAINER,
        "postgres": POSTGRES_CONTAINER,
    }.get(service)

    if not container:
        print(f"Serviço desconhecido: {service}")
        sys.exit(1)

    cmd = ["docker", "logs", container, "--tail", str(tail)]
    if follow:
        cmd.append("-f")

    print(f"=== Logs de {container} ===")
    run(cmd)


def cmd_restart(args: argparse.Namespace) -> None:
    """Reinicia um serviço via docker compose."""
    service = args.service

    print(f"=== Reiniciando serviço '{service}' via docker compose ===")
    run(
        [
            "bash",
            "-lc",
            f"cd {PROJECT_ROOT} && docker compose restart {service}",
        ]
    )


def cmd_cleanup_checkpoints(args: argparse.Namespace) -> None:
    """Executa a limpeza de checkpoints antigos dentro do backend."""
    days = args.days
    dry_run = args.dry_run

    print(
        f"=== Limpando checkpoints antigos (>{days} dias, dry-run={dry_run}) no container {BACKEND_CONTAINER} ==="
    )
    cmd = [
        "docker",
        "exec",
        "-e",
        "PYTHONPATH=/app",
        BACKEND_CONTAINER,
        "python",
        "scripts/cleanup_checkpoints.py",
        "--days",
        str(days),
    ]
    if dry_run:
        cmd.append("--dry-run")

    run(cmd)


def cmd_health(_args: argparse.Namespace) -> None:
    """Checa o endpoint /health da API."""
    print("=== Verificando /health da API (http://localhost:8000/health) ===")
    run(["curl", "-s", "http://localhost:8000/health"])
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ferramenta de gestão do ambiente DeepCode VSA."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser(
        "status", help="Mostrar status dos containers Docker do projeto."
    )
    p_status.set_defaults(func=cmd_status)

    # logs
    p_logs = subparsers.add_parser(
        "logs", help="Mostrar logs de um serviço (backend, frontend, postgres)."
    )
    p_logs.add_argument(
        "--service",
        choices=["backend", "frontend", "postgres"],
        default="backend",
        help="Serviço alvo.",
    )
    p_logs.add_argument(
        "--tail",
        type=int,
        default=100,
        help="Número de linhas finais de log a exibir.",
    )
    p_logs.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Seguir logs em tempo real (como tail -f).",
    )
    p_logs.set_defaults(func=cmd_logs)

    # restart
    p_restart = subparsers.add_parser(
        "restart",
        help="Reiniciar um serviço via docker compose (backend, frontend, postgres).",
    )
    p_restart.add_argument(
        "--service",
        choices=["backend", "frontend", "postgres"],
        required=True,
        help="Serviço a ser reiniciado.",
    )
    p_restart.set_defaults(func=cmd_restart)

    # cleanup-checkpoints
    p_cleanup = subparsers.add_parser(
        "cleanup-checkpoints",
        help="Executar limpeza de checkpoints antigos dentro do container backend.",
    )
    p_cleanup.add_argument(
        "--days",
        type=int,
        default=180,
        help="Idade mínima (em dias) para considerar thread inativa. Padrão: 180.",
    )
    p_cleanup.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas simula a limpeza, sem executar DELETE.",
    )
    p_cleanup.set_defaults(func=cmd_cleanup_checkpoints)

    # health
    p_health = subparsers.add_parser(
        "health", help="Checar o endpoint /health da API backend."
    )
    p_health.set_defaults(func=cmd_health)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

