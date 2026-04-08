from __future__ import annotations

from invoice_batch.domain.models import ExtractedDocument, ValidationMessage


class ConfigurableValidator:
    def __init__(
        self,
        required_fields_by_document_type: dict[str, list[str]],
        invoice_rules: dict[str, object] | None = None,
    ) -> None:
        self.required_fields_by_document_type = required_fields_by_document_type
        self.invoice_rules = invoice_rules or {}

    def validate(self, document: ExtractedDocument) -> list[ValidationMessage]:
        messages: list[ValidationMessage] = []
        required_fields = self.required_fields_by_document_type.get(
            document.document_type,
            [],
        )

        for field_name in required_fields:
            if document.fields.get(field_name) in (None, "", []):
                messages.append(
                    ValidationMessage(
                        level="warning",
                        code="missing_required_field",
                        message=f"Falta campo requerido: {field_name}",
                    )
                )

        if document.document_type == "invoice":
            messages.extend(self._validate_invoice_due_date(document))

        return messages

    def _validate_invoice_due_date(
        self,
        document: ExtractedDocument,
    ) -> list[ValidationMessage]:
        messages: list[ValidationMessage] = []
        invoice_due_date = document.fields.get("invoice_due_date")
        payment_terms = (document.fields.get("payment_terms") or "").strip().lower()

        if invoice_due_date not in (None, ""):
            return messages

        allowed_terms = {
            str(value).strip().lower()
            for value in self.invoice_rules.get(
                "allow_missing_invoice_due_date_when_payment_terms",
                [],
            )
        }
        # Variantes de contado que por definición nunca tienen fecha de vencimiento.
        # Se verifican independientemente de la configuración.
        _contado_base = {"contado", "contado inmediato", "contado sin intereses", "consignacion", "consignación"}
        if payment_terms and (payment_terms in allowed_terms or payment_terms in _contado_base):
            return messages

        policy = self.invoice_rules.get(
            "missing_invoice_due_date_policy_for_other_payment_terms",
            "configurable",
        )
        if policy == "warning":
            messages.append(
                ValidationMessage(
                    level="warning",
                    code="missing_invoice_due_date",
                    message=(
                        "La factura no informa fecha_de_vencimiento_factura. "
                        "No se reemplaza con fecha_de_vencimiento_cae."
                    ),
                )
            )

        return messages
