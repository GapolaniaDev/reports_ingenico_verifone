# 🚀 Guía de Instalación Rápida

## Paso 1: Instalar la Extensión en Chrome

1. Abre **Google Chrome**
2. Navega a `chrome://extensions/` en la barra de direcciones
3. Activa el **"Modo de desarrollador"** (esquina superior derecha)
4. Haz clic en **"Cargar extensión sin empaquetar"**
5. Selecciona la carpeta `aura-curl-interceptor`
6. ✅ ¡Extensión instalada!

## Paso 2: Configurar la Extensión

### Obtener las Cookies

1. Abre tu sitio de Salesforce/Verifone
2. Abre DevTools (F12)
3. Ve a la pestaña **Network**
4. Filtra por `aura` o busca cualquier petición
5. Haz clic en una petición
6. Busca el header **"Cookie:"** en la sección "Request Headers"
7. **Copia el valor completo** (sin incluir "Cookie:")

Ejemplo:
```
renderCtx=...; CookieConsentPolicy=0:1; sid=00D4P0000010NXY!AQ...; ...
```

### Guardar las Cookies en la Extensión

1. Haz clic en el icono de la extensión (⚡) en la barra de herramientas
2. Pega el cookie en el campo de texto
3. Haz clic en **"💾 Guardar Cookies"**
4. Deberías ver: **"✓ Configurado"**

## Paso 3: Usar la Extensión

1. Con la extensión configurada, navega a Salesforce
2. Realiza cualquier acción (filtrar work orders, etc.)
3. La extensión capturará automáticamente las peticiones
4. Haz clic en cualquier petición en la lista
5. El cURL completo se mostrará abajo
6. Haz clic en **"📄 Copiar cURL"**
7. ¡Listo! Pega el comando en tu terminal o app

## 🎯 Ejemplo de Uso

### Escenario: Capturar petición de Work Orders

1. Abre Salesforce Verifone
2. Ve a la vista de Work Orders
3. Cambia algún filtro o recarga la página
4. Abre la extensión (clic en el icono ⚡)
5. Verás las peticiones capturadas
6. Haz clic en la petición más reciente
7. Copia el cURL y úsalo en tu aplicación

## 🔄 Actualizar Cookies

Las cookies **expiran** después de un tiempo. Cuando notes que los cURL no funcionan:

1. Repite el Paso 2 para obtener cookies frescas
2. Guárdalas en la extensión
3. Las nuevas peticiones usarán las cookies actualizadas

## ⚙️ Configuración Avanzada

### Limpiar Peticiones

- Haz clic en **"🗑️ Limpiar Todo"** en el footer
- Esto borra todas las peticiones guardadas

### Límite de Peticiones

- La extensión guarda las últimas **20 peticiones**
- Las más antiguas se eliminan automáticamente

### Filtrado Automático

La extensión solo captura peticiones que:
- Van a `/s/sfsites/aura`
- Son de tipo POST
- Tienen `listViewIdOrName: "Technician_Work_Order_List_View"`

## 🐛 Solución de Problemas

### La extensión no aparece

- Verifica que está activada en `chrome://extensions/`
- Recarga la página de Chrome
- Prueba desactivar/activar el "Modo de desarrollador"

### No captura peticiones

- Asegúrate de haber guardado las cookies primero
- Recarga la página de Salesforce después de instalar
- Verifica en la consola (F12) que aparezcan logs de `[Aura Interceptor]`

### El cURL no funciona

- Las cookies pueden haber expirado - actualízalas
- Verifica que copiaste el cookie completo
- Asegúrate de estar usando las cookies del mismo dominio

## 📝 Notas Importantes

- ⚠️ **NUNCA** compartas tus cookies con nadie
- ⚠️ Las cookies contienen información de sesión sensible
- ⚠️ Actualiza las cookies regularmente para evitar errores
- ✅ Esta extensión solo funciona localmente en tu navegador
- ✅ No envía datos a ningún servidor externo

## 🎨 Personalización

Si quieres personalizar los iconos:

1. Edita `create-icons.py` y cambia los colores
2. Ejecuta: `python3 create-icons.py`
3. Recarga la extensión en Chrome

O usa `generate-icons.html` para generar iconos personalizados en el navegador.

## 📚 Más Ayuda

Para más detalles, consulta el archivo `README.md` principal.

---

¡Disfruta usando la extensión! 🎉
