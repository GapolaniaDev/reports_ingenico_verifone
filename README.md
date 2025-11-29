# 🧾 Invoice Management System

**Sistema completo de gestión de facturas para Verifone e Ingenico**

---

## 📋 Tabla de Contenidos

1. [Descripción](#descripción)
2. [Inicio Rápido](#inicio-rápido)
3. [Características](#características)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [Configuración](#configuración)
6. [Uso](#uso)
7. [API Endpoints](#api-endpoints)
8. [Credenciales](#credenciales)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción

Sistema web Flask para automatizar la generación y gestión de facturas de trabajo de Verifone e Ingenico.

### Tecnologías:
- **Backend:** Flask (Python 3.9+)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **APIs:** Salesforce Aura, Ingenico Portal
- **Extensiones:** Chrome Extension (Aura cURL Interceptor)

---

## ⚡ Inicio Rápido

### 1. Requisitos
```bash
Python 3.9+
pip
```

### 2. Instalación
```bash
# Clonar repositorio
cd "Invoice OCT 2025"

# Instalar dependencias
pip3 install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Ejecutar
```bash
# Opción A: Script automático
./scripts/start_server.sh

# Opción B: Manual
python3 app/app.py
```

### 4. Acceder
Abrir en navegador: **http://localhost:8080**

---

## ✨ Características

### 🔐 Verifone
- ✅ Gestión de credenciales Aura API
- ✅ Generación automática de invoices
- ✅ Filtrado por rango de fechas
- ✅ Cálculo automático de charges por área/tipo
- ✅ Detección de trabajos "On Site"
- ✅ Exportación a Excel

### 📦 Ingenico
- ✅ Importación de "Closed Job List" HTML
- ✅ Búsqueda y descarga de trabajos cerrados
- ✅ Parsing automático de datos
- ✅ Cálculo de totales por área

### 🎨 Interfaz
- ✅ Dashboard moderno y responsive
- ✅ Indicador de estado en tiempo real
- ✅ Sistema de notificaciones modal
- ✅ Tabla interactiva con sorting
- ✅ Exportación a Excel
- ✅ Viewer unificado Ingenico + Verifone

---

## 📂 Estructura del Proyecto

```
Invoice OCT 2025/
├── app/                        # Core application
│   ├── app.py                  # Flask app principal
│   ├── generate_invoice.py     # Lógica de generación Verifone
│   └── config.py               # Configuraciones
│
├── scripts/                    # Scripts auxiliares
│   ├── fetch_ingenico_closed_jobs.py
│   ├── update_credentials.py
│   └── debug_curl.py
│
├── templates/                  # Templates HTML (Jinja2)
│   ├── base.html               # Template base
│   ├── credentials.html        # Gestión de credenciales
│   ├── viewer.html             # Viewer principal
│   └── index.html              # Dashboard
│
├── static/                     # Archivos estáticos
├── extensions/                 # Chrome extensions
│   └── aura-curl-interceptor/
│
├── tests/                      # Tests y ejemplos
├── data/                       # Datos generados
│   ├── VerifoneWorkOrders/
│   └── logs/
│
└── docs/                       # Documentación
```

---

## ⚙️ Configuración

### Variables de Entorno (.env)

#### Verifone Aura API
```bash
API_URL_HEADER=https://verifone.lightning.force.com/aura
ORIGIN_URL=https://verifone.lightning.force.com
REFERER_HEADER=https://verifone.lightning.force.com/

# Cookies (obtener desde Chrome DevTools)
AURA_COOKIE="sid=...; ..."
```

#### Ingenico API
```bash
INGENICO_BASE_URL=https://portal.ingenico.com.au
INGENICO_USERNAME=tu_usuario
INGENICO_PASSWORD=tu_password
```

### Cómo Obtener Credenciales

#### Verifone (Aura Cookie)
1. Abrir Chrome DevTools (F12)
2. Ir a Network tab
3. Navegar en Verifone Portal
4. Copiar Request Headers → Cookie
5. Pegar en `.env` → `AURA_COOKIE`

**O usar la extensión Chrome:**
1. Instalar `aura-curl-interceptor`
2. Abrir popup
3. Copiar cookie automáticamente

Más detalles: [docs/CREDENTIALS.md](docs/CREDENTIALS.md)

---

## 🚀 Uso

### Generar Invoice Verifone

1. Ir a **http://localhost:8080/viewer**
2. Click en **"Generate Invoice"**
3. Seleccionar rango de fechas
4. Configurar límite de registros
5. Generar

El sistema:
- Obtiene work orders de Salesforce Aura API
- Filtra por fecha (inclusivo)
- Calcula charges automáticamente
- Genera HTML con tabla completa
- Guarda en `VerifoneWorkOrders/invoice_YYYYMMDD_HHMMSS/`

### Cargar Archivo Ingenico

1. Ir a **http://localhost:8080/viewer**
2. En sección "Ingenico - Closed Job List"
3. Upload archivo HTML exportado de Ingenico
4. Ver resultados en tabla unificada

### Exportar a Excel

1. Cargar datos (Verifone y/o Ingenico)
2. Click en **"Export to Excel"**
3. Archivo `.xlsx` se descarga con 3 sheets:
   - All Jobs
   - Ingenico
   - Verifone

---

## 🔌 API Endpoints

### `GET /`
Redirect a `/credentials`

### `GET /credentials`
Página de gestión de credenciales

### `GET /viewer`
Viewer principal de reportes

### `POST /api/generate-invoice`
Genera invoice de Verifone

**Body:**
```json
{
  "date_from": "2025-11-01",
  "date_to": "2025-11-29",
  "search_string": "",
  "record_limit": 200
}
```

**Response:**
```json
{
  "success": true,
  "message": "Invoice generation started"
}
```

### `GET /api/generation-status`
Obtiene estado actual de generación

**Response:**
```json
{
  "running": true,
  "progress": 33,
  "total": 201,
  "message": "Procesando...",
  "errors": []
}
```

### `POST /api/save-credentials`
Guarda credenciales de Verifone

### `POST /api/test-connection`
Prueba conexión con Aura API

---

## 🔐 Credenciales

### Estructura de Credenciales Verifone

El sistema requiere cookies de sesión de Salesforce Aura:

```
sid=...
clientSrc=...
CookieConsentPolicy=...
LSKey-c$CookieConsentPolicy=...
```

### Expiración
Las cookies expiran después de ~2 horas de inactividad. Si obtienes error de autenticación, actualiza las credenciales.

### Seguridad
- ❌ **NUNCA** commitear `.env` a git
- ✅ `.env` está en `.gitignore`
- ✅ Usar `.env.example` como template

---

## 🛠️ Troubleshooting

### Error: "Server connection failed"
**Causa:** Flask server no está corriendo
**Solución:** Ejecutar `./scripts/start_server.sh`

### Error: "Authentication failed"
**Causa:** Cookies Aura expiradas
**Solución:** Actualizar cookies en `/credentials`

### Error: "No se encontró la tabla esperada"
**Causa:** Archivo HTML de Ingenico incorrecto
**Solución:** Exportar archivo correcto desde Ingenico Portal

### Trabajos "On Site" no aparecen
**Causa:** Status field no detectado
**Solución:** Verificar que el campo Status = "On Site" en Salesforce

### Cálculos incorrectos
**Causa:** Área mal calculada o job type no reconocido
**Solución:** Revisar `calculateCharge()` en `generate_invoice.py`

---

## 📊 Cálculo de Charges

### Áreas (por Postcode)
- **Area 1:** Adelaide metro (default)
- **Area 2:** Postcodes específicos (5110, 5116, 5111, etc.)
- **Area 3:** Regiones remotas

### Tarifas Base (Area 1)
- Installation/Swap: **$28.00**
- After Hours: **$80.00**
- Weekend: **$40.00**
- After Hours + Weekend: **$90.00**
- Recovery: **$10.00** (fijo)
- De-installation: **$10.00** (fijo)
- Multiple jobs: **$10.00** (segundo terminal)

**Nota:** Areas 2 y 3 tienen tarifas incrementadas. Ver código para detalles.

---

## 🎨 Sistema de Notificaciones

El sistema incluye notificaciones modales profesionales:

- ✅ **Success:** Verde - Operaciones exitosas
- ⚠️ **Warning:** Amarillo - Validaciones fallidas
- ❌ **Error:** Rojo - Errores críticos
- ℹ️ **Info:** Azul - Información general

Auto-cierre: 5s (success/info), 8s (warning/error)

---

## 🔄 Estado del Sistema

Indicador en esquina superior derecha:

- ✓ **Ready:** Sistema listo (verde, pulse suave)
- ⚙️ **Generating:** Procesando (naranja, spinner)
- ✓ **Completed:** Finalizado (verde brillante)
- ⚠️ **Error:** Error (rojo, clickeable para detalles)

---

## 📦 Dependencias

Ver `requirements.txt`:
- Flask
- requests
- python-dotenv

---

## 👨‍💻 Desarrollo

### Agregar nuevo endpoint
1. Editar `app/app.py`
2. Agregar `@app.route('/nueva-ruta')`
3. Reiniciar servidor

### Modificar cálculos
1. Editar `app/generate_invoice.py`
2. Función `calculateCharge()`
3. Probar con work orders de ejemplo

### Cambiar estilos
1. Editar `templates/base.html` (estilos globales)
2. O `templates/viewer.html` (estilos específicos)

---

## 📝 Changelog

Ver archivo `docs/CHANGELOG.md` para historial completo de cambios.

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar [Troubleshooting](#troubleshooting)
2. Revisar logs en `data/logs/flask_server.log`
3. Contactar al desarrollador

---

**Última actualización:** Noviembre 2025
