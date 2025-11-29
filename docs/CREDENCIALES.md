# Guía de Actualización de Credenciales

## Por qué necesitas actualizar las credenciales

Las cookies y tokens de autenticación tienen tiempo de expiración. Cuando esto sucede, verás uno de estos errores:

- ❌ "You don't have access to this record"
- ❌ "markup://aura:invalidSession"
- ❌ "invalid_csrf"

## Método 1: Actualización Manual (Recomendado para primera vez)

### Paso 1: Obtener las credenciales desde el navegador

1. Abre Chrome/Firefox y navega a: https://verifone123.my.site.com/verifonefs
2. Inicia sesión si es necesario
3. Abre las **DevTools** (presiona F12)
4. Ve a la pestaña **Network**
5. Navega a cualquier work order para generar tráfico
6. En la lista de peticiones, busca una que se llame **"aura"**
7. Click derecho sobre ella → **Copy** → **Copy as cURL**

### Paso 2: Extraer los valores del comando curl

El comando curl que copiaste contiene toda la información necesaria. Busca:

#### A. Las cookies (línea que empieza con `-H 'Cookie:`)

Identifica cada valor:
- `sid=XXXXX` → Este es el MÁS IMPORTANTE
- `BrowserId=XXXXX`
- `renderCtx=XXXXX`
- etc.

#### B. El token (en `--data-raw` o `--data-urlencode`)

Busca: `aura.token=XXXXX`

**⚠️ IMPORTANTE**: Si el token contiene `%3D` o `%2F`, está URL-encoded y necesitas decodificarlo.

Para decodificar, usa Python:
```bash
python3 -c "from urllib.parse import unquote; print(unquote('TU_TOKEN_AQUI'))"
```

### Paso 3: Actualizar el archivo .env

Abre el archivo `.env` y reemplaza los valores:

```bash
# Las cookies más importantes
COOKIE_SID=00D4P0000010NXY!AQEAQ...  # ← Reemplazar con tu nuevo SID
COOKIE_BROWSER_ID=bygjMKjf...        # ← Actualizar
# ... etc.

# El token (SIN URL encoding)
AURA_TOKEN=eyJub25jZSI6...  # ← Debe tener "=" al final, NO "%3D"
```

### Paso 4: Verificar

Ejecuta el script:
```bash
python3 generate_invoice.py
```

Si ves:
```
Status Code para 0WOVy00000FKsV3OAL: 200
   ✓ Datos parseados correctamente
```

¡Éxito! Las credenciales funcionan.

## Método 2: Script Automático (En desarrollo)

Puedes usar el script `update_credentials.py` para actualizar automáticamente:

```bash
python3 update_credentials.py
```

Luego pega el comando curl completo cuando se te solicite.

**Nota**: Este método está en desarrollo y puede necesitar ajustes.

## Valores que cambian frecuentemente

| Variable | Frecuencia | Importancia |
|----------|-----------|-------------|
| `COOKIE_SID` | Cada sesión | ⚠️⚠️⚠️ Crítico |
| `AURA_TOKEN` | Cada sesión | ⚠️⚠️⚠️ Crítico |
| `COOKIE_BROWSER_ID` | Cada navegador | ⚠️ Media |
| `COOKIE_CLIENT_SRC` | Cada IP | ⚠️ Media |
| Otros | Raramente | ℹ️ Baja |

## Checklist de troubleshooting

Si el script no funciona después de actualizar:

- [ ] ¿El SID (`COOKIE_SID`) está actualizado?
- [ ] ¿El token (`AURA_TOKEN`) está decodificado (sin `%3D`)?
- [ ] ¿Copiaste el comando curl COMPLETO?
- [ ] ¿Tu sesión en el navegador sigue activa?
- [ ] ¿El archivo .env tiene las líneas correctas (sin espacios extra)?

## Cómo saber si necesitas actualizar

Ejecuta el script. Si ves en la salida:

```
⚠️  Error de acceso: You don't have access to this record
```

O:

```
⚠️  Error al parsear JSON
Respuesta recibida: */{"event":{"descriptor":"markup://aura:invalidSession"
```

→ Es hora de actualizar las credenciales.

## Preguntas Frecuentes

### ¿Con qué frecuencia debo actualizar?

Depende de cuánto tiempo mantengas tu sesión abierta en el navegador. Típicamente:
- Si cierras el navegador: necesitarás actualizar
- Si cambias de red/IP: puede que necesites actualizar
- En general: actualiza cada vez que ejecutes el script después de varias horas

### ¿Puedo usar credenciales de otra computadora?

No, las cookies están vinculadas a tu navegador específico y sesión. Debes obtenerlas desde la misma máquina donde ejecutas el script.

### ¿Por qué el token tiene que estar decodificado?

El servidor espera el token en formato plano. Si está URL-encoded, el servidor no lo puede validar y rechaza la petición.

## Seguridad

⚠️ **IMPORTANTE**:
- NUNCA compartas tu archivo `.env`
- NUNCA subas el `.env` a Git (está en `.gitignore`)
- El SID y token son como tu contraseña
- Si alguien obtiene tu SID, puede acceder a tu cuenta

---

¿Problemas? Revisa el README.md o abre un issue.
