#!/usr/bin/env python3
"""
Script auxiliar para actualizar las credenciales en el archivo .env
Permite actualizar tokens específicos para cada tipo de petición
"""

import re
from pathlib import Path
from urllib.parse import unquote


def extract_cookie_value(cookie_string, cookie_name):
    """Extrae el valor de una cookie específica desde el string de cookies."""
    pattern = rf'{re.escape(cookie_name)}=([^;]+)'
    match = re.search(pattern, cookie_string)
    return match.group(1) if match else None


def update_header_credentials(curl_command):
    """
    Actualiza credenciales para la petición HEADER (lista de Work Orders).
    Solo actualiza: cookies + AURA_TOKEN_HEADER
    """
    print("\n" + "="*70)
    print("ACTUALIZANDO CREDENCIALES PARA PETICIÓN HEADER")
    print("="*70)
    print()

    return update_credentials(curl_command, token_type='HEADER')


def update_first_request_credentials(curl_command):
    """
    Actualiza credenciales para la PRIMERA petición (detalles de Work Order).
    Solo actualiza: cookies + AURA_TOKEN
    """
    print("\n" + "="*70)
    print("ACTUALIZANDO CREDENCIALES PARA PRIMERA PETICIÓN")
    print("="*70)
    print()

    return update_credentials(curl_command, token_type='FIRST')


def update_pii_credentials(curl_command):
    """
    Actualiza credenciales para la petición PII (información sensible).
    Solo actualiza: cookies + AURA_TOKEN_PII
    """
    print("\n" + "="*70)
    print("ACTUALIZANDO CREDENCIALES PARA PETICIÓN PII")
    print("="*70)
    print()

    return update_credentials(curl_command, token_type='PII')


def update_ingenico_credentials(curl_command):
    """
    Actualiza credenciales para Ingenico eCAMS.
    Extrae: cookies + filtros de búsqueda (assigned_to, job_type, fechas, page_size)
    """
    print("\n" + "="*70)
    print("ACTUALIZANDO CREDENCIALES PARA INGENICO eCAMS")
    print("="*70)
    print()

    print("Extrayendo información del comando curl...")

    # Extraer cookies
    cookie_match = re.search(r"-H 'Cookie: ([^']+)'", curl_command)
    if not cookie_match:
        # Intentar con comillas dobles
        cookie_match = re.search(r'-H "Cookie: ([^"]+)"', curl_command)

    if not cookie_match:
        print("❌ No se encontraron cookies en el comando curl")
        return False

    cookie_string = cookie_match.group(1)

    # Mapeo de cookies de Ingenico
    ingenico_cookie_mapping = {
        '__utmz': 'INGENICO_COOKIE_UTMZ',
        'ASP.NET_SessionId': 'INGENICO_COOKIE_SESSION_ID',
        '__RequestVerificationToken_L2VDQU1T0': 'INGENICO_COOKIE_REQUEST_VERIFICATION',
        '__utmc': 'INGENICO_COOKIE_UTMC',
        '__utma': 'INGENICO_COOKIE_UTMA',
        '__utmt': 'INGENICO_COOKIE_UTMT',
        '__utmb': 'INGENICO_COOKIE_UTMB'
    }

    # Extraer filtros del POST data
    # Buscar assigned_to
    assigned_to_match = re.search(r'cboAssignedTo[=\']([^\s&\'\"]+)', curl_command)
    assigned_to = assigned_to_match.group(1) if assigned_to_match else '5516'

    # Buscar job_type
    job_type_match = re.search(r'cboJobType[=\']([^\s&\'\"]+)', curl_command)
    job_type = job_type_match.group(1) if job_type_match else 'ALL'

    # Buscar from_date
    from_date_match = re.search(r'txtFromDate[=\']([^\s&\'\"]+)', curl_command)
    from_date = unquote(from_date_match.group(1)) if from_date_match else '01/10/25'

    # Buscar to_date
    to_date_match = re.search(r'txtToDate[=\']([^\s&\'\"]+)', curl_command)
    to_date = unquote(to_date_match.group(1)) if to_date_match else '31/10/25'

    # Buscar page_size
    page_size_match = re.search(r'cboPageSize[=\']([^\s&\'\"]+)', curl_command)
    page_size = page_size_match.group(1) if page_size_match else '100'

    print(f"✓ Filtros extraídos:")
    print(f"  - Técnico asignado: {assigned_to}")
    print(f"  - Tipo de trabajo: {job_type}")
    print(f"  - Fecha desde: {from_date}")
    print(f"  - Fecha hasta: {to_date}")
    print(f"  - Page size: {page_size}")

    # Leer el archivo .env actual
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ No se encontró el archivo .env")
        return False

    with open(env_path, 'r') as f:
        env_content = f.read()

    # Actualizar cada cookie
    updates_count = 0
    print()
    print("Actualizando cookies de Ingenico...")
    for cookie_name, env_var in ingenico_cookie_mapping.items():
        cookie_value = extract_cookie_value(cookie_string, cookie_name)
        if cookie_value:
            # Reemplazar el valor en el contenido del .env
            pattern = rf'^{env_var}=.*$'
            replacement = f'{env_var}={cookie_value}'
            env_content, count = re.subn(pattern, replacement, env_content, flags=re.MULTILINE)
            if count > 0:
                updates_count += 1
                print(f"  ✓ {env_var}")

    # Actualizar filtros de búsqueda
    print()
    print("Actualizando filtros de búsqueda...")

    filter_mapping = {
        'INGENICO_ASSIGNED_TO': assigned_to,
        'INGENICO_JOB_TYPE': job_type,
        'INGENICO_FROM_DATE': from_date,
        'INGENICO_TO_DATE': to_date,
        'INGENICO_PAGE_SIZE': page_size
    }

    for env_var, value in filter_mapping.items():
        pattern = rf'^{env_var}=.*$'
        replacement = f'{env_var}={value}'
        env_content, count = re.subn(pattern, replacement, env_content, flags=re.MULTILINE)
        if count > 0:
            updates_count += 1
            print(f"  ✓ {env_var}")
        else:
            print(f"  ⚠️  No se encontró {env_var} en .env")

    # Guardar el archivo actualizado
    with open(env_path, 'w') as f:
        f.write(env_content)

    print()
    print("="*70)
    print(f"✅ Credenciales de Ingenico actualizadas exitosamente!")
    print(f"   Total de variables actualizadas: {updates_count}")
    print("="*70)

    return True


