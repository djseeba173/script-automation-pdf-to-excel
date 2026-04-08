from __future__ import annotations

import logging
from pathlib import Path

from invoice_batch.domain.contracts import DocumentClassifier, FileManager, InvoiceExtractor, InvoiceValidator, OutputWriter
from invoice_batch.domain.models import FileProcessResult, RunContext


class InvoiceProcessor:
    def __init__(
        self,
        classifier: DocumentClassifier,
        extractor: InvoiceExtractor,
        validator: InvoiceValidator,
        writer: OutputWriter,
        file_manager: FileManager,
        logger: logging.Logger,
    ) -> None:
        self.classifier = classifier
        self.extractor = extractor
        self.validator = validator
        self.writer = writer
        self.file_manager = file_manager
        self.logger = logger

    def process_file(self, run_context: RunContext, source_path: Path) -> FileProcessResult:
        working_path = self.file_manager.move_to_working(source_path, run_context.run_id)
        self.logger.info("Procesando archivo %s", working_path.name)

        try:
            document_type = self.classifier.classify(working_path)
            document, raw_payload = self.extractor.extract(working_path, document_type)
            validation_messages = self.validator.validate(document)
            status = "warning" if any(msg.level == "warning" for msg in validation_messages) else "success"

            result = FileProcessResult(
                file_path=working_path,
                status=status,
                detected_document_type=document_type,
                document=document,
                validation_messages=validation_messages,
                raw_payload=raw_payload,
            )
        except Exception as exc:
            result = FileProcessResult(
                file_path=working_path,
                status="error",
                detected_document_type=locals().get("document_type"),
                error_message=str(exc),
            )

        self.writer.write_document_artifacts(run_context, result)
        self.file_manager.archive_result(result)
        return result
