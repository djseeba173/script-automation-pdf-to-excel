from __future__ import annotations

from pathlib import Path

from invoice_batch.application.batch_runner import BatchRunner
from invoice_batch.application.invoice_processor import InvoiceProcessor
from invoice_batch.config import load_config
from invoice_batch.logging_setup import configure_logging
from invoice_batch.services.azure_document_intelligence import AzureDocumentIntelligenceExtractor
from invoice_batch.services.csv_writer import ExcelOutputWriter
from invoice_batch.services.onedrive_uploader import OneDriveClient
from invoice_batch.services.document_classifier import ConfigurableDocumentClassifier
from invoice_batch.services.file_manager import LocalFileManager
from invoice_batch.services.graph_mailer import GraphMailer
from invoice_batch.services.reporting import RunReporter
from invoice_batch.services.validation import ConfigurableValidator


def build_runner(config_path: Path) -> BatchRunner:
    config = load_config(config_path)
    logger = configure_logging(config)

    classifier = ConfigurableDocumentClassifier(config.processing.allowed_document_types)
    extractor = AzureDocumentIntelligenceExtractor(config.azure)
    validator = ConfigurableValidator(
        config.validation.required_fields_by_document_type,
        config.validation.invoice_rules,
    )
    onedrive_client = OneDriveClient(config) if config.onedrive.enabled else None
    writer = ExcelOutputWriter(config, uploader=onedrive_client)
    file_manager = LocalFileManager(config)
    reporter = RunReporter(config, logger)
    mailer = GraphMailer(config)

    processor = InvoiceProcessor(
        classifier=classifier,
        extractor=extractor,
        validator=validator,
        writer=writer,
        file_manager=file_manager,
        logger=logger,
    )

    return BatchRunner(
        config=config,
        processor=processor,
        file_manager=file_manager,
        reporter=reporter,
        mailer=mailer,
        onedrive_client=onedrive_client,
        logger=logger,
    )
