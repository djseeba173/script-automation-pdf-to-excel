# Análisis de extracción de campos — PDFs de ejemplo

Fecha: 2026-04-08

## Objetivo

Determinar, archivo por archivo, qué campos son extraíbles localmente del texto del PDF
y cuáles dependen de Azure Document Intelligence. Insumo para decidir qué lógica
adicional hace falta antes de la primera corrida real.

---

## Resumen ejecutivo

Todos los PDFs tienen capa de texto extraíble (no son imagen pura).
Hay campos que Azure no va a devolver estructurados pero que sí están presentes
en el texto crudo y pueden parsearse con regex: CAE, fecha vto. CAE, tipo de comprobante,
letra A/B/C, y claves de sucursal.

---

## Hallazgos por archivo

### 1. `00003_00000012-UNISHOP.pdf`
**Proveedor real:** TRAPEZOIDE EDICIONES  
**Destinatario:** UNISHOP SA (CUIT 33-62759915-9)  
**Observación:** 3 páginas (Original / Duplicado / Triplicado) con contenido idéntico.
Solo hace falta procesar la primera.

| Campo | Texto en PDF | Extraíble localmente |
|---|---|---|
| Tipo de comprobante | `FACTURAACOD. 01` | Sí — regex, texto fusionado por el extractor PDF |
| Letra | `A` — incrustada en `FACTURA A` | Sí — regex |
| Nro. comprobante | `Punto de Venta: Comp. Nro:00003 00000012` | Sí — regex |
| Fecha emisión | `Fecha de Emisión: 26/03/2026` | Sí |
| Fecha vto. CAE | `Fecha de Vto. de CAE: 05/04/2026` | Sí — regex |
| CAE | `CAE N°: 86139139214749` | Sí — regex |
| Condición de venta | `Contado` | Sí |
| Desc. por ítem | columna `% Bonif` — valor `45,00` | Sí — en línea de ítem |
| ISBN | `010` (código propio, no ISBN-13) | Campo `ProductCode` en Azure |
| Importe Total | `Importe Total: $ 7700,00` | Sí |
| Importe Exento | `Importe Exento: $ 7700,00` | Sí |
| IVA | `IVA 21%: $ 0,00` | Sí |
| Otros tributos | `Importe Otros Tributos: $ 0,00` | Sí |

**Clave de sucursal disponible:** `UNISHOP SA` como cliente/destinatario.
No tiene identificador entre corchetes en este documento.

---

### 2. `08_1795_CREDITO_0020-00006025 Nordelta.PDF`
**Proveedor:** UNISHOP SA  
**Destinatario:** no explicitado en texto extraíble (campos vacíos `SENOR/ES :`)  
**Observación:** 2 páginas (Original / Duplicado).

| Campo | Texto en PDF | Extraíble localmente |
|---|---|---|
| Tipo de comprobante | `Nota de Credito` | Sí — texto explícito |
| Letra | No visible en texto extraído | ❌ Depende de Azure o imagen |
| Nro. comprobante | `0020-00006025` | Sí — primera línea |
| Fecha emisión | `Fecha : 12/03/2026` | Sí — regex |
| Fecha vto. CAE | `Fecha Vto.: 22/03/2026` | Sí — regex |
| CAE | `C.A.E. :  86117359422834` | Sí — regex |
| Condición de venta | `CONTADO INMEDIATO` | Sí |
| Clave de sucursal | `[1795]` — entre corchetes junto al nombre | **Sí — patrón clave** |
| Código ítem | `LASKAI816` | Campo `ProductCode` en Azure |
| Título | `DIOSAS DE CADA MUJER (ED.ARG) (N.E.)` | Sí — campo `Description` en Azure |
| Precio | `42.650,00` | Sí |
| Dto. | `45` | Sí — columna `Dto` |
| Neto ítem | `23.458` | Sí |
| Neto total | `Neto : 23.457,50` | Sí |
| Total | `Total : 23.457,50` | Sí |
| IVA contenido | `IVA Contenido ($ 0)` | Sí |

**Clave de sucursal:** el número entre corchetes `[1795]` aparece en la misma línea
que el nombre del proveedor (`UNISHOP SA   [1795]`). Es el patrón a extraer.

---

### 3. `08_2713_FACTURA_0020-00158092 Naesqui.PDF`
**Proveedor:** UNISHOP SA  
**Destinatario:** no explicitado en texto extraíble  
**Layout:** mismo que el de la nota de crédito anterior.

