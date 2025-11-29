# 🔧 Ingenico eCAMS Integration - Quick Start Guide

## ✅ Implementación Completada

La integración de Ingenico eCAMS para descargar Closed Jobs ha sido completada exitosamente.

---

## 🎯 **Características Implementadas**

### 1. **Módulo Principal** (`fetch_ingenico_closed_jobs.py`)
   - ✅ Flujo POST → GET con sesión persistente
   - ✅ Extracción dinámica de tokens ASPX (`__VIEWSTATE`, `__EVENTVALIDATION`, `__VIEWSTATEGENERATOR`)
   - ✅ Parser HTML → JSON de tabla de Closed Jobs
   - ✅ Extrae **TODAS** las columnas de la tabla automáticamente
   - ✅ Guarda HTML raw + JSON parseado en carpetas timestamped
   - ✅ Manejo robusto de errores (sesión expirada, tokens faltantes, etc.)

### 2. **Gestión de Credenciales** (`update_credentials.py`)
   - ✅ Opción #4 agregada para Ingenico
   - ✅ Extrae cookies + filtros de búsqueda desde cURL
   - ✅ Actualiza `.env` automáticamente
   - ✅ Prelllena filtros en interfaz web

### 3. **Endpoints Flask** (`app.py`)
   - ✅ `GET /ingenico` - Interfaz web
   - ✅ `GET /api/ingenico/get-filters` - Obtiene filtros desde `.env`
   - ✅ `POST /api/ingenico/search-closed-jobs` - Ejecuta búsqueda
   - ✅ `POST /api/ingenico/update-credentials` - Actualiza credenciales
   - ✅ `GET /api/ingenico/list-downloads` - Historial de descargas

### 4. **Interfaz Web** (`templates/ingenico.html`)
   - ✅ 3 pestañas: Search / Credentials / Downloads
   - ✅ Campos prellenados desde `.env` (editables)
   - ✅ Actualización de credenciales desde cURL
   - ✅ Historial de descargas
   - ✅ Manejo de sesión expirada con mensaje claro

---

## 🚀 **Cómo Usar**

### **Método 1: Interfaz Web** (Recomendado)

1. **Iniciar el servidor Flask:**
   ```bash
   cd "/Users/gustavo/Downloads/Invoice OCT 2025"
   python3 app.py
   ```

2. **Abrir en el navegador:**
   ```
   http://localhost:8080/ingenico
   ```

3. **Primera vez - Actualizar Credenciales:**
   - Ve a la pestaña **"🔐 Update Credentials"**
   - Sigue las instrucciones para copiar el cURL
   - Pega el cURL y presiona **"Update Credentials"**
   - Los filtros se actualizarán automáticamente

4. **Buscar Closed Jobs:**
   - Ve a la pestaña **"🔍 Search Jobs"**
   - Ajusta los filtros si es necesario (prellenados desde `.env`)
   - Presiona **"🔍 Buscar Closed Jobs"**
   - Espera unos segundos
   - Verás el resumen y podrás abrir los archivos

5. **Ver Descargas Anteriores:**
   - Ve a la pestaña **"📥 Downloads History"**
   - Verás todas las búsquedas anteriores
   - Puedes abrir el JSON o HTML directamente

---

### **Método 2: CLI (Línea de Comandos)**

1. **Actualizar credenciales:**
   ```bash
   python3 update_credentials.py
   # Selecciona opción 4 (INGENICO)
   # Pega el cURL cuando se solicite
   ```

2. **Ejecutar búsqueda:**
   ```bash
   python3 fetch_ingenico_closed_jobs.py
   ```

3. **Los archivos se guardarán en:**
   ```
   closedJobIngenico/
   └── YYYYMMDD_HHMMSS_DD-MM-YYtoDD-MM-YY/
       ├── closed_jobs_01-10-25_31-10-25_YYYYMMDD_HHMMSS.html
       └── closed_jobs_01-10-25_31-10-25_YYYYMMDD_HHMMSS.json
   ```

---

## 📂 **Estructura de Archivos Generados**

### **Carpeta:**
```
closedJobIngenico/20251102_223045_01-10-25to31-10-25/
```
- Formato: `YYYYMMDD_HHMMSS_fecha-desde-fecha-hasta`

### **HTML:**
```
closed_jobs_01-10-25_31-10-25_20251102_223045.html
```
- HTML raw de la respuesta de Ingenico
- Útil para debugging si el parser falla

### **JSON:**
```json
{
  "metadata": {
    "fetch_timestamp": "20251102_223045",
    "filters": {
      "from_date": "01/10/25",
      "to_date": "31/10/25",
      "assigned_to": "5516",
      "job_type": "ALL",
      "page_size": "100"
    },
    "total_jobs": 35
  },
  "jobs": [
    {
      "JobID": "4535166",
      "FSP": "5516",
      "ClientID": "CBA",
      "JobType": "DEINSTALL",
      "TerminalID": "14695200",
      "RequiredBy": "15/10/2025 4:14:00 PM",
      "MerchantName": "AUSTRALIAN RED CROSS SOCIETY",
      "Suburb": "ADELAIDE",
      "Postcode": "5000",
      "OnSiteDateTime": "15/10/2025 11:19:00 AM",
      "OffSiteDateTime": "15/10/2025 11:19:00 AM",
      "DeviceType": "ESLITEMOVE5-MOB",
      "ProjectNo": "",
      "Billable": "Yes",
      "Fix": "COMPLETE",
      "SLAMet": "Yes",
      "MultipleJobID": "",
      "ExtraTime": "",
      "AfterHour": "No",
      "Weekend": "No",
      "ExtTermCollected": "0"
    },
    ...
  ]
}
```

