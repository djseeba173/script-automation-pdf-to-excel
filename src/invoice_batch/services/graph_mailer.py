from __future__ import annotations

import logging
import time

from invoice_batch.config import AppConfig
from invoice_batch.domain.models import RunSummary

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"


class GraphMailer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("invoice_batch.graph_mailer")
        self._token: str | None = None
        self._token_expiry: float = 0.0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token
        resp = requests.post(
            _TOKEN_URL.format(tenant_id=self.config.graph.tenant_id),
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.graph.client_id,
                "client_secret": self.config.graph.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
        return self._token

    def send_run_summary(self, summary: RunSummary) -> None:
        if not self.config.reporting.summary_recipients:
            self.logger.warning("Mail summary habilitado, pero no hay destinatarios configurados.")
            return
        if requests is None:
            self.logger.error("requests no instalado — no se puede enviar mail.")
            return

        sender = self.config.graph.sender
        if not sender:
            self.logger.error("GRAPH_SENDER no configurado — no se puede enviar mail.")
            return

        subject, body = self._build_message(summary)

        to_recipients = [
            {"emailAddress": {"address": addr}}
            for addr in self.config.reporting.summary_recipients
        ]

        try:
            token = self._get_token()
            resp = requests.post(
                _SEND_MAIL_URL.format(sender=sender),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "message": {
                        "subject": subject,
                        "body": {"contentType": "HTML", "content": body},
                        "toRecipients": to_recipients,
                    },
                    "saveToSentItems": False,
                },
                timeout=30,
            )
            resp.raise_for_status()
            self.logger.info(
                "Mail enviado | run_id=%s | recipients=%s",
                summary.run_id,
                ", ".join(self.config.reporting.summary_recipients),
            )
        except Exception as exc:
            detail = ""
            try:
                detail = f" | {exc.response.json()}"
            except Exception:
                pass
            self.logger.error("No se pudo enviar el mail de resumen: %s%s", exc, detail)

    def _build_message(self, summary: RunSummary) -> tuple[str, str]:
        estado = "con errores" if summary.error_count else "exitosa"
        subject = f"[Facturas PDF] Corrida {summary.run_id} — {estado}"

        excel_count = summary.success_count + summary.warning_count

        subtypes = ["Factura", "Nota de Crédito", "Nota de Débito", "Acuse de Devolución"]
        subtype_rows = "".join(
            f"<tr><td style='padding:4px 12px'>{s}</td>"
            f"<td style='padding:4px 12px;text-align:center'><b>{summary.subtype_counts.get(s, 0)}</b></td></tr>"
            for s in subtypes
        )

        error_rows = ""
        for r in summary.results:
            if r.status == "error":
                error_rows += (
                    f"<tr><td style='padding:4px 12px;color:#c00'>{r.file_path.name}</td>"
                    f"<td style='padding:4px 12px'>{r.error_message or '-'}</td></tr>"
                )

        error_section = ""
        if error_rows:
            error_section = f"""
            <h3 style='color:#c00'>Archivos con error</h3>
            <table border='1' cellspacing='0' cellpadding='0' style='border-collapse:collapse;font-size:13px'>
              <tr style='background:#f2dede'><th style='padding:4px 12px'>Archivo</th><th style='padding:4px 12px'>Error</th></tr>
              {error_rows}
            </table>"""

        fatal_section = ""
        if summary.fatal_error:
            fatal_section = f"<p style='color:#c00'><b>Error fatal:</b> {summary.fatal_error}</p>"

        duration = int((summary.finished_at - summary.started_at).total_seconds())

        body = f"""
        <div style='font-family:Arial,sans-serif;font-size:14px;max-width:600px'>
          <h2 style='color:#1F4E78'>Resumen de corrida — Facturas PDF a Excel</h2>
          <table border='1' cellspacing='0' cellpadding='0' style='border-collapse:collapse;font-size:13px;margin-bottom:16px'>
            <tr><td style='padding:4px 12px'>Archivos procesados</td><td style='padding:4px 12px;text-align:center'><b>{summary.total_files}</b></td></tr>
            <tr><td style='padding:4px 12px'>Exitosos</td><td style='padding:4px 12px;text-align:center'><b style='color:green'>{summary.success_count + summary.warning_count}</b></td></tr>
            <tr><td style='padding:4px 12px'>Con error</td><td style='padding:4px 12px;text-align:center'><b style='color:{"#c00" if summary.error_count else "green"}'>{summary.error_count}</b></td></tr>
            <tr><td style='padding:4px 12px'>Excel generados</td><td style='padding:4px 12px;text-align:center'><b>{excel_count}</b></td></tr>
            <tr><td style='padding:4px 12px'>Duración</td><td style='padding:4px 12px;text-align:center'>{duration}s</td></tr>
          </table>

          <h3 style='color:#1F4E78'>Por tipo de comprobante</h3>
          <table border='1' cellspacing='0' cellpadding='0' style='border-collapse:collapse;font-size:13px;margin-bottom:16px'>
            <tr style='background:#2E75B6;color:white'><th style='padding:4px 12px'>Tipo</th><th style='padding:4px 12px'>Cantidad</th></tr>
            {subtype_rows}
          </table>

          {error_section}
          {fatal_section}

          <p style='color:#888;font-size:11px'>Corrida: {summary.run_id} | {summary.started_at.strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        """
        return subject, body
