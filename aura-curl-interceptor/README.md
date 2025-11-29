# ⚡ Aura cURL Interceptor

Extensión de Chrome para interceptar peticiones Aura y generar comandos cURL completos automáticamente.

## 📋 Características

- ✅ Intercepta peticiones POST a endpoints Aura (`/s/sfsites/aura`)
- ✅ Filtra automáticamente peticiones de `Technician_Work_Order_List_View`
- ✅ Genera comandos cURL completos con todos los headers
- ✅ Usa `--data-urlencode` para mantener datos sin codificar
- ✅ Interfaz gráfica moderna y fácil de usar
- ✅ Copia al portapapeles con un clic
- ✅ Historial de las últimas 20 peticiones

## 🚀 Instalación

### Método 1: Desarrollo Local (Recomendado)

1. Abre Chrome y ve a `chrome://extensions/`
2. Activa el "Modo de desarrollador" (esquina superior derecha)
3. Haz clic en "Cargar extensión sin empaquetar"
4. Selecciona la carpeta `aura-curl-interceptor`
5. ¡Listo! La extensión está instalada

### Método 2: Empaquetar extensión

1. Ve a `chrome://extensions/`
2. Haz clic en "Empaquetar extensión"
3. Selecciona la carpeta `aura-curl-interceptor`
4. Se generará un archivo `.crx` que puedes compartir

## 📖 Uso

### Paso 1: Configurar Cookies

1. Abre la extensión haciendo clic en el icono en la barra de herramientas
2. Abre DevTools (F12) y ve a la pestaña "Network"
3. Encuentra cualquier petición a Salesforce
4. Copia el header `Cookie` completo (sin incluir "Cookie:")
5. Pégalo en el campo de texto de la extensión
6. Haz clic en "💾 Guardar Cookies"

### Paso 2: Capturar Peticiones

1. Navega a tu página de Salesforce (Verifone, etc.)
2. Realiza cualquier acción que genere peticiones a Aura
3. La extensión capturará automáticamente las peticiones válidas
4. Las peticiones aparecerán en la lista

### Paso 3: Copiar cURL

1. Haz clic en cualquier petición de la lista
2. El comando cURL completo se mostrará abajo
3. Haz clic en "📄 Copiar cURL" para copiar al portapapeles
4. Pega el comando en tu terminal o aplicación

## 🎯 Filtrado de Peticiones

La extensión solo captura peticiones que cumplan con:

- ✅ URL contiene `/s/sfsites/aura`
- ✅ Método es `POST`
- ✅ Body contiene datos válidos
- ✅ El `listViewIdOrName` es `Technician_Work_Order_List_View`

Esto asegura que solo captures las peticiones relevantes para tu workflow.

## 🔧 Estructura del Proyecto

```
aura-curl-interceptor/
├── manifest.json        # Configuración de la extensión
├── popup.html          # Interfaz del popup
├── popup.js           # Lógica del popup
├── styles.css         # Estilos CSS
├── content.js         # Script de interceptación
├── icons/             # Iconos de la extensión
└── README.md          # Este archivo
```

## 🛠️ Tecnologías

- **Manifest V3** - Última versión del sistema de extensiones de Chrome
- **Chrome Storage API** - Almacenamiento persistente
- **Vanilla JavaScript** - Sin dependencias externas
- **CSS3** - Interfaz moderna con gradientes y animaciones

## 📝 Formato del cURL Generado

```bash
curl 'https://example.com/s/sfsites/aura' \
  -X POST \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Origin: https://example.com' \
  -H 'Referer: https://example.com/...' \
  -H 'User-Agent: Mozilla/5.0...' \
  -H 'Accept-Language: en-AU,en-GB...' \
  -H 'Cache-Control: no-cache' \
  -H 'Pragma: no-cache' \
  -H 'Cookie: [TUS COOKIES]' \
  --data-urlencode 'message=...' \
  --data-urlencode 'aura.context=...' \
  --data-urlencode 'aura.pageURI=...' \
  --data-urlencode 'aura.token=...'
```

## 🎨 Características de la UI

- 🎨 Diseño moderno con gradientes púrpura
- 📱 Responsive y adaptable
- ✨ Animaciones suaves
- 🌙 Código destacado con tema oscuro
- 📋 Lista de peticiones con scroll
- 🔔 Notificaciones toast
- 🎯 Indicadores de estado

## ⚙️ Permisos

La extensión requiere:

- `storage` - Para guardar cookies y peticiones
- `activeTab` - Para inyectar el script en la pestaña activa
- `scripting` - Para ejecutar el interceptor
- `host_permissions: *://*/*` - Para funcionar en cualquier sitio

## 🐛 Troubleshooting

### La extensión no captura peticiones

1. Asegúrate de haber guardado las cookies primero
2. Verifica que estás en una página de Salesforce
3. Abre la consola (F12) y busca mensajes de `[Aura Interceptor]`
4. Recarga la página después de activar la extensión

### El cURL no funciona

1. Verifica que las cookies sean correctas y estén actualizadas
2. Las cookies expiran - actualízalas regularmente
3. Asegúrate de copiar el header Cookie completo

### La interfaz no se muestra bien

1. Actualiza Chrome a la última versión
2. Desactiva otras extensiones que puedan interferir
3. Limpia la caché del navegador

## 📄 Licencia

MIT License - Úsalo libremente en tus proyectos

## 👤 Autor

Creado para facilitar el debugging y testing de peticiones Aura en Salesforce.

---

**Nota:** Esta extensión es solo para uso de desarrollo y testing. Nunca compartas tus cookies o credenciales.