| Campo | Texto en PDF | Extraíble localmente |
|---|---|---|
| Tipo de comprobante | `Factura` | Sí — texto explícito |
| Letra | No visible en texto extraído | ❌ Depende de Azure o imagen |
| Nro. comprobante | `0020-00158092` | Sí — primera línea |
| Fecha emisión | `Fecha : 09/03/2026` | Sí |
| Fecha vto. CAE | `Fecha Vto.: 19/03/2026` | Sí |
| CAE | `C.A.E. :  86106914480537` | Sí |
| Condición de venta | `CONSIGNACION` | Sí |
| Clave de sucursal | `[2713]` | **Sí — mismo patrón** |
| Códigos ítem | `SOLA079`, `SOLA089`, `LUM001`, `VIP275`, `VIP292` | Azure `ProductCode` |
| Títulos | explícitos por línea | Azure `Description` |
| Dto. por ítem | `40` o `45` | Sí — columna `Dto` |
| Neto total | `Neto : 87.991,00` | Sí |
| Total | `Total : 87.991,00` | Sí |

**Observación:** los códigos de ítem (`SOLA079`, `LUM001`, etc.) son códigos de
editorial/distribuidor, no ISBNs. El ISBN no está presente en los documentos de UNISHOP.

---

### 4. `Fact.Vta. Nro.  0000500010910 - Fecha 10-03-20261.PDF`
**Proveedor:** PEYHACHE S.A.  
**Destinatario:** Estación Libro (CUIT 33-62759915-9)  
**Observación:** 22 páginas (Original + Duplicado + Triplicado × múltiples hojas por volumen).
El contenido de cabecera y cierre se repite en cada página; el detalle de ítems se distribuye.

| Campo | Texto en PDF | Extraíble localmente |
|---|---|---|
| Tipo de comprobante | `FACTURA NRO.` | Sí |
| Letra | `A` — campo separado explícito | **Sí — muy claro** |
| Nro. comprobante | `FACTURA NRO. 00005-00010910` | Sí |
| Fecha emisión | `Fecha de emisión : 10/03/2026` | Sí |
| Fecha vto. CAE | `Fecha de Vto. de CAE: 20/03/2026` | Sí |
| CAE | `CAE N°: 86107042866417` | Sí |
| Cliente | `Estación Libro` | Azure `CustomerName` |
| CUIT cliente | `33-62759915-9` | Sí |
| Domicilio cliente | `Las Magnolias 754. Local 1044. (1629) Pilar - Buenos Aires` | Sí |
| Plazo de pago | `30 DIAS FF` | Sí |
| ISBN por ítem | código de 13 dígitos al inicio de cada línea | Sí — regex |
| Desc. por ítem | `% DESCUENTO` — columna con valores 45, 59 | Sí |
| IVA % por ítem | columna explícita — valores 0 o 21 | Sí |
| Importe Neto | `Importe Neto: Pes 8.745.471,20` (en cierre) | Sí — parcialmente fusionado |
| IVA 21% | `IVA 21%: Pes 64.272,40` | Sí |
| Percepción IIBB CABA | `Percepciones IIBB C.A.B.A  0,00` | Sí |
| Percepción IIBB Bs As | `Percepciones IIBB Bs As 0,00` | Sí |
| Percepción IVA | `Per. de IVA  0,00` | Sí |
| Importe Total | `Importe Total: Pes 9.115.802,60` | Sí |

**Clave de sucursal:** `Estación Libro` como nombre del cliente.
No tiene identificador entre corchetes, pero el domicilio también es clave
(`Las Magnolias 754. Local 1044.` → sucursal Pilar/Nordelta).

---

## Consolidado: qué sale de dónde

### Campos que salen nativos de Azure prebuilt-invoice (alta confianza)

- `VendorName` → proveedor
- `CustomerName` → nombre cliente (base para resolver sucursal)
- `InvoiceDate` → fecha de emisión
- `DueDate` → fecha de vencimiento comercial (si el PDF la expone)
- `InvoiceTotal` → importe total
- `SubTotal` → importe neto
- `TotalTax` → IVA
- `Items[].Description` → título
- `Items[].Quantity` → cantidad
- `Items[].UnitPrice` → precio unitario
- `Items[].Amount` → total línea
- `Items[].ProductCode` → código de ítem (cód. editorial o ISBN según proveedor)

