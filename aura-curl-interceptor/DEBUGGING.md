# 🐛 Guía de Debugging - Aura cURL Interceptor

## 📊 Logs de Consola

La extensión ahora tiene **logging extensivo** en consola para ayudarte a depurar cualquier problema.

## 🔍 Cómo Ver los Logs

### Ver logs del Content Script (Interceptor)

1. Abre tu página de Salesforce/Verifone
2. Abre DevTools (F12)
3. Ve a la pestaña **Console**
4. Deberías ver logs con el prefijo `[Aura Interceptor]`

### Ver logs del Popup

1. Haz clic derecho en el icono de la extensión (⚡)
2. Selecciona **"Inspeccionar popup"**
3. Se abrirá DevTools del popup
4. Ve a la pestaña **Console**
5. Deberías ver logs con el prefijo `[Popup]`

## 📋 Tipos de Logs

### Content Script (content.js)

Los logs del content script te dirán:

#### ✅ Inicialización
```
[Aura Interceptor] ===== INICIADO =====
[Aura Interceptor] Versión: 1.0.0
[Aura Interceptor] URL actual: https://...
[Aura Interceptor] ========== HOOKS INSTALADOS ==========
```

**Qué significa:** El interceptor se cargó correctamente y está listo.

#### 🔵 Detección de Peticiones FETCH
```
[Aura Interceptor] [FETCH] Detectada petición fetch: https://...
[Aura Interceptor] [FETCH] ✓ Petición coincide con filtros, capturando...
```

**Qué significa:** Se detectó una petición fetch que coincide con los filtros.

#### 🟣 Detección de Peticiones XHR
```
[Aura Interceptor] [XHR] open() llamado: POST https://...
[Aura Interceptor] [XHR] send() llamado: https://...
[Aura Interceptor] [XHR] ✓ Petición coincide con filtros, capturando...
```

**Qué significa:** Se detectó una petición XMLHttpRequest que coincide.

#### 🟢 Petición Válida
```
[Aura Interceptor] ✓ Es petición Aura
[Aura Interceptor] ✓ Parámetro message encontrado
[Aura Interceptor] ListView encontrado: Technician_Work_Order_List_View
[Aura Interceptor] ✓✓✓ PETICIÓN VÁLIDA ✓✓✓
[Aura Interceptor] ✓✓✓ PETICIÓN GUARDADA EXITOSAMENTE ✓✓✓
```

**Qué significa:** La petición cumple todos los requisitos y se guardó correctamente.

#### 🟠 Petición Filtrada
```
[Aura Interceptor] ❌ ListView no coincide: WorkOrderListView !== "Technician_Work_Order_List_View"
[Aura Interceptor] Petición ignorada por filtro de listView
```

**Qué significa:** La petición fue detectada pero no es del listView correcto.

#### 🔴 Errores
```
[Aura Interceptor] ❌❌❌ ERROR AL GUARDAR ❌❌❌
[Aura Interceptor] Error details: ...
```

**Qué significa:** Hubo un error al guardar la petición en storage.

### Popup (popup.js)

Los logs del popup te dirán:

#### ✅ Inicialización
```
[Popup] ===== POPUP INICIADO =====
[Popup] ✓ Cookie cargado
[Popup] ✓ Peticiones cargadas: 5
[Popup] ===== POPUP LISTO =====
```

**Qué significa:** El popup se cargó correctamente con los datos guardados.

#### 🔵 Storage Changes
```
[Popup] Storage changed!
[Popup] ✓ Nuevas peticiones detectadas: 6
```

**Qué significa:** Se detectó una nueva petición y el popup se actualizó.

## 🔧 Troubleshooting por Síntomas

### ❌ Problema: No veo ningún log de `[Aura Interceptor]`

**Diagnóstico:** El content script no se cargó.

