from __future__ import annotations

import argparse
from pathlib import Path

from invoice_batch.bootstrap import build_runner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesa facturas por lote usando Azure Document Intelligence."
    )
    parser.add_argument(
        "--config",
        default="config/settings.example.json",
        help="Ruta al archivo JSON de configuracion.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = build_runner(Path(args.config))
    summary = runner.run()
    return 0 if summary.fatal_error is None else 1