def update_credentials(curl_command, token_type):
    """
    Actualiza el archivo .env con credenciales específicas según el tipo.

    token_type puede ser:
    - 'HEADER': Actualiza AURA_TOKEN_HEADER
    - 'FIRST': Actualiza AURA_TOKEN
    - 'PII': Actualiza AURA_TOKEN_PII
    """

    print("Extrayendo información del comando curl...")

    # Extraer cookies
    cookie_match = re.search(r"-H 'Cookie: ([^']+)'", curl_command)
    if not cookie_match:
        print("❌ No se encontraron cookies en el comando curl")
        return False

    cookie_string = cookie_match.group(1)

    # Extraer token (puede estar URL-encoded)
    token_match = re.search(r'aura\.token=([^&\s\'\"]+)', curl_command)
    if not token_match:
        print("❌ No se encontró el token en el comando curl")
        return False

    aura_token = unquote(token_match.group(1))
    print(f"✓ Token extraído y decodificado")

    # Mapeo de cookies del navegador a variables de entorno
    cookie_mapping = {
        'renderCtx': 'COOKIE_RENDER_CTX',
        'CookieConsentPolicy': 'COOKIE_CONSENT_POLICY',
        'BrowserId': 'COOKIE_BROWSER_ID',
        'autocomplete': 'COOKIE_AUTOCOMPLETE',
        'sid_Client': 'COOKIE_SID_CLIENT',
        'inst': 'COOKIE_INST',
        'oid': 'COOKIE_OID',
        '__Secure-has-sid': 'COOKIE_SECURE_HAS_SID',
        '79eb100099b9a8bf': 'COOKIE_79EB',
        'ssostartpage': 'COOKIE_SSO_START_PAGE',
        'saml_request_id': 'COOKIE_SAML_REQUEST_ID',
        'oinfo': 'COOKIE_OINFO',
        'sid': 'COOKIE_SID',
        'clientSrc': 'COOKIE_CLIENT_SRC'
    }

    # Leer el archivo .env actual
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ No se encontró el archivo .env")
        return False

    with open(env_path, 'r') as f:
        env_content = f.read()

    # Actualizar cada cookie
    updates_count = 0
    print()
    print("Actualizando cookies...")
    for cookie_name, env_var in cookie_mapping.items():
        cookie_value = extract_cookie_value(cookie_string, cookie_name)
        if cookie_value:
            # Reemplazar el valor en el contenido del .env
            pattern = rf'^{env_var}=.*$'
            replacement = f'{env_var}={cookie_value}'
            env_content, count = re.subn(pattern, replacement, env_content, flags=re.MULTILINE)
            if count > 0:
                updates_count += 1
                print(f"  ✓ {env_var}")

    # Determinar qué token actualizar según el tipo
    print()
    print("Actualizando token específico...")

    if token_type == 'HEADER':
        token_var = 'AURA_TOKEN_HEADER'
    elif token_type == 'FIRST':
        token_var = 'AURA_TOKEN'
    elif token_type == 'PII':
        token_var = 'AURA_TOKEN_PII'
    else:
        print(f"❌ Tipo de token inválido: {token_type}")
        return False

    pattern = rf'^{token_var}=.*$'
    replacement = f'{token_var}={aura_token}'
    env_content, count = re.subn(pattern, replacement, env_content, flags=re.MULTILINE)
    if count > 0:
        updates_count += 1
        print(f"  ✓ {token_var}")
    else:
        print(f"  ⚠️  No se encontró {token_var} en .env")

    # Guardar el archivo actualizado
    with open(env_path, 'w') as f:
        f.write(env_content)

    print()
    print("="*70)
    print(f"✅ Credenciales actualizadas exitosamente!")
    print(f"   Total de variables actualizadas: {updates_count}")
    print(f"   Token actualizado: {token_var}")
    print("="*70)

    return True


