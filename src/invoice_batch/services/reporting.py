from __future__ import annotations

import json
import logging

from invoice_batch.config import AppConfig
from invoice_batch.domain.models import FileProcessResult, RunContext, RunSummary


class RunReporter:
    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def report_start(self, run_context: RunContext) -> None:
        self.logger.info(
            "Inicio de corrida %s | archivos detectados=%s",
            run_context.run_id,
            len(run_context.input_files),
        )

    def report_file_result(self, result: FileProcessResult) -> None:
        payload = {
            "file": result.file_path.name,
            "document_type": result.detected_document_type,
            "status": result.status,
            "warnings": len([msg for msg in result.validation_messages if msg.level == "warning"]),
            "error": result.error_message,
        }
        self.logger.info("Resultado archivo %s", json.dumps(payload, ensure_ascii=False))

    def report_finish(self, summary: RunSummary) -> None:
        self.logger.info(
            "Fin de corrida %s | total=%s success=%s warning=%s error=%s fatal_error=%s",
            summary.run_id,
            summary.total_files,
            summary.success_count,
            summary.warning_count,
            summary.error_count,
            summary.fatal_error,
        )
