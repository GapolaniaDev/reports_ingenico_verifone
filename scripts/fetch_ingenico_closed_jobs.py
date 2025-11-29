#!/usr/bin/env python3
"""
Módulo para obtener Closed Jobs desde Ingenico eCAMS.
Implementa el flujo POST de búsqueda → GET del listado manteniendo sesión persistente.
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class IngenicoError(Exception):
    """Excepción base para errores de Ingenico"""
    pass


class SessionExpiredError(IngenicoError):
    """Sesión expirada - necesita actualizar credenciales"""
    pass


class TokenExtractionError(IngenicoError):
    """No se pudieron extraer tokens ASPX del formulario"""
    pass


class SearchFailedError(IngenicoError):
    """POST de búsqueda no retornó 302 redirect"""
    pass


def build_cookie_string():
    """Construye el string de cookies desde las variables de entorno."""
    cookies = [
        f"__utmz={os.getenv('INGENICO_COOKIE_UTMZ', '')}",
        f"ASP.NET_SessionId={os.getenv('INGENICO_COOKIE_SESSION_ID', '')}",
        f"__RequestVerificationToken_L2VDQU1T0={os.getenv('INGENICO_COOKIE_REQUEST_VERIFICATION', '')}",
        f"__utmc={os.getenv('INGENICO_COOKIE_UTMC', '')}",
        f"__utma={os.getenv('INGENICO_COOKIE_UTMA', '')}",
        f"__utmt={os.getenv('INGENICO_COOKIE_UTMT', '')}",
        f"__utmb={os.getenv('INGENICO_COOKIE_UTMB', '')}"
    ]
    return "; ".join(cookies)


def get_form_page():
    """
    Hace GET a FSPClosedJobSearch.aspx para obtener tokens ASPX y establecer sesión.

    Returns:
        tuple: (tokens_dict, requests.Session)

    Raises:
        TokenExtractionError: Si no se pueden extraer los tokens
    """
    logger.info("Obteniendo formulario de búsqueda...")

    search_url = os.getenv('INGENICO_SEARCH_URL')

    # Crear sesión persistente
    session = requests.Session()

    # Construir headers
    headers = {
        'User-Agent': os.getenv('INGENICO_USER_AGENT', ''),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': os.getenv('INGENICO_ACCEPT_LANGUAGE', ''),
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cookie': build_cookie_string()
    }

    try:
        response = session.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Extraer tokens ASPX usando BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        viewstate = soup.find('input', {'id': '__VIEWSTATE'})
        eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})
        viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})

        if not viewstate or not eventvalidation or not viewstategenerator:
            logger.error("No se pudieron encontrar todos los tokens ASPX en el HTML")
            raise TokenExtractionError("Tokens ASPX no encontrados en el formulario")

        tokens = {
            '__VIEWSTATE': viewstate.get('value', ''),
            '__EVENTVALIDATION': eventvalidation.get('value', ''),
            '__VIEWSTATEGENERATOR': viewstategenerator.get('value', '')
        }

        logger.info(f"✓ Tokens ASPX extraídos exitosamente")
        logger.debug(f"  __VIEWSTATE: {tokens['__VIEWSTATE'][:50]}...")
        logger.debug(f"  __EVENTVALIDATION: {tokens['__EVENTVALIDATION'][:50]}...")
        logger.debug(f"  __VIEWSTATEGENERATOR: {tokens['__VIEWSTATEGENERATOR']}")

        return tokens, session

    except requests.RequestException as e:
        logger.error(f"Error al obtener formulario: {e}")
        raise IngenicoError(f"Error al conectar con Ingenico: {e}")


def post_search(session, tokens, filters):
    """
    Envía POST con filtros de búsqueda y tokens ASPX.

    Args:
        session: requests.Session con cookies establecidas
        tokens: dict con __VIEWSTATE, __EVENTVALIDATION, __VIEWSTATEGENERATOR
        filters: dict con from_date, to_date, assigned_to, job_type, page_size

    Returns:
        bool: True si el POST fue exitoso (302 redirect)

    Raises:
        SearchFailedError: Si no se obtiene redirect 302
    """
    logger.info(f"Enviando búsqueda con filtros: {filters}")

    search_url = os.getenv('INGENICO_SEARCH_URL')

    headers = {
        'User-Agent': os.getenv('INGENICO_USER_AGENT', ''),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': os.getenv('INGENICO_ACCEPT_LANGUAGE', ''),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://services.ingenico.com.au',
        'Referer': search_url,
        'Upgrade-Insecure-Requests': '1'
    }

    # Construir form data con tokens + filtros
    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': tokens['__VIEWSTATE'],
        '__VIEWSTATEGENERATOR': tokens['__VIEWSTATEGENERATOR'],
        '__EVENTVALIDATION': tokens['__EVENTVALIDATION'],
        '__RequestVerificationToken': os.getenv('INGENICO_COOKIE_REQUEST_VERIFICATION', ''),
        'ctl00$ContentPlaceHolder1$cboAssignedTo': filters.get('assigned_to', '5516'),
        'ctl00$ContentPlaceHolder1$cboJobType': filters.get('job_type', 'ALL'),
        'ctl00$ContentPlaceHolder1$txtFromDate': filters.get('from_date', '01/10/25'),
        'ctl00$ContentPlaceHolder1$txtToDate': filters.get('to_date', '31/10/25'),
        'ctl00$ContentPlaceHolder1$cboPageSize': filters.get('page_size', '100'),
        'ctl00$ContentPlaceHolder1$txtJobIDs': '',
        'ctl00$ContentPlaceHolder1$btnSearch': ' GO '
    }

    try:
        # allow_redirects=False para capturar el 302
        response = session.post(search_url, headers=headers, data=data,
                               timeout=30, allow_redirects=False)

        # Validar que sea un 302 redirect
        if response.status_code == 302:
            redirect_location = response.headers.get('Location', '')
            logger.info(f"✓ POST exitoso - Redirect 302 a: {redirect_location}")

            if 'FSPClosedJobList.aspx' in redirect_location:
                return True
            else:
                logger.warning(f"Redirect inesperado: {redirect_location}")
                raise SearchFailedError(f"Redirect a ubicación inesperada: {redirect_location}")
        else:
            logger.error(f"POST no retornó 302. Status: {response.status_code}")
            logger.debug(f"Response: {response.text[:500]}")
            raise SearchFailedError(f"POST retornó {response.status_code} en lugar de 302")

    except requests.RequestException as e:
        logger.error(f"Error en POST de búsqueda: {e}")
        raise IngenicoError(f"Error al enviar búsqueda: {e}")


def get_job_list(session):
    """
    Hace GET a FSPClosedJobList.aspx usando la misma sesión.

    Args:
        session: requests.Session con cookies y estado del POST

    Returns:
        str: HTML crudo de la página con la tabla de trabajos

    Raises:
        IngenicoError: Si falla la petición
    """
    logger.info("Obteniendo listado de trabajos cerrados...")

    list_url = os.getenv('INGENICO_LIST_URL')

    headers = {
        'User-Agent': os.getenv('INGENICO_USER_AGENT', ''),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': os.getenv('INGENICO_ACCEPT_LANGUAGE', ''),
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': os.getenv('INGENICO_SEARCH_URL'),
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = session.get(list_url, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info(f"✓ Listado obtenido - {len(response.text)} bytes")
        return response.text

    except requests.RequestException as e:
        logger.error(f"Error al obtener listado: {e}")
        raise IngenicoError(f"Error al obtener listado de trabajos: {e}")


def parse_html_table(html_content):
    """
    Parsea la tabla HTML del listado de trabajos cerrados.

    Args:
        html_content: str con el HTML crudo de la página

    Returns:
        list[dict]: Lista de trabajos con todos los campos de la tabla

    Raises:
        SessionExpiredError: Si no se encuentra la tabla (posible sesión expirada)
    """
    logger.info("Parseando tabla HTML...")

    soup = BeautifulSoup(html_content, 'html.parser')

    # Buscar tabla por ID
    table = soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_grdJob'})

    if not table:
        logger.error("Tabla no encontrada - posible sesión expirada")
        raise SessionExpiredError("No se encontró la tabla de trabajos. La sesión puede haber expirado.")

    # Extraer headers dinámicamente
    header_row = table.find('tr', {'class': 'FormGridHeaderCell'})
    if not header_row:
        logger.error("No se encontró fila de headers")
        raise IngenicoError("Estructura de tabla inválida - no se encontraron headers")

    headers = []
    for th in header_row.find_all('td'):
        header_text = th.get_text(strip=True)
        headers.append(header_text)

    logger.info(f"  Headers encontrados: {headers}")

    # Extraer filas de datos
    jobs = []
    row_count = 0

    for row in table.find_all('tr'):
        # Saltar headers y paginación
        row_classes = row.get('class', [])
        if 'FormGridHeaderCell' in row_classes or 'FormGridPagerCell' in row_classes:
            continue

        cells = row.find_all('td')
        if len(cells) == 0:
            continue

        # Validar que tenga al menos la mayoría de columnas (última es checkbox, puede variar)
        if len(cells) < len(headers) - 1:
            continue

        job_data = {}

        for i, cell in enumerate(cells):
            if i >= len(headers):
                break

            header_name = headers[i]

            # Extraer texto o link
            link = cell.find('a')
            if link and header_name == 'JobID':
                job_data[header_name] = link.get_text(strip=True)
            elif header_name == 'Bulk':
                # Skip checkbox column
                continue
            else:
                value = cell.get_text(strip=True)
                # Convertir &nbsp; a string vacío
                job_data[header_name] = value if value and value != '\xa0' else ''

        if job_data:  # Solo agregar si tiene datos
            jobs.append(job_data)
            row_count += 1

    logger.info(f"✓ {row_count} trabajos parseados exitosamente")

    return jobs


def save_results(jobs_data, filters, timestamp):
    """
    Guarda resultados en carpeta timestamped con HTML raw + JSON parseado.

    Args:
        jobs_data: tuple de (html_raw, jobs_list)
        filters: dict con filtros usados en la búsqueda
        timestamp: str con timestamp de la ejecución

    Returns:
        dict: Información de los archivos guardados
    """
    html_raw, jobs_list = jobs_data

    logger.info("Guardando resultados...")

    # Crear carpeta base
    base_folder = Path('closedJobIngenico')
    base_folder.mkdir(exist_ok=True)

    # Crear carpeta timestamped
    folder_name = f"{timestamp}_{filters['from_date'].replace('/', '-')}to{filters['to_date'].replace('/', '-')}"
    output_folder = base_folder / folder_name
    output_folder.mkdir(exist_ok=True)

    # Construir nombre de archivos
    date_range = f"{filters['from_date'].replace('/', '-')}_{filters['to_date'].replace('/', '-')}"
    file_base = f"closed_jobs_{date_range}_{timestamp}"

    # Guardar HTML raw
    html_file = output_folder / f"{file_base}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_raw)
    logger.info(f"  ✓ HTML guardado: {html_file}")

    # Guardar JSON con metadata
    json_data = {
        'metadata': {
            'fetch_timestamp': timestamp,
            'filters': filters,
            'total_jobs': len(jobs_list)
        },
        'jobs': jobs_list
    }

    json_file = output_folder / f"{file_base}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    logger.info(f"  ✓ JSON guardado: {json_file}")

    return {
        'success': True,
        'folder': str(output_folder),
        'html_file': str(html_file),
        'json_file': str(json_file),
        'total_jobs': len(jobs_list)
    }


def search_closed_jobs(filters=None, max_retries=1):
    """
    Función principal que orquesta el flujo completo de búsqueda.

    Args:
        filters: dict opcional con filtros. Si None, usa valores de .env
        max_retries: int número máximo de reintentos en caso de error

    Returns:
        dict: Resultado de la operación con información de archivos guardados

    Raises:
        SessionExpiredError: Si la sesión está expirada después de reintentos
        IngenicoError: Para otros errores
    """
    # Construir filtros desde parámetros o .env
    if filters is None:
        filters = {
            'from_date': os.getenv('INGENICO_FROM_DATE', '01/10/25'),
            'to_date': os.getenv('INGENICO_TO_DATE', '31/10/25'),
            'assigned_to': os.getenv('INGENICO_ASSIGNED_TO', '5516'),
            'job_type': os.getenv('INGENICO_JOB_TYPE', 'ALL'),
            'page_size': os.getenv('INGENICO_PAGE_SIZE', '100')
        }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    logger.info("="*70)
    logger.info("INICIANDO BÚSQUEDA DE CLOSED JOBS - INGENICO")
    logger.info("="*70)
    logger.info(f"Filtros: {filters}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("")

    for attempt in range(max_retries + 1):
        try:
            # Paso 1: Obtener formulario y tokens
            tokens, session = get_form_page()

            # Paso 2: Enviar búsqueda
            post_search(session, tokens, filters)

            # Paso 3: Obtener listado
            html_raw = get_job_list(session)

            # Paso 4: Parsear tabla
            jobs_list = parse_html_table(html_raw)

            # Paso 5: Guardar resultados
            result = save_results((html_raw, jobs_list), filters, timestamp)

            logger.info("")
            logger.info("="*70)
            logger.info(f"✓ BÚSQUEDA COMPLETADA EXITOSAMENTE")
            logger.info(f"  Total de trabajos: {result['total_jobs']}")
            logger.info(f"  Carpeta: {result['folder']}")
            logger.info("="*70)

            return result

        except SessionExpiredError as e:
            logger.error(f"Sesión expirada en intento {attempt + 1}")
            if attempt < max_retries:
                logger.info(f"Reintentando... ({attempt + 1}/{max_retries})")
                continue
            else:
                # No más reintentos - notificar al usuario
                return {
                    'success': False,
                    'error': 'SESSION_EXPIRED',
                    'message': '⚠️ Sesión expirada. Por favor actualiza las credenciales de Ingenico desde un cURL reciente.'
                }

        except Exception as e:
            logger.error(f"Error en intento {attempt + 1}: {e}")
            if attempt < max_retries:
                logger.info(f"Reintentando... ({attempt + 1}/{max_retries})")
                continue
            else:
                return {
                    'success': False,
                    'error': 'UNKNOWN_ERROR',
                    'message': f'Error al procesar búsqueda: {str(e)}'
                }


def main():
    """Función principal para testing desde CLI"""
    import sys

    # Verificar que existan credenciales básicas
    if not os.getenv('INGENICO_COOKIE_SESSION_ID'):
        print("❌ Error: No se encontraron credenciales de Ingenico en .env")
        print("   Ejecuta update_credentials.py primero para configurar las credenciales")
        sys.exit(1)

    print("\nBUSCANDO CLOSED JOBS EN INGENICO...")
    print("-" * 70)

    result = search_closed_jobs()

    if result['success']:
        print(f"\n✅ ÉXITO!")
        print(f"   Trabajos encontrados: {result['total_jobs']}")
        print(f"   Archivos guardados en: {result['folder']}")
    else:
        print(f"\n❌ ERROR: {result['message']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
