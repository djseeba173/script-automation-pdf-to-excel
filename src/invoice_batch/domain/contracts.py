from __future__ import annotations

from pathlib import Path
from typing import Protocol

from invoice_batch.domain.models import ExtractedDocument, FileProcessResult, RunContext, RunSummary, ValidationMessage


class DocumentClassifier(Protocol):
    def classify(self, file_path: Path) -> str:
        """Clasifica o infiere el tipo documental esperado para el archivo."""


class InvoiceExtractor(Protocol):
    def extract(self, file_path: Path, document_type: str) -> tuple[ExtractedDocument, dict]:
        """Extrae el documento y devuelve modelo interno + payload crudo."""


class InvoiceValidator(Protocol):
    def validate(self, document: ExtractedDocument) -> list[ValidationMessage]:
        """Valida el documento y devuelve mensajes de validacion."""


class OutputWriter(Protocol):
    def write_document_artifacts(self, run_context: RunContext, result: FileProcessResult) -> None:
        """Escribe salidas por archivo."""

    def finalize_run(self, summary: RunSummary) -> None:
        """Escribe salidas agregadas de la corrida."""


class FileManager(Protocol):
    def ensure_directories(self) -> None:
        """Garantiza la existencia de directorios de trabajo."""

    def discover_pending_files(self) -> list[Path]:
        """Devuelve archivos pendientes de procesar."""

    def move_to_working(self, source_path: Path, run_id: str) -> Path:
        """Mueve un archivo a working antes de procesarlo."""

    def archive_result(self, result: FileProcessResult) -> None:
        """Mueve el archivo a processed o error segun resultado."""


class RunReporter(Protocol):
    def report_start(self, run_context: RunContext) -> None:
        """Registra inicio de corrida."""

    def report_file_result(self, result: FileProcessResult) -> None:
        """Registra resultado por archivo."""

    def report_finish(self, summary: RunSummary) -> None:
        """Registra cierre de corrida."""


class Mailer(Protocol):
    def send_run_summary(self, summary: RunSummary) -> None:
        """Envia resumen de corrida."""