**Soluciones:**
1. Recarga la extensión en `chrome://extensions/`
2. Recarga la página de Salesforce (F5)
3. Verifica que la extensión esté activada
4. Verifica que estés en una página permitida (no chrome://, file://, etc.)

**Verificación:**
- Ve a `chrome://extensions/`
- Busca "Aura cURL Interceptor"
- Debe estar activada (toggle ON)
- Debe tener permisos para acceder a sitios

---

### ⚠️ Problema: Veo logs de FETCH/XHR pero dice "No coincide con filtros"

**Diagnóstico:** Las peticiones se detectan pero no cumplen los criterios.

**Logs esperados:**
```
[Aura Interceptor] [FETCH] No coincide con filtros
{
  hasAura: false / true,
  isPOST: false / true,
  isString: false / true
}
```

**Soluciones:**

1. **hasAura: false** - La URL no contiene `/s/sfsites/aura`
   - Verifica que estés en la página correcta de Salesforce
   - Algunas páginas usan otros endpoints

2. **isPOST: false** - No es una petición POST
   - Las peticiones GET no se capturan
   - Asegúrate de estar haciendo acciones que generen POST

3. **isString: false** - El body no es string
   - Esto es raro, puede ser FormData u otro formato
   - Reporta este caso

---

### ⚠️ Problema: Veo "✓ Es petición Aura" pero "❌ No se encontró parámetro message"

**Diagnóstico:** Es una petición Aura pero sin el parámetro `message`.

**Logs esperados:**
```
[Aura Interceptor] ✓ Es petición Aura
[Aura Interceptor] ❌ No se encontró parámetro "message", ignorando
[Aura Interceptor] Body (primeros 500 chars): ...
```

**Soluciones:**
- Verifica el body en los logs
- Puede ser un tipo diferente de petición Aura
- Si quieres capturar este tipo, el filtro necesita ajustarse

---

### ⚠️ Problema: Veo "ListView no coincide"

**Diagnóstico:** La petición es válida pero es de un listView diferente.

**Logs esperados:**
```
[Aura Interceptor] ❌ ListView no coincide: WorkOrderListView !== "Technician_Work_Order_List_View"
```

**Soluciones:**

**Opción A: Cambiar el filtro** (Capturar TODAS las peticiones Aura)

Edita `content.js` línea 68-72, cambia:
```javascript
if (listView !== "Technician_Work_Order_List_View") {
  console.log(/* ... */);
  return;
}
```

Por:
```javascript
// REMOVER ESTE BLOQUE COMPLETO o comentarlo
// Esto capturará TODAS las peticiones Aura
```

**Opción B: Cambiar el listView esperado**

Edita `content.js` línea 68, cambia:
```javascript
if (listView !== "TU_LIST_VIEW_AQUI") {
```

Reemplaza `TU_LIST_VIEW_AQUI` por el listView que viste en los logs.

---

### ⚠️ Problema: Veo "✓✓✓ PETICIÓN VÁLIDA ✓✓✓" pero "❌❌❌ ERROR AL GUARDAR"

**Diagnóstico:** La petición se capturó pero no se pudo guardar en storage.

**Logs esperados:**
```
[Aura Interceptor] ✓✓✓ PETICIÓN VÁLIDA ✓✓✓
[Aura Interceptor] ❌❌❌ ERROR AL GUARDAR ❌❌❌
[Aura Interceptor] Error details: ...
```

**Soluciones:**
1. Verifica que la extensión tenga permiso de `storage` en `manifest.json`
2. Verifica que no haya errores de permisos en `chrome://extensions/`
3. Prueba desinstalar y reinstalar la extensión
4. Limpia el storage: Ve al popup y haz clic en "🗑️ Limpiar Todo"

---

### ❌ Problema: El popup no muestra las peticiones capturadas

**Diagnóstico:** El popup no está recibiendo las actualizaciones del storage.

**Logs en el popup esperados:**
```
[Popup] Storage changed!
[Popup] ✓ Nuevas peticiones detectadas: X
```

**Soluciones:**

1. **Verifica que el popup esté escuchando:**
   - Inspecciona el popup (clic derecho → "Inspeccionar popup")
   - Busca en console: `[Popup] ✓ Listener de storage instalado`

2. **Cierra y reabre el popup:**
   - El popup se reinicia cada vez que lo abres
   - Los logs deberían aparecer de nuevo

3. **Verifica storage manualmente:**
   - En DevTools del popup, ve a Console
   - Ejecuta: `chrome.storage.local.get(['auraRequests'], (data) => console.log(data))`
   - Deberías ver las peticiones guardadas

---

### ✅ Problema: Todo funciona pero quiero ver más detalles

**Logs adicionales disponibles:**

En cualquier momento en el popup, ejecuta en console:

```javascript
// Ver todas las peticiones guardadas
chrome.storage.local.get(['auraRequests'], (data) => {
  console.log('Peticiones guardadas:', data.auraRequests);
});

// Ver cookie guardado
chrome.storage.local.get(['auraCookie'], (data) => {
  console.log('Cookie guardado:', data.auraCookie);
});

// Ver todo el storage
chrome.storage.local.get(null, (data) => {
  console.log('Storage completo:', data);
});
```

## 🎯 Workflow de Debugging Típico

### Escenario: Configuración inicial

1. Instala la extensión
2. Abre Salesforce
3. Abre console (F12) → Console
4. **Verifica:** `[Aura Interceptor] ===== INICIADO =====`
5. Abre el popup de la extensión
6. Inspecciona el popup (clic derecho → Inspeccionar)
7. **Verifica:** `[Popup] ===== POPUP LISTO =====`
8. Pega las cookies y guarda
9. **Verifica:** `[Popup] ✓ Cookie guardado en storage`
10. **Verifica:** `[Popup] ✓ Content script inyectado exitosamente`

### Escenario: Capturando peticiones

1. Con la console abierta (F12)
2. Realiza una acción en Salesforce (filtrar, recargar, etc.)
3. **Busca en console:**
   - `[Aura Interceptor] [FETCH]` o `[XHR]`
4. **Si ves peticiones pero no se guardan:**
   - Busca qué filtro está fallando
   - Busca mensajes de "No coincide con filtros"
5. **Si ves "✓✓✓ PETICIÓN VÁLIDA ✓✓✓":**
   - ¡Excelente! Abre el popup
   - Deberías ver la petición en la lista
6. **Si ves "✓✓✓ PETICIÓN GUARDADA EXITOSAMENTE ✓✓✓":**
   - En el popup inspected, deberías ver:
   - `[Popup] Storage changed!`
   - `[Popup] ✓ Nuevas peticiones detectadas: X`

## 📞 Reportar Problemas

Si encuentras un problema que no puedes resolver:

1. Abre console de la página (F12)
2. Inspecciona el popup (clic derecho → Inspeccionar)
3. Copia TODOS los logs de ambas consoles
4. Incluye:
   - Versión de Chrome
   - URL de la página
   - Pasos para reproducir
   - Todos los logs con `[Aura Interceptor]` y `[Popup]`

## 🔄 Resetear Todo

Si todo falla, resetea completamente:

1. Abre `chrome://extensions/`
2. Remueve "Aura cURL Interceptor"
3. Reinstala la extensión (Cargar sin empaquetar)
4. Recarga la página de Salesforce
5. Abre el popup, pega cookies nuevas
6. Inspecciona ambas consoles para ver los logs de inicialización

---

Con estos logs detallados, deberías poder identificar exactamente dónde está fallando la extensión. ¡Buena suerte! 🚀