### Campos que requieren parsing adicional sobre texto crudo

| Campo | Patrón a usar | Confianza |
|---|---|---|
| CAE | `CAE N[°º]?[\s:]+(\d+)` o `C\.A\.E\.\s*:\s*(\d+)` | Alta — presente en los 4 |
| Fecha vto. CAE | `Fecha.*?Vto.*?CAE.*?(\d{2}/\d{2}/\d{4})` | Alta |
| Tipo de comprobante | buscar `Factura`, `Nota de Credito`, `Nota de Débito` | Alta |
| Letra A/B/C | buscar `^[ABC]$` en campos aislados o en `FACTURA [ABC]` | Media — no aparece en UNISHOP |
| Nro. comprobante | `(\d{4})-(\d{8})` o `Comp\. Nro:(\d+)\s+(\d+)` | Alta |
| Descuento por ítem | columna variable: `% Bonif`, `Dto`, `% DESCUENTO` | Media — Azure puede traerlo |
| Otros tributos / IIBB | `Percepciones IIBB.*?(\d[\d.,]*)` | Alta para PEYHACHE, no aplica en UNISHOP |
| Clave de sucursal (bracket) | `\[(\d+)\]` junto al nombre del proveedor | Alta para UNISHOP |

### Campos con incertidumbre o dependencia por proveedor

| Campo | Situación |
|---|---|
| Letra A/B/C en UNISHOP | No aparece en texto extraído — puede estar en imagen o sencillamente no se imprime |
| ISBN | Solo PEYHACHE tiene ISBN-13 en las líneas. UNISHOP usa códigos de editorial |
| `invoice_due_date` | UNISHOP tiene `Fecha Vto.` que es vto. de CAE, no vto. comercial. Pueden coincidir |
| Descuento por ítem | Presente como texto en los 4 archivos pero puede que Azure no lo traiga estructurado |

---

## Implicancias para el código

### 1. Capa de extracción complementaria (nuevo servicio)

Hace falta un `RawTextExtractor` que, dado el texto crudo que devuelve Azure
(o extraído localmente como fallback), aplique regex para:

- CAE + fecha vto. CAE
- Tipo de comprobante + letra
- Número de comprobante (como validación cruzada)
- Clave de sucursal entre corchetes
- Otros tributos / IIBB

Azure expone el texto crudo del documento en `result.content`. No hay que llamarlo
por separado — ya viene en la misma respuesta del `analyze_document`.

### 2. BranchResolver

Tabla de mapeo configurable en `settings.json`. Clave de entrada: el texto
extraído del cliente/destinatario más el identificador entre corchetes si existe.

Ejemplos de claves observadas:
- `[1795]` → sucursal Nordelta (UNISHOP)
- `[2713]` → sucursal Naesqui/CABA (UNISHOP)
- `Estación Libro` + `Las Magnolias 754` → sucursal Pilar

### 3. Modelo de dominio — campos nuevos a agregar

```python
branch: str | None           # sucursal resuelta
document_letter: str | None  # A, B o C
document_subtype: str | None # Factura, Nota de Crédito, etc.
cae: str | None              # ya en extractor, falta poblar
cae_due_date: str | None     # ya en extractor, falta poblar
other_taxes: dict | None     # IIBB CABA, IIBB Bs As, Percepción IVA
line_discount: float | None  # por ítem
```

### 4. Multipage — solo procesar página 1

Los PDFs de UNISHOP traen Original/Duplicado/Triplicado como páginas del mismo archivo.
PEYHACHE trae 22 páginas por volumen de ítems + copias.
La cabecera y el cierre se repiten en cada página.
Hay que normalizar: tomar cabecera y cierre de la primera aparición,
y acumular ítems hasta que se detecte cambio de copia (DUPLICADO / TRIPLICADO).

---

## Próximos pasos recomendados

1. Actualizar `ExtractedDocument` con los campos nuevos
2. Agregar `RawTextExtractor` como servicio complementario al de Azure
3. Agregar `BranchResolver` con tabla configurable
4. Actualizar `AzureDocumentIntelligenceExtractor` para poblar CAE y otros campos
   desde `result.content` además de `result.documents[0].fields`
5. Documentar en `settings.example.json` la estructura de la tabla de mapeo de sucursales
6. Definir cómo manejar multipage antes de la primera corrida real
