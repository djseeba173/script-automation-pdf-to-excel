from __future__ import annotations

import shutil
from pathlib import Path

from invoice_batch.config import AppConfig
from invoice_batch.domain.models import FileProcessResult


class LocalFileManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def ensure_directories(self) -> None:
        for path in (
            self.config.paths.input_dir,
            self.config.paths.working_dir,
            self.config.paths.processed_dir,
            self.config.paths.error_dir,
            self.config.paths.output_dir,
            self.config.paths.log_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def discover_pending_files(self) -> list[Path]:
        extensions = {ext.lower() for ext in self.config.processing.supported_extensions}
        return sorted(
            path
            for path in self.config.paths.input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        )

    def move_to_working(self, source_path: Path, run_id: str) -> Path:
        target_dir = self.config.paths.working_dir / run_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / source_path.name
        return Path(shutil.move(str(source_path), str(target_path)))

    def archive_result(self, result: FileProcessResult) -> None:
        base_dir = (
            self.config.paths.processed_dir
            if result.status in {"success", "warning"}
            else self.config.paths.error_dir
        )
        base_dir.mkdir(parents=True, exist_ok=True)
        target_path = base_dir / result.file_path.name
        shutil.move(str(result.file_path), str(target_path))
