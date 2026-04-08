# Invoice Batch

Esqueleto inicial para procesamiento batch de facturas desde archivos PDF usando Azure Document Intelligence.

## Objetivo

- Ejecutar por lote desde Windows Task Scheduler.
- Procesar archivos individualmente con tolerancia a errores.
- Generar trazabilidad por corrida y por archivo.
- Mantener desacoplados validaciones, formato CSV y envío de mail.

## Ejecución

```powershell
python -m invoice_batch --config config/settings.example.json
```

## Estado

Base técnica inicial. Los contratos principales están definidos, pero varias reglas funcionales siguen como placeholders configurables.
