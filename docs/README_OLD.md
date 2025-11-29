# Generador de Facturas para Work Orders

Este script en Python genera facturas en formato HTML a partir de datos de work orders obtenidos desde el sistema Verifone.

## Características

- ✅ Obtiene IDs de work orders automáticamente desde API Header
- ✅ Guarda automáticamente los IDs en `allWO.json` en cada ejecución
- ✅ **Peticiones paralelas**: Procesa hasta 10 work orders simultáneamente
- ✅ **Doble petición por Work Order**: Obtiene datos básicos + información PII (terminal_id, dirección, etc.)
- ✅ Crea una carpeta con timestamp para cada ejecución en `VerifoneWorkOrders/`
- ✅ Genera archivo HTML con tabla de resultados
- ✅ Calcula MultipleJobID automáticamente (trabajos en misma dirección/fecha)
- ✅ Guarda respuestas raw en JSON para debug
- ✅ Indicador de progreso en tiempo real
- ✅ Estadísticas de tiempo y éxito/fallos
- ✅ Logging detallado de errores

## Requisitos

- Python 3.9+
- Librerías: `requests`, `python-dotenv`

### Instalación de dependencias

```bash
pip3 install -r requirements.txt
```

O manualmente:
```bash
pip3 install requests python-dotenv
```

## Archivos principales

| Archivo | Descripción |
|---------|-------------|
| `generate_invoice.py` | Script principal que genera las facturas |
| `update_credentials.py` | **Actualiza credenciales por tipo de petición** |
| `debug_curl.py` | **Genera comandos cURL para debug con 3 opciones** |
| `allWO.json` | IDs de work orders (se actualiza automáticamente) |
| `.env` | Configuración y credenciales (NO COMPARTIR) |

## Uso básico

### 1. Actualizar credenciales

Las credenciales (cookies, tokens) expiran frecuentemente. Para actualizarlas:

```bash
python3 update_credentials.py
```

**NUEVO:** El script ahora tiene un menú con 3 opciones:

```
  1. HEADER - Petición de cabecera (lista de Work Orders)
     → Actualiza: cookies + AURA_TOKEN_HEADER

  2. PRIMERA - Primera petición (detalles de Work Order)
     → Actualiza: cookies + AURA_TOKEN

  3. PII - Petición de información sensible
     → Actualiza: cookies + AURA_TOKEN_PII
```

**¿Cuál opción usar?**
- **Opción 1 (HEADER)**: Si no se obtiene la lista de Work Orders
- **Opción 2 (PRIMERA)**: Si falla al obtener detalles de un Work Order
- **Opción 3 (PII)**: Si las columnas TerminalID, Suburb, Postcode están vacías

**Cada tipo de petición puede usar tokens diferentes**, por eso ahora puedes actualizarlos por separado.

#### Pasos para actualizar credenciales:

1. Abre el navegador y ve al sitio de Verifone
2. Abre DevTools (F12) > Network
3. Navega según la opción:
   - Opción 1: Ve a la lista de Work Orders
   - Opción 2: Click en un Work Order específico
   - Opción 3: Ve a la sección con Terminal ID/dirección
4. Busca la petición a 'aura' en Network
5. Click derecho > Copy > Copy as cURL
6. El script lo leerá del clipboard automáticamente

### 2. Generar facturas

```bash
python3 generate_invoice.py
```

El script:
1. Obtiene lista de IDs desde API Header
2. Guarda los IDs en `allWO.json` automáticamente
3. Hace 2 peticiones por cada Work Order:
   - Primera: Datos básicos (JobID, Status, etc.)
   - Segunda (PII): Información sensible (terminal_id, dirección, etc.)
4. Calcula MultipleJobID para trabajos en misma dirección/día
5. Genera HTML con todas las columnas
6. Guarda respuestas raw para debug

### 3. Debug de peticiones

Si algo falla, usa el script de debug:

```bash
python3 debug_curl.py
```

**Menú con 3 opciones:**
1. **Debug petición CABECERA** - Lista de Work Orders
2. **Debug PRIMERA petición** - Detalles de un Work Order
3. **Debug petición PII** - Información sensible

Cada opción genera el comando cURL exacto que Python ejecuta, para que puedas probarlo manualmente y ver qué está fallando.

## Estructura del HTML generado

El archivo HTML contiene una tabla con las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| JobID | ID del trabajo (WorkOrderNumber) |
| FSP | Field Service Provider |
| ClientID | Cliente (Bank_Brand) |
| JobType | Tipo de trabajo (SWAP, INSTALL, etc.) |
| **TerminalID** | **ID del terminal (desde PII)** |
| RequiredBy | Fecha requerida |
| MerchantName | Nombre del comerciante |
| **Suburb** | **Ciudad (desde PII)** |
| **Postcode** | **Código postal (desde PII)** |
| Area | Área/Estado/Zona |
| OnSiteDateTime | Fecha/hora de llegada |
| DeviceType | Tipo de dispositivo |
| ProjectNo | Número de proyecto |
| Billable | Si es facturable |
| Fix | Estado (Completed/Failed) |
| SLAMet | Si cumplió SLA |
| **MultipleJobID** | **ID del trabajo principal si hay múltiples en misma dirección/día** |
| ExtraTime | Tiempo extra |
| AfterHour | Si fue fuera de horario (6pm-6am) |
| Weekend | Si fue fin de semana |
| Extratime (Block) | Bloques de tiempo extra |
| Charge | Cargo calculado |