def read_from_clipboard():
    """Intenta leer el comando curl desde el clipboard."""
    try:
        import subprocess
        # Try macOS
        result = subprocess.run(['pbpaste'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def get_curl_command():
    """Obtiene el comando cURL desde clipboard o archivo."""
    # Try to read from clipboard first
    print("\nIntentando leer el comando curl desde el clipboard...")
    curl_command = read_from_clipboard()

    if curl_command and curl_command.startswith('curl'):
        print("✓ Comando curl encontrado en el clipboard!")
        print(f"  (Primeros 80 caracteres: {curl_command[:80]}...)")
        print()
        response = input("¿Usar este comando? (s/n): ").strip().lower()
        if response == 's' or response == 'y':
            return curl_command

    # If clipboard reading failed or user declined, read from file
    print()
    print("OPCIÓN ALTERNATIVA:")
    print("1. Copia el comando curl")
    print("2. Guárdalo en un archivo llamado 'curl_temp.txt' en esta carpeta")
    print("3. Presiona Enter cuando esté listo")
    print()
    input("Presiona Enter para continuar...")

    temp_file = Path('curl_temp.txt')
    if temp_file.exists():
        with open(temp_file, 'r') as f:
            curl_command = f.read().strip()
        print("✓ Comando curl leído desde curl_temp.txt")
        # Delete temp file
        temp_file.unlink()
        return curl_command
    else:
        print("❌ No se encontró el archivo curl_temp.txt")
        return None


def show_instructions(credential_type):
    """Muestra instrucciones específicas según el tipo de credencial."""
    print()
    print("="*70)
    print("INSTRUCCIONES")
    print("="*70)
    print()
    print("1. Abre el navegador y ve al sitio de Verifone")
    print("2. Abre DevTools (F12) > Network")

    if credential_type == '1':
        print("3. Navega a la lista de Work Orders")
        print("   (https://verifone123.my.site.com/verifonefs/s/recordlist/WorkOrder/Default)")
        print("4. Busca la petición a 'aura' que contiene 'getItems'")
    elif credential_type == '2':
        print("3. Navega a un Work Order específico")
        print("   (Click en cualquier work order de la lista)")
        print("4. Busca la petición a 'aura' que contiene 'getRecord'")
    elif credential_type == '3':
        print("3. En la página de un Work Order, busca información PII")
        print("   (Debería haber una sección con Terminal ID, dirección, etc.)")
        print("4. Busca la petición a 'aura' que contiene 'startFlow'")

    print("5. Click derecho > Copy > Copy as cURL")
    print("6. El comando se copiará al clipboard")
    print()
    print("="*70)


def main():
    """Función principal con menú de selección."""
    print()
    print("="*70)
    print("      ACTUALIZADOR DE CREDENCIALES")
    print("="*70)
    print()
    print("Este script actualiza las credenciales en .env de forma selectiva")
    print()
    print("Selecciona qué sistema quieres actualizar:")
    print()
    print("  VERIFONE:")
    print("  1. HEADER - Petición de cabecera (lista de Work Orders)")
    print("     → Actualiza: cookies + AURA_TOKEN_HEADER")
    print()
    print("  2. PRIMERA - Primera petición (detalles de Work Order)")
    print("     → Actualiza: cookies + AURA_TOKEN")
    print()
    print("  3. PII - Petición de información sensible")
    print("     → Actualiza: cookies + AURA_TOKEN_PII")
    print()
    print("  INGENICO:")
    print("  4. INGENICO - Credenciales para Closed Jobs")
    print("     → Actualiza: cookies + filtros de búsqueda")
    print()
    print("  0. Salir")
    print()

    try:
        opcion = input("Opción [1-4]: ").strip()

        if opcion == '0':
            print("Saliendo...")
            return

        if opcion not in ['1', '2', '3', '4']:
            print("❌ Opción inválida")
            return

        # Mostrar instrucciones específicas
        if opcion != '4':
            show_instructions(opcion)
        else:
            # Instrucciones para Ingenico
            print()
            print("="*70)
            print("INSTRUCCIONES PARA INGENICO")
            print("="*70)
            print()
            print("1. Abre el navegador y ve a Ingenico eCAMS")
            print("   (https://services.ingenico.com.au/eCAMS/Member/FSPClosedJobSearch.aspx)")
            print("2. Abre DevTools (F12) > Network")
            print("3. Completa el formulario de búsqueda y presiona 'GO'")
            print("4. Busca la petición POST a 'FSPClosedJobSearch.aspx'")
            print("5. Click derecho > Copy > Copy as cURL")
            print("6. El comando se copiará al clipboard")
            print()
            print("="*70)

        # Obtener el comando cURL
        curl_command = get_curl_command()

        if not curl_command or not curl_command.strip():
            print("❌ No se pudo obtener el comando curl")
            return

        print()
        print("-" * 70)

        # Procesar según la opción
        success = False
        if opcion == '1':
            success = update_header_credentials(curl_command)
        elif opcion == '2':
            success = update_first_request_credentials(curl_command)
        elif opcion == '3':
            success = update_pii_credentials(curl_command)
        elif opcion == '4':
            success = update_ingenico_credentials(curl_command)

        if success:
            print()
            print("🎉 ¡Listo! Credenciales actualizadas correctamente")
            print()
            print("PRÓXIMOS PASOS:")

            if opcion == '1':
                print("  - Las credenciales HEADER están actualizadas")
                print("  - Puedes ejecutar: python3 generate_invoice.py")
                print("  - Si falla la primera petición, actualiza opción 2")
                print("  - Si falla la petición PII, actualiza opción 3")
            elif opcion == '2':
                print("  - Las credenciales de PRIMERA petición están actualizadas")
                print("  - Si falla la petición PII, actualiza opción 3")
            elif opcion == '3':
                print("  - Las credenciales PII están actualizadas")
                print("  - Ahora deberías ver terminal_id, suburb, postcode en el invoice")
            elif opcion == '4':
                print("  - Las credenciales de INGENICO están actualizadas")
                print("  - Puedes ejecutar: python3 fetch_ingenico_closed_jobs.py")
                print("  - O usa la interfaz web en http://localhost:8080/ingenico")

            print()
        else:
            print()
            print("❌ Hubo un error al procesar el comando curl")
            print("   Verifica que hayas copiado el comando completo")
            print()

    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario")
        return


if __name__ == '__main__':
    main()
