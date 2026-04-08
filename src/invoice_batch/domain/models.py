from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DocumentLine:
    line_number: int
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractedDocument:
    source_file: str
    document_type: str
    fields: dict[str, Any] = field(default_factory=dict)
    lines: list[DocumentLine] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationMessage:
    level: str
    code: str
    message: str


@dataclass(slots=True)
class FileProcessResult:
    file_path: Path
    status: str
    detected_document_type: str | None = None
    document: ExtractedDocument | None = None
    validation_messages: list[ValidationMessage] = field(default_factory=list)
    error_message: str | None = None
    raw_payload: dict[str, Any] | None = None


@dataclass(slots=True)
class RunContext:
    run_id: str
    started_at: datetime
    input_files: list[Path]


@dataclass(slots=True)
class RunSummary:
    run_id: str
    started_at: datetime
    finished_at: datetime
    total_files: int
    success_count: int
    warning_count: int
    error_count: int
    skipped_count: int
    results: list[FileProcessResult] = field(default_factory=list)
    fatal_error: str | None = None
    subtype_counts: dict[str, int] = field(default_factory=dict)
