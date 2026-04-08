"""
Test rápido del GraphMailer — no llama a Azure ni procesa PDFs.
Uso: python test_mail.py --config config/settings.json
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from invoice_batch.config import load_config
from invoice_batch.domain.models import RunSummary
from invoice_batch.services.graph_mailer import GraphMailer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/settings.json")
    args = parser.parse_args()

    config = load_config(Path(args.config))

    summary = RunSummary(
        run_id="TEST_20260408",
        started_at=datetime.now(),
        finished_at=datetime.now(),
        total_files=3,
        success_count=2,
        warning_count=1,
        error_count=0,
        skipped_count=0,
        subtype_counts={
            "Factura": 2,
            "Nota de Crédito": 1,
        },
    )

    mailer = GraphMailer(config)
    mailer.send_run_summary(summary)
    print("Listo — revisá el log para ver si se envió o el error detallado.")


if __name__ == "__main__":
    main()
