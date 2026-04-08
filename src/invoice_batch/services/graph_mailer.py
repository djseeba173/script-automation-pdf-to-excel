from __future__ import annotations

import logging

from invoice_batch.config import AppConfig
from invoice_batch.domain.models import RunSummary


class GraphMailer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("invoice_batch.graph_mailer")

    def send_run_summary(self, summary: RunSummary) -> None:
        if not self.config.reporting.summary_recipients:
            self.logger.warning("Mail summary habilitado, pero no hay destinatarios configurados.")
            return

        # Placeholder. La implementacion real deberia:
        # 1. Obtener token OAuth2 con client credentials.
        # 2. Construir el body del mail con resumen y adjuntos si aplica.
        # 3. Invocar Microsoft Graph /sendMail.
        self.logger.info(
            "Placeholder GraphMailer | run_id=%s | recipients=%s",
            summary.run_id,
            ",".join(self.config.reporting.summary_recipients),
        )
