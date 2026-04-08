# Analisis Tecnico de PDFs de Ejemplo

Fecha de analisis: 2026-04-07

## Objetivo

Evaluar los PDFs de ejemplo para estimar:

- diferencias de estructura entre proveedores
- patrones comunes reutilizables
- necesidad de tratamiento especifico por proveedor o tipo documental
- variabilidad de labels relevantes

## Alcance real del analisis

El entorno local analizado no tiene Azure SDK ni credenciales activas, por lo que no fue posible correr Azure Document Intelligence sobre estos archivos en esta instancia.

El analisis se hizo sobre:

- nombres de archivo
- metadatos PDF
- presencia o ausencia de capa de texto embebida
- texto recuperable desde streams PDF cuando existia

## Archivos revisados

- `pdf_input_examples/00003_00000012-UNISHOP.pdf`
- `pdf_input_examples/08_1795_CREDITO_0020-00006025 Nordelta.PDF`
- `pdf_input_examples/08_2713_FACTURA_0020-00158092 Naesqui.PDF`
- `pdf_input_examples/Fact.Vta. Nro.  0000500010910 - Fecha 10-03-20261.PDF`

## Hallazgos por archivo

### 1. `00003_00000012-UNISHOP.pdf`

- No se pudo recuperar texto legible localmente.
- Se detecta uso de imagen, sin evidencia clara de capa textual reutilizable.
- Riesgo: puede requerir OCR puro o depender por completo de Azure.
- Conclusion provisoria: caso de alta incertidumbre tecnica; no alcanza para inferir labels ni layout real.

### 2. `08_1795_CREDITO_0020-00006025 Nordelta.PDF`

- Proveedor identificado: `UNISHOP SA`.
- Tipo documental visible en texto: `Nota de Credito`.
- Label de condicion de venta: `COND.DE VENTA`.
- Valor detectado de condicion de pago/venta: `CONTADO INMEDIATO`.
- Label de fecha del documento: `Fecha`.
- Label de CAE: `C.A.E.`
- Label de vencimiento fiscal: `Fecha Vto.`
- Label de total: `Total`.
- Label de importe neto: `Neto`.
- Contiene tabla/tabularidad estable de items o movimientos.

### 3. `08_2713_FACTURA_0020-00158092 Naesqui.PDF`

- Proveedor identificado: `UNISHOP SA`.
- Tipo documental visible en texto: `Factura`.
- Mismo layout base que la nota de credito anterior.
- Cambian el tipo documental y algunos valores, pero la estructura general es altamente reutilizable.
- Tambien aparecen `COND.DE VENTA`, `Fecha`, `C.A.E.`, `Fecha Vto.`, `Total`, `Neto`.

### 4. `Fact.Vta. Nro.  0000500010910 - Fecha 10-03-20261.PDF`

- Proveedor identificado: `PEYHACHE S.A.`
- Layout marcadamente distinto al de UNISHOP.
- Labels observables:
  - `FACTURA NRO.`
  - `Fecha de emisión`
  - `Plazo de pago`
  - `CAE N°`
  - `Fecha de Vto. de CAE`
  - `Importe Neto`
  - `Importe Total`
  - `Importe Otros Tributos`
- El PDF contiene mucho mas texto estructurado que los ejemplos de UNISHOP.
- Expone de forma mas explicita la separacion entre fecha comercial y fecha fiscal.

## Patrones comunes observados

- Hay al menos un conjunto comun de conceptos de negocio/fiscales:
  - numero de comprobante
  - fecha del comprobante
  - total/neto
  - CAE
  - fecha de vencimiento del CAE
  - condicion o plazo de pago
- El concepto existe en varios documentos, pero los labels cambian.
- El layout y la densidad textual varian mucho entre ejemplos.

## Variabilidad de labels

Ejemplos observados:

- Fecha comercial:
  - `Fecha`
  - `Fecha de emisión`
- Condicion de pago:
  - `COND.DE VENTA`
  - `Plazo de pago`
- Tipo documental:
  - `Factura`
  - `Nota de Credito`
- Vencimiento fiscal:
  - `Fecha Vto.`
  - `Fecha de Vto. de CAE`
- Importes:
  - `Neto`
  - `Importe Neto`
  - `Total`
  - `Importe Total`

Conclusion: no conviene depender de un unico set de labels hardcodeado.

## Evaluacion por proveedor

### UNISHOP

- Los dos ejemplos legibles muestran una familia documental coherente.
- Hay alta probabilidad de reutilizar una misma estrategia de parsing/mapeo para varios tipos documentales del mismo proveedor.
- El tipo documental parece detectable dentro del mismo layout base.

### PEYHACHE

- Requiere otra estrategia de lectura/mapeo.
- Tiene labels mas explicitos y un layout diferente.
- No conviene forzar una plantilla unica para unificarlo con UNISHOP en esta etapa.

## Implicancias para la arquitectura

- Se justifica mantener clasificacion documental desacoplada.
- Se justifica contemplar una futura capa de `document family` o `layout profile` ademas de `document_type`.
- Se justifica no cerrar aun un parser unico por labels fijos.
- Se justifica mantener campos fiscales separados:
  - `invoice_due_date`
  - `cae_due_date`
  - `cae`
- Se justifica permitir logica comun por concepto y overrides por proveedor/layout.

## Conclusion tecnica actual

- No todos los PDFs tienen la misma calidad estructural.
- Hay evidencia de patrones reutilizables dentro de un mismo proveedor/layout.
- Hay evidencia suficiente de que no todos los proveedores podran resolverse con el mismo tratamiento fino.
- La estrategia recomendada sigue siendo:
  - modelo interno comun
  - clasificacion desacoplada
  - adaptadores/mapeos especificos por layout cuando haga falta
  - evitar hardcodear labels definitivos hasta validar Azure sobre estos ejemplos

## Siguiente validacion recomendada

Cuando el entorno tenga Azure Document Intelligence operativo:

- correr los 4 ejemplos por Azure
- comparar salida estructurada por archivo
- medir cuales campos salen nativos y cuales necesitan refuerzo
- verificar si `cae`, `cae_due_date` y `payment_terms` aparecen de forma consistente
- confirmar si `00003_00000012-UNISHOP.pdf` es OCR puro o responde a otra estructura documental