## Configuración avanzada

### Archivo .env

Las credenciales y configuración están en `.env`:

```bash
# Cookies (compartidas por todas las peticiones)
COOKIE_SID=...
COOKIE_OID=...
# ... más cookies

# Tokens separados por tipo de petición
AURA_TOKEN_HEADER=...    # Para obtener lista de Work Orders
AURA_TOKEN=...            # Para obtener detalles de Work Order
AURA_TOKEN_PII=...        # Para obtener información PII

# URLs y configuración
API_URL_HEADER=...
API_URL=...
API_URL_PII=...
```

### Modificar cantidad de work orders

Por defecto procesa todos los Work Orders obtenidos. Para limitar:

```python
# En generate_invoice.py, línea ~920
work_order_ids = work_order_ids[:10]  # Procesar solo 10
```

## Solución de problemas

### ❌ No se obtienen Work Orders

**Síntoma:** `No se pudieron obtener IDs desde Header API`

**Solución:**
```bash
python3 update_credentials.py
# Selecciona opción 1 (HEADER)
```

### ❌ Columnas TerminalID, Suburb, Postcode vacías

**Síntoma:** Los Work Orders se procesan pero faltan datos PII

**Diagnóstico:**
```bash
python3 debug_curl.py
# Selecciona opción 3 (PII)
# Copia el cURL y ejecútalo en terminal
# Si ves error 401/403 → Credenciales expiradas
```

**Solución:**
```bash
python3 update_credentials.py
# Selecciona opción 3 (PII)
```

### ❌ Error: "You don't have access to this record"

Las cookies o el token han expirado. Actualiza credenciales (opción 2 o 3 según la petición que falla).

### ❌ MultipleJobID no se calcula

El MultipleJobID se calcula cuando hay múltiples trabajos que cumplen:
- Misma fecha (día/mes/año)
- Misma dirección (street)

Si está vacío, puede ser porque:
1. No hay trabajos múltiples en la misma ubicación/día
2. El campo `street` está vacío (problema con petición PII)

**Solución:** Actualiza credenciales PII (opción 3)

### ⚠️ Mensajes de error en consola

El script ahora muestra mensajes detallados:

```
⚠️  Error en petición PII para 0WOVy...: Status 401
⚠️  No se extrajeron datos PII para 0WOVy... (outputVariables: 0)
⚠️  No hay respuesta PII para 0WOVy...
```

Estos mensajes indican exactamente qué está fallando.

## Rendimiento

Con paralelización activada (10 workers simultáneos):
- **145 work orders procesados en ~24 segundos** (2 peticiones por WO)
- Velocidad promedio: ~6 work orders por segundo
- Sin paralelización tomaría ~4-5 minutos

## Cambios recientes

### ✅ Actualización selectiva de tokens (Noviembre 2025)

- `update_credentials.py` ahora tiene menú con 3 opciones
- Permite actualizar cada token por separado
- Cada tipo de petición puede usar su propio token

### ✅ Formato correcto petición PII (Noviembre 2025)

- Actualizado formato del Referer y pageURI para petición PII
- Ahora incluye parámetros: `tour=`, `isdtp=p1`, `nonce=`, etc.
- Formato idéntico al navegador

### ✅ allWO.json se actualiza automáticamente (Noviembre 2025)

- Ya no necesitas mantener `allWO.json` manualmente
- Se actualiza automáticamente en cada ejecución de `generate_invoice.py`

### ✅ debug_curl.py con 3 opciones (Noviembre 2025)

- Menú interactivo para generar cURL de debug
- Opción 1: Cabecera (lista de WO)
- Opción 2: Primera petición (detalles WO)
- Opción 3: Petición PII (información sensible)

### ✅ Logging detallado de errores (Noviembre 2025)

- Mensajes claros cuando falla petición PII
- Indica exactamente qué dato falta
- Facilita el debug

## Estructura de archivos

```
.
├── generate_invoice.py          # Script principal
├── update_credentials.py        # Actualiza credenciales (CON MENÚ)
├── debug_curl.py                # Debug cURL (CON MENÚ)
├── allWO.json                   # IDs (se actualiza automáticamente)
├── requirements.txt             # Dependencias
├── .env                         # Credenciales (NO COMPARTIR)
├── .env.example                 # Plantilla de configuración
├── .gitignore                   # Archivos ignorados
├── README.md                    # Esta documentación
└── VerifoneWorkOrders/          # Carpeta de salidas
    └── invoice_YYYYMMDD_HHMMSS/ # Carpeta por ejecución
        ├── header.json          # Respuesta cabecera
        ├── raw_response_*.json  # Respuestas primera petición
        ├── raw_pii_response_*.json # Respuestas PII
        └── invoice_*.html       # Factura generada
```

## Próximas mejoras

- [x] Paralelización de peticiones ✅
- [x] Doble petición (básica + PII) ✅
- [x] Cálculo de MultipleJobID ✅
- [x] Cálculo automático de weekend/after hours ✅
- [x] Actualización selectiva de tokens ✅
- [ ] Exportación a CSV/Excel
- [ ] Configuración de workers paralelos en .env
- [ ] Reintentos automáticos en caso de errores