---

## 🔐 **Configuración de Credenciales**

### **Variables en `.env`:**

```bash
# Cookies de sesión (se actualizan con update_credentials.py)
INGENICO_COOKIE_UTMZ=...
INGENICO_COOKIE_SESSION_ID=...
INGENICO_COOKIE_REQUEST_VERIFICATION=...
INGENICO_COOKIE_UTMC=...
INGENICO_COOKIE_UTMA=...
INGENICO_COOKIE_UTMT=...
INGENICO_COOKIE_UTMB=...

# Filtros de búsqueda (se actualizan con update_credentials.py)
INGENICO_ASSIGNED_TO=5516
INGENICO_JOB_TYPE=ALL
INGENICO_FROM_DATE=01/10/25
INGENICO_TO_DATE=31/10/25
INGENICO_PAGE_SIZE=100
```

### **Cómo Obtener el cURL:**

1. Abre el navegador y ve a:
   ```
   https://services.ingenico.com.au/eCAMS/Member/FSPClosedJobSearch.aspx
   ```

2. Abre **DevTools (F12)** → Pestaña **Network**

3. Completa el formulario de búsqueda:
   - Assigned To: 5516
   - Job Type: ALL
   - From Date: 01/10/25
   - To Date: 31/10/25
   - Page Size: 100
   - Presiona **"GO"**

4. En la pestaña Network, busca la petición **POST** a `FSPClosedJobSearch.aspx`

5. Click derecho → **Copy** → **Copy as cURL**

6. Pega en `update_credentials.py` (opción 4) o en la interfaz web

---

## ⚠️ **Manejo de Errores**

### **Sesión Expirada**
Si ves el error:
```
⚠️ Sesión expirada. Por favor actualiza las credenciales de Ingenico desde un cURL reciente.
```

**Solución:**
1. Ve a la interfaz web → Pestaña "Credentials"
2. O ejecuta `python3 update_credentials.py` (opción 4)
3. Copia un nuevo cURL desde el navegador
4. Actualiza las credenciales

### **Tokens ASPX No Encontrados**
Si ves el error:
```
TokenExtractionError: Tokens ASPX no encontrados en el formulario
```

**Solución:**
- Las cookies están expiradas
- Actualiza las credenciales con un cURL nuevo

### **POST No Retornó 302**
Si ves el error:
```
SearchFailedError: POST retornó 200 en lugar de 302
```

**Solución:**
- Los filtros o tokens son inválidos
- Actualiza las credenciales

---

## 📊 **Columnas Extraídas**

El parser extrae **TODAS** las columnas de la tabla automáticamente. Actualmente incluye:

1. JobID
2. FSP
3. ClientID
4. JobType
5. TerminalID
6. RequiredBy
7. MerchantName
8. Suburb
9. Postcode
10. OnSiteDateTime
11. OffSiteDateTime
12. DeviceType
13. ProjectNo
14. Billable
15. Fix
16. SLAMet
17. MultipleJobID
18. ExtraTime
19. AfterHour
20. Weekend
21. ExtTermCollected

*(La columna "Bulk" con el checkbox se omite automáticamente)*

---

## 🧪 **Testing**

### **Test 1: Verificar instalación**
```bash
python3 -c "from fetch_ingenico_closed_jobs import search_closed_jobs; print('✓ OK')"
```

### **Test 2: Verificar credenciales**
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Session ID:', os.getenv('INGENICO_COOKIE_SESSION_ID'))"
```

### **Test 3: Ejecutar búsqueda**
```bash
python3 fetch_ingenico_closed_jobs.py
```

---

## 📝 **Notas Importantes**

1. **Sesiones ASPX:**
   - Las sesiones de Ingenico expiran rápidamente
   - Actualiza credenciales antes de cada búsqueda grande

2. **Tokens Dinámicos:**
   - Los tokens `__VIEWSTATE`, `__EVENTVALIDATION`, `__VIEWSTATEGENERATOR` se extraen automáticamente en cada búsqueda
   - No necesitas actualizar credenciales para cada búsqueda, solo cuando la sesión expire

3. **Límite de Resultados:**
   - El `page_size` máximo es **200** (limitación de Ingenico)
   - Si tienes más trabajos, haz múltiples búsquedas con rangos de fechas más pequeños

4. **Formato de Fechas:**
   - Ingenico usa formato: `DD/MM/YY` (ej: `01/10/25`)
   - El JSON guarda las fechas tal como las devuelve Ingenico

---

## 🎉 **¡Listo para Usar!**

Tu integración de Ingenico está completa y lista para usarse. Puedes:

- ✅ Buscar Closed Jobs desde la interfaz web
- ✅ Actualizar credenciales fácilmente
- ✅ Ver historial de descargas
- ✅ Procesar los datos en JSON para análisis

**Próximos pasos sugeridos:**
1. Actualiza tus credenciales con el cURL que me proporcionaste
2. Prueba una búsqueda desde la interfaz web
3. Verifica que el JSON tenga los datos correctos
4. ¡Disfruta de la automatización! 🚀
