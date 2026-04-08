from __future__ import annotations

from pathlib import Path


class ConfigurableDocumentClassifier:
    def __init__(self, allowed_document_types: list[str]) -> None:
        self.allowed_document_types = allowed_document_types

    def classify(self, file_path: Path) -> str:
        # Placeholder deliberado:
        # hoy no existe regla estable de deteccion/clasificacion.
        # Se retorna un tipo default configurable para mantener desacople.
        if "invoice" in self.allowed_document_types:
            return "invoice"
        return self.allowed_document_types[0]
