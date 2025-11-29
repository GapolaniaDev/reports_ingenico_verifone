#!/usr/bin/env python3
"""
Script para generar facturas desde datos de work orders.
Hace peticiones al servidor para obtener detalles de cada trabajo y genera un HTML con los resultados.
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Cargar variables de entorno desde .env
load_dotenv()


def fetch_all_work_order_ids(search_string='', page_size=None):
    """
    Hace una petición al servidor para obtener todos los IDs de work orders.
    Los IDs se encuentran en: context.globalValueProviders[1].values.records

    Args:
        search_string: Texto para filtrar por nombre de cliente, merchant, etc.
        page_size: Número de registros a obtener (default: desde .env o 50)
    """
    url = os.getenv('API_URL_HEADER')
    origin = os.getenv('ORIGIN_URL')
    referer = os.getenv('REFERER_HEADER')

    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': origin,
        'Referer': referer,
        'User-Agent': os.getenv('USER_AGENT'),
        'X-SFDC-Page-Scope-Id': os.getenv('X_SFDC_PAGE_SCOPE_ID_HEADER', ''),
        'X-SFDC-Request-Id': os.getenv('X_SFDC_REQUEST_ID_HEADER', ''),
        'Cookie': build_cookie_string()
    }

    # Construir el mensaje con 3 actions (matching exact working request)
    entity_name = os.getenv('HEADER_ENTITY_NAME', 'WorkOrder')
    list_view_id = os.getenv('HEADER_LIST_VIEW_ID', 'Technician_Work_Order_List_View')
    filter_name = os.getenv('FILTER_NAME', 'Technician_Work_Order_List_View')
    layout_type = os.getenv('HEADER_LAYOUT_TYPE', 'LIST')
    layout_mode = os.getenv('HEADER_LAYOUT_MODE', 'EDIT')

    # Use provided page_size or default from env
    if page_size is None:
        page_size = int(os.getenv('HEADER_PAGE_SIZE', '50'))

    in_context_of_component = os.getenv('HEADER_IN_CONTEXT_OF_COMPONENT', 'force:listViewManagerGrid')

    message = {
        "actions": [
            {
                "id": "6975;a",
                "descriptor": "serviceComponent://ui.force.components.controllers.lists.listViewManagerGrid.ListViewManagerGridController/ACTION$getRecordLayoutComponent",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "listReference": {
                        "entityKeyPrefixOrApiName": entity_name,
                        "listViewIdOrName": list_view_id,
                        "inContextOfRecordId": None,
                        "isMRU": False,
                        "isSearch": False
                    },
                    "layoutType": layout_type,
                    "layoutMode": layout_mode,
                    "inContextOfComponent": in_context_of_component,
                    "enableMassActions": True,
                    "enableRowErrors": True,
                    "useHoversForLookup": False
                }
            },
            {
                "id": "6976;a",
                "descriptor": "serviceComponent://ui.force.components.controllers.lists.listViewDataManager.ListViewDataManagerController/ACTION$getItems",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "filterName": filter_name,
                    "entityName": entity_name,
                    "pageSize": page_size,
                    "layoutType": layout_type,
                    "sortBy": None,
                    "getCount": False,
                    "enableRowActions": False,
                    "offset": 0,
                    "searchString": search_string if search_string else None
                },
                "storable": True
            },
            {
                "id": "6977;a",
                "descriptor": "serviceComponent://ui.force.components.controllers.lists.listViewManager.ListViewManagerController/ACTION$getMetadataInitialLoad",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "listReference": {
                        "entityKeyPrefixOrApiName": entity_name,
                        "listViewIdOrName": list_view_id,
                        "inContextOfRecordId": None,
                        "isMRU": False,
                        "isSearch": False
                    }
                }
            }
        ]
    }

    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID_HEADER'),
        "app": os.getenv('AURA_APP_HEADER'),
        "loaded": json.loads(os.getenv('AURA_LOADED_HEADER', '{}')),
        "dn": [],
        "globals": {},
        "uad": True
    }

    # Construir el cuerpo de la petición
    data = {
        'message': json.dumps(message),
        'aura.context': json.dumps(aura_context),
        'aura.pageURI': os.getenv('AURA_PAGE_URI_HEADER'),
        'aura.token': os.getenv('AURA_TOKEN_HEADER')
    }

    try:
        print("   Haciendo petición Header para obtener IDs...")
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            try:
                json_response = response.json()

                # Extraer IDs de: context.globalValueProviders[2].values.records
                context = json_response.get('context', {})
                global_value_providers = context.get('globalValueProviders', [])

                if len(global_value_providers) >= 3:
                    # Los records están en el índice 2 (tercer elemento)
                    records = global_value_providers[2].get('values', {}).get('records', {})
                    # Las claves del diccionario 'records' son los IDs
                    work_order_ids = list(records.keys())
                    print(f"   ✓ {len(work_order_ids)} IDs obtenidos desde Header (context.globalValueProviders[2].values.records)")
                    return work_order_ids, json_response
                else:
                    print(f"   ✗ Error: estructura de respuesta inesperada (globalValueProviders tiene {len(global_value_providers)} elementos, se esperaban al menos 3)")
                    return [], json_response
            except json.JSONDecodeError as e:
                print(f"   ✗ Error al decodificar JSON: {e}")
                return [], None
        else:
            print(f"   ✗ Error HTTP {response.status_code}")
            return [], None
    except Exception as e:
        print(f"   ✗ Error en petición Header: {e}")
        return [], None


def load_work_order_ids(filename='allWO.json'):
    """Carga los IDs de work orders desde el archivo JSON (método legacy)."""
    with open(filename, 'r') as f:
        # El archivo es una lista de IDs como strings
        content = f.read()
        # Limpiar el contenido y extraer solo los IDs válidos
        ids = []
        for line in content.split('\n'):
            line = line.strip().strip(',').strip('"').strip("'").strip('{').strip('}')
            if line and line.startswith('0WO'):
                ids.append(line)
        return ids


def build_cookie_string():
    """Retorna el string de cookies completo desde las variables de entorno.
    Ahora simplemente devuelve HEADER_COOKIE_STRING tal como fue guardado."""
    cookie_string = os.getenv('HEADER_COOKIE_STRING', '')

    if not cookie_string:
        print("[WARNING] HEADER_COOKIE_STRING is empty, using fallback individual cookies")
        # Fallback al método anterior si HEADER_COOKIE_STRING no existe
        cookies = [
            f"renderCtx={os.getenv('COOKIE_RENDER_CTX')}",
            f"CookieConsentPolicy={os.getenv('COOKIE_CONSENT_POLICY')}",
            f"LSKey-c$CookieConsentPolicy={os.getenv('COOKIE_CONSENT_POLICY')}",
            f"BrowserId={os.getenv('COOKIE_BROWSER_ID')}",
            f"autocomplete={os.getenv('COOKIE_AUTOCOMPLETE')}",
            f"oid={os.getenv('COOKIE_OID')}",
            f"ssostartpage={os.getenv('COOKIE_SSO_START_PAGE')}",
            f"sid_Client={os.getenv('COOKIE_SID_CLIENT')}",
            f"inst={os.getenv('COOKIE_INST')}",
            f"__Secure-has-sid={os.getenv('COOKIE_SECURE_HAS_SID')}",
            f"79eb100099b9a8bf={os.getenv('COOKIE_79EB')}",
            f"oinfo={os.getenv('COOKIE_OINFO')}",
            f"saml_request_id={os.getenv('COOKIE_SAML_REQUEST_ID')}",
            f"sid={os.getenv('COOKIE_SID')}",
            f"clientSrc={os.getenv('COOKIE_CLIENT_SRC')}"
        ]
        return "; ".join(cookies)

    return cookie_string


def fetch_work_order_detail(work_order_id):
    """Hace una petición al servidor para obtener los detalles de un work order."""

    url = os.getenv('API_URL')
    origin = os.getenv('ORIGIN_URL')
    referer_base = os.getenv('REFERER_BASE_URL')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Origin': origin,
        'Referer': f'{referer_base}{work_order_id}',
        'Accept-Language': os.getenv('ACCEPT_LANGUAGE'),
        'User-Agent': os.getenv('USER_AGENT'),
        'Cookie': build_cookie_string()
    }

    # Construir el mensaje con el ID específico
    message = {
        "actions": [{
            "id": "199;a",
            "descriptor": "serviceComponent://ui.force.components.controllers.recordGlobalValueProvider.RecordGvpController/ACTION$getRecord",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "recordDescriptor": f"{work_order_id}.undefined.FULL.null.null.null.VIEW.true.null.null.null"
            }
        }]
    }

    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID'),
        "app": "siteforce:communityApp",
        "loaded": {
            "APPLICATION@markup://siteforce:communityApp": os.getenv('AURA_APP_VERSION')
        },
        "dn": [],
        "globals": {},
        "uad": True
    }

    # Construir el cuerpo de la petición
    data = {
        'message': json.dumps(message),
        'aura.context': json.dumps(aura_context),
        'aura.pageURI': f'{os.getenv("AURA_PAGE_URI_BASE")}{work_order_id}',
        'aura.token': os.getenv('AURA_TOKEN')
    }

    try:
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                # Silenciar errores en modo paralelo, se reportarán en process_single_work_order
                return None
        else:
            return None
    except Exception as e:
        # Silenciar excepciones en modo paralelo
        return None


def fetch_work_order_pii_details(work_order_id):
    """Hace una segunda petición al servidor para obtener los detalles PII de un work order."""

    url = os.getenv('API_URL_PII')
    origin = os.getenv('ORIGIN_URL')

    # Generar nonce único para esta petición
    import hashlib
    import time
    nonce = hashlib.sha256(f"{work_order_id}{time.time()}".encode()).hexdigest()

    # Construir pageURI completo con todos los parámetros
    page_uri = f"/verifonefs/VF_DisplayPIIDetailsWorkOrderPage?id={work_order_id}&tour=&isdtp=p1&sfdcIFrameOrigin={origin}&sfdcIFrameHost=web&nonce={nonce}&ltn_app_id=&clc=0"
    referer = f"{origin}{page_uri}"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Origin': origin,
        'Referer': referer,
        'Accept-Language': os.getenv('ACCEPT_LANGUAGE'),
        'User-Agent': os.getenv('USER_AGENT'),
        'Cookie': build_cookie_string()
    }

    # Construir el mensaje con el ID específico para la petición PII
    message = {
        "actions": [{
            "id": "69;a",
            "descriptor": "aura://FlowRuntimeConnectController/ACTION$startFlow",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "flowDevName": os.getenv('FLOW_DEV_NAME'),
                "arguments": f'[{{"name":"recordId","type":"String","value":"{work_order_id}"}}]',
                "enableTrace": False,
                "enableRollbackMode": False,
                "debugAsUserId": "",
                "useLatestSubflow": False,
                "isBuilderDebug": False
            }
        }]
    }

    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID_PII'),
        "app": os.getenv('AURA_APP_PII'),
        "loaded": {
            f"APPLICATION@markup://{os.getenv('AURA_APP_PII')}": os.getenv('AURA_APP_VERSION_PII')
        },
        "dn": [],
        "globals": {},
        "uad": True
    }

    # Construir el cuerpo de la petición
    data = {
        'message': json.dumps(message),
        'aura.context': json.dumps(aura_context),
        'aura.pageURI': page_uri,
        'aura.token': os.getenv('AURA_TOKEN_PII')
    }

    try:
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Error decodificando JSON en PII para {work_order_id}: {e}")
                return None
        else:
            print(f"   ⚠️  Error en petición PII para {work_order_id}: Status {response.status_code}")
            print(f"       Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ⚠️  Excepción en petición PII para {work_order_id}: {e}")
        return None


def calculate_after_hour(onsite_datetime_str):
    """
    Calcula si el trabajo fue fuera de horario (after hours).
    After hour = entre 6pm y 6am
    """
    if not onsite_datetime_str or onsite_datetime_str == 'N/A':
        return 'N/A'

    try:
        from datetime import datetime
        # El formato es: "26/08/2025 3:46 PM"
        dt = datetime.strptime(onsite_datetime_str, '%d/%m/%Y %I:%M %p')
        hour = dt.hour

        # After hours: >= 18:00 (6pm) o < 6:00 (6am)
        if hour >= 18 or hour < 6:
            return 'YES'
        else:
            return 'NO'
    except:
        return 'N/A'


def calculate_weekend(onsite_datetime_str):
    """
    Calcula si el trabajo fue en fin de semana.
    Weekend = Sábado (5) o Domingo (6)
    """
    if not onsite_datetime_str or onsite_datetime_str == 'N/A':
        return 'N/A'

    try:
        from datetime import datetime
        # El formato es: "26/08/2025 3:46 PM"
        dt = datetime.strptime(onsite_datetime_str, '%d/%m/%Y %I:%M %p')
        weekday = dt.weekday()  # 0=Monday, 6=Sunday

        # Weekend: Sábado (5) o Domingo (6)
        if weekday >= 5:
            return 'YES'
        else:
            return 'NO'
    except:
        return 'N/A'


def parse_pii_details(pii_response, work_order_id=''):
    """Extrae la información PII de la segunda petición."""
    if not pii_response:
        print(f"   ⚠️  No hay respuesta PII para {work_order_id}")
        return {
            'terminal_id': '',
            'merchant_name': '',
            'suburb': '',
            'postcode': '',
            'street': ''
        }

    try:
        # Navegar por la estructura: actions[0].returnValue.response.outputVariables
        actions = pii_response.get('actions', [])
        if not actions:
            print(f"   ⚠️  No hay 'actions' en respuesta PII para {work_order_id}")
            return {
                'terminal_id': '',
                'merchant_name': '',
                'suburb': '',
                'postcode': '',
                'street': ''
            }

        return_value = actions[0].get('returnValue', {})
        response = return_value.get('response', {})
        output_variables = response.get('outputVariables', [])

        # Debug: mostrar cuántas variables se encontraron
        if not output_variables:
            print(f"   ⚠️  No hay 'outputVariables' en respuesta PII para {work_order_id}")

        # Extraer los datos según el mapeo especificado
        terminal_id = ''
        suburb = ''
        postcode = ''
        merchant_name = ''  # Por ahora vacío según especificación
        street = ''

        # outputVariables[0] contiene terminal_id_c__c y street__c
        if len(output_variables) > 0:
            var_0_value = output_variables[0].get('value', {})
            terminal_id = var_0_value.get('terminal_id_c__c', '')
            street = var_0_value.get('street__c', '')

        # outputVariables[1] contiene City y PostalCode
        if len(output_variables) > 1:
            var_1_value = output_variables[1].get('value', {})
            suburb = var_1_value.get('City', '')
            postcode = var_1_value.get('PostalCode', '')

        # Debug: mostrar lo que se extrajo
        extracted_count = sum([1 for x in [terminal_id, street, suburb, postcode] if x])
        if extracted_count == 0:
            print(f"   ⚠️  No se extrajeron datos PII para {work_order_id} (outputVariables: {len(output_variables)})")

        return {
            'terminal_id': terminal_id if terminal_id else '',
            'merchant_name': merchant_name,
            'suburb': suburb if suburb else '',
            'postcode': postcode if postcode else '',
            'street': street if street else ''
        }

    except Exception as e:
        print(f"   ⚠️  Error parseando PII para {work_order_id}: {e}")
        return {
            'terminal_id': '',
            'merchant_name': '',
            'suburb': '',
            'postcode': '',
            'street': ''
        }


def parse_work_order_data(api_response, work_order_id):
    """Extrae la información relevante de la respuesta de la API."""
    if not api_response:
        return None

    try:
        # Verificar si hay errores de acceso
        context = api_response.get('context', {})
        global_value_providers = context.get('globalValueProviders', [])

        for provider in global_value_providers:
            if provider.get('type') == '$Record':
                record_errors = provider.get('values', {}).get('recordErrors', {})
                if work_order_id in record_errors:
                    # Error de acceso - será reportado por process_single_work_order
                    return None

                # Buscar el record en records
                records = provider.get('values', {}).get('records', {})
                if work_order_id in records:
                    record_data = records[work_order_id]
                    # Navegar a WorkOrder -> record -> fields
                    work_order = record_data.get('WorkOrder', {})
                    record = work_order.get('record', {})
                    fields = record.get('fields', {})

                    # Extraer los campos según el mapeo especificado
                    job_id = extract_field_value(fields, 'WorkOrderNumber')
                    fsp = ''  # Vacío por ahora
                    client_id = extract_field_display_value(fields, 'Bank_Brand__r')
                    job_type = extract_field_display_value(fields, 'Work_Order_Type__c')
                    # terminal_id, suburb, postcode y merchant_name se obtendrán de la segunda petición
                    terminal_id = ''
                    required_by = ''  # Vacío por ahora
                    merchant_name = ''
                    suburb = ''
                    postcode = ''
                    area = extract_field_display_value(fields, 'Zone__c')
                    onsite_datetime = extract_field_display_value(fields, 'On_Site_Start_Time__c')

                    # Extract On_Site_End_Time__c value (ISO format) for date filtering
                    onsite_end_time_iso = extract_field_value(fields, 'On_Site_End_Time__c')

                    # Extract On_Site_Start_Time__c value (ISO format) as fallback for "On Site" jobs
                    onsite_start_time_iso = extract_field_value(fields, 'On_Site_Start_Time__c')

                    device_type = extract_field_display_value(fields, 'WorkType')
                    project_no = ''  # Vacío por ahora
                    billable = ''  # Vacío por ahora
                    fix = extract_field_display_value(fields, 'Status')  # Status del work order
                    sla_met = ''  # Vacío por ahora
                    multiple_job_id = ''  # Vacío por ahora
                    extra_time = ''  # Vacío por ahora

                    # Si ClientID está vacío, es "N/A", o es "NONE", usar las 3 primeras letras de DeviceType
                    # Esto ocurre comúnmente con el banco CBA
                    if (not client_id or client_id == 'N/A' or client_id.upper() == 'NONE') and device_type and device_type != 'N/A':
                        client_id = device_type[:3].upper()

                    # Calcular After Hour y Weekend basados en OnSiteDateTime
                    after_hour = calculate_after_hour(onsite_datetime)
                    weekend = calculate_weekend(onsite_datetime)

                    extratime_block = ''  # Vacío por ahora
                    charge = ''  # Vacío por ahora

                    # Detectar si el trabajo está en estado "On Site"
                    is_onsite = (fix == 'On Site')

                    result = {
                        'job_id': job_id,
                        'fsp': fsp,
                        'client_id': client_id,
                        'job_type': job_type,
                        'terminal_id': terminal_id,
                        'required_by': required_by,
                        'merchant_name': merchant_name,
                        'suburb': suburb,
                        'postcode': postcode,
                        'area': area,
                        'onsite_datetime': onsite_datetime,
                        'onsite_end_time_iso': onsite_end_time_iso,  # ISO format for filtering
                        'onsite_start_time_iso': onsite_start_time_iso,  # Fallback for "On Site" jobs
                        'device_type': device_type,
                        'project_no': project_no,
                        'billable': billable,
                        'fix': fix,
                        'is_onsite': is_onsite,  # Flag para identificar trabajos onsite
                        'sla_met': sla_met,
                        'multiple_job_id': multiple_job_id,
                        'extra_time': extra_time,
                        'after_hour': after_hour,
                        'weekend': weekend,
                        'extratime_block': extratime_block,
                        'charge': charge,
                        'street': ''  # Se llenará con la segunda petición
                    }
                    return result

        # No se encontraron datos en la estructura esperada
        return None

    except Exception as e:
        # Error al parsear - será reportado por process_single_work_order
        return None


def extract_field_value(fields, field_name):
    """Extrae el valor de un campo de la estructura de la API."""
    if field_name in fields:
        field = fields[field_name]
        if isinstance(field, dict) and 'value' in field:
            return field['value']
        return field
    return 'N/A'


def extract_field_display_value(fields, field_name):
    """Extrae el displayValue de un campo de la estructura de la API."""
    if field_name in fields:
        field = fields[field_name]
        if isinstance(field, dict) and 'displayValue' in field:
            display_value = field['displayValue']
            # Si displayValue es None, intentar obtener el value
            if display_value is None and 'value' in field:
                value = field['value']
                # Si value es un dict con Name, extraerlo
                if isinstance(value, dict) and 'fields' in value:
                    name_field = value['fields'].get('Name', {})
                    if isinstance(name_field, dict) and 'value' in name_field:
                        return name_field['value']
                return value
            return display_value if display_value is not None else 'N/A'
        return field
    return 'N/A'


def process_single_work_order(wo_id, output_folder, index, total):
    """
    Procesa un único work order: hace dos peticiones, guarda las respuestas y parsea los datos.
    Esta función se ejecutará en paralelo para múltiples work orders.
    """
    try:
        # Hacer la primera petición
        api_response = fetch_work_order_detail(wo_id)

        # Guardar la respuesta raw para debug
        if api_response:
            debug_file = output_folder / f'raw_response_{wo_id}.json'
            with open(debug_file, 'w') as f:
                json.dump(api_response, f, indent=2)

        # Parsear los datos de la primera petición
        parsed_data = parse_work_order_data(api_response, wo_id)

        # Si la primera petición fue exitosa, hacer la segunda petición
        if parsed_data:
            pii_response = fetch_work_order_pii_details(wo_id)

            # Guardar la respuesta PII raw para debug
            if pii_response:
                pii_debug_file = output_folder / f'raw_pii_response_{wo_id}.json'
                with open(pii_debug_file, 'w') as f:
                    json.dump(pii_response, f, indent=2)

            # Parsear los datos PII de la segunda petición
            pii_data = parse_pii_details(pii_response, wo_id)

            # Combinar los datos de ambas peticiones
            parsed_data['terminal_id'] = pii_data['terminal_id']
            parsed_data['merchant_name'] = pii_data['merchant_name']
            parsed_data['suburb'] = pii_data['suburb']
            parsed_data['postcode'] = pii_data['postcode']
            parsed_data['street'] = pii_data['street']

        # Retornar resultado con información de progreso
        return {
            'index': index,
            'total': total,
            'wo_id': wo_id,
            'data': parsed_data,
            'success': parsed_data is not None
        }
    except Exception as e:
        print(f"   ⚠️  Error procesando {wo_id}: {e}")
        return {
            'index': index,
            'total': total,
            'wo_id': wo_id,
            'data': None,
            'success': False,
            'error': str(e)
        }


def normalize_address(address):
    """Normaliza una dirección para comparación."""
    if not address or address == 'N/A':
        return ''
    # Convertir a minúsculas, trim, y reemplazar espacios múltiples por uno solo
    normalized = address.strip().lower()
    import re
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def normalize_date_to_day(onsite_datetime):
    """Extrae solo el día (YYYY-MM-DD) de un OnSiteDateTime."""
    if not onsite_datetime or onsite_datetime == 'N/A':
        return ''
    try:
        # El formato es: "26/08/2025 3:46 PM"
        dt = datetime.strptime(onsite_datetime, '%d/%m/%Y %I:%M %p')
        return dt.strftime('%Y-%m-%d')
    except:
        return ''


def calculate_multiple_job_ids(work_orders_data):
    """
    Calcula el MultipleJobID para cada trabajo.

    Busca trabajos que compartan:
    - Misma fecha (día, mes, año - ignorando hora)
    - Misma dirección (street__c normalizada)

    El trabajo con el menor JobID (principal) tendrá MultipleJobID vacío.
    Los demás trabajos del grupo tendrán el JobID del principal.
    """
    # Crear un índice por (fecha_normalizada, dirección_normalizada) -> lista de trabajos
    location_index = {}

    for wo in work_orders_data:
        if not wo:
            continue

        date_key = normalize_date_to_day(wo.get('onsite_datetime', ''))
        addr_key = normalize_address(wo.get('street', ''))

        # Solo indexar si tenemos fecha y dirección válidas
        if date_key and addr_key:
            key = (date_key, addr_key)
            if key not in location_index:
                location_index[key] = []
            location_index[key].append(wo)

    # Ahora para cada grupo de trabajos, determinar el principal (menor JobID)
    for key, matching_jobs in location_index.items():
        # Si solo hay un trabajo en este grupo, no hay múltiples
        if len(matching_jobs) <= 1:
            for wo in matching_jobs:
                wo['multiple_job_id'] = ''
            continue

        # Ordenar por JobID para encontrar el menor (principal)
        sorted_jobs = sorted(matching_jobs, key=lambda x: x.get('job_id', ''))
        principal_job = sorted_jobs[0]
        principal_job_id = principal_job.get('job_id', '')

        # Asignar MultipleJobID
        for wo in matching_jobs:
            if wo.get('job_id') == principal_job_id:
                # El trabajo principal tiene MultipleJobID vacío
                wo['multiple_job_id'] = ''
            else:
                # Los demás trabajos tienen el JobID del principal
                wo['multiple_job_id'] = principal_job_id

    # Para trabajos sin grupo válido (sin fecha o dirección), dejar vacío
    for wo in work_orders_data:
        if not wo:
            continue

        date_key = normalize_date_to_day(wo.get('onsite_datetime', ''))
        addr_key = normalize_address(wo.get('street', ''))

        # Si no tiene fecha o dirección válidas, asegurarse de que esté vacío
        if not date_key or not addr_key:
            wo['multiple_job_id'] = ''

    return work_orders_data


def filter_by_date_range(work_orders_data, date_from, date_to):
    """
    Filtra work orders por rango de fechas usando On_Site_End_Time__c.value (ISO format).

    Args:
        work_orders_data: Lista de work orders con campo 'onsite_end_time_iso'
        date_from: Fecha inicial en formato YYYY-MM-DD
        date_to: Fecha final en formato YYYY-MM-DD

    Returns:
        Lista filtrada de work orders dentro del rango de fechas
    """
    if not date_from or not date_to:
        # Si no hay filtro de fecha, retornar todos
        return work_orders_data

    try:
        # Convertir las fechas a datetime (solo fecha, sin hora)
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date()

        filtered_orders = []

        for wo in work_orders_data:
            if not wo:
                continue

            # Obtener el valor ISO de On_Site_End_Time__c (trabajos completados)
            onsite_end_iso = wo.get('onsite_end_time_iso')
            # Obtener el valor ISO de On_Site_Start_Time__c (fallback para trabajos "On Site")
            onsite_start_iso = wo.get('onsite_start_time_iso')

            # Usar onsite_end_time si existe, si no, usar onsite_start_time
            date_iso_to_use = onsite_end_iso if (onsite_end_iso and onsite_end_iso != 'N/A') else onsite_start_iso

            if not date_iso_to_use or date_iso_to_use == 'N/A':
                # Si no hay ninguna fecha disponible, excluir el work order
                print(f"   ⚠️  Sin fecha para filtrar: {wo.get('job_id', 'N/A')}")
                continue

            try:
                # Parsear el ISO string: "2025-11-29T02:11:18.000Z"
                # Extraer solo la parte de fecha
                wo_date = datetime.fromisoformat(date_iso_to_use.replace('Z', '+00:00')).date()

                # Verificar si está dentro del rango (inclusivo)
                if from_date <= wo_date <= to_date:
                    filtered_orders.append(wo)
                    # Log para debug de trabajos "On Site"
                    if wo.get('is_onsite'):
                        print(f"   ✓ Incluido trabajo On Site: {wo.get('job_id', 'N/A')} - Fecha: {wo_date}")

            except (ValueError, AttributeError) as e:
                # Si hay error al parsear la fecha, excluir el work order
                print(f"   ⚠️  Error parseando fecha para {wo.get('job_id', 'N/A')}: {e}")
                continue

        print(f"\n   Filtrado por fecha aplicado:")
        print(f"   - Rango: {date_from} a {date_to}")
        print(f"   - Work orders antes del filtro: {len(work_orders_data)}")
        print(f"   - Work orders después del filtro: {len(filtered_orders)}")

        return filtered_orders

    except ValueError as e:
        print(f"   ⚠️  Error en formato de fechas: {e}")
        return work_orders_data


def get_jobtype_class(job_type):
    """Determina la clase CSS según el tipo de trabajo."""
    if not job_type or job_type == 'N/A':
        return 'jobtype-other'

    job_type_lower = job_type.lower()

    if 'recovery' in job_type_lower or 'deinstall' in job_type_lower:
        return 'jobtype-recovery'
    elif 'install' in job_type_lower and 'deinstall' not in job_type_lower:
        return 'jobtype-install'
    elif 'swap' in job_type_lower:
        return 'jobtype-swap'
    else:
        return 'jobtype-other'


def generate_html(work_orders_data, output_folder):
    """Genera un archivo HTML con la información de los work orders."""

    # Ordenar los work orders por fecha (OnSiteDateTime) de más reciente a más antiguo
    def parse_date(wo):
        """Parsea la fecha del formato 'DD/MM/YYYY HH:MM AM/PM' para ordenamiento."""
        onsite_dt = wo.get('onsite_datetime', '')
        if not onsite_dt or onsite_dt == 'N/A':
            # Si no hay fecha, poner al final
            return datetime.min
        try:
            # El formato es: "26/08/2025 3:46 PM"
            return datetime.strptime(onsite_dt, '%d/%m/%Y %I:%M %p')
        except:
            # Si no se puede parsear, poner al final
            return datetime.min

    # Ordenar: reverse=True para tener las fechas más recientes primero
    work_orders_data_sorted = sorted(work_orders_data, key=parse_date, reverse=True)

    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')[:-3]  # Incluye milisegundos (3 dígitos)
    filename = f"invoice_{timestamp}.html"
    filepath = output_folder / filename

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Work Orders Invoice - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-completed {{
            color: green;
            font-weight: bold;
        }}
        .status-failed {{
            color: red;
            font-weight: bold;
        }}
        .status-onsite {{
            background: #ffe5b4 !important;
            border-left: 4px solid #ff9800;
        }}
        .status-onsite:hover {{
            background: #ffd699 !important;
        }}
        /* Estilos para JobType */
        .jobtype-recovery, .jobtype-deinstall {{
            background-color: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        .jobtype-install {{
            background-color: #27ae60;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        .jobtype-swap {{
            background-color: #f39c12;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        .jobtype-other {{
            background-color: #95a5a6;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Work Orders Invoice</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Work Orders: {len(work_orders_data)}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>JobID</th>
                <th>FSP</th>
                <th>ClientID</th>
                <th>JobType</th>
                <th>TerminalID</th>
                <th>RequiredBy</th>
                <th>MerchantName</th>
                <th>Suburb</th>
                <th>Postcode</th>
                <th>Area</th>
                <th>OnSiteDateTime</th>
                <th>DeviceType</th>
                <th>ProjectNo</th>
                <th>Billable</th>
                <th>Fix</th>
                <th>SLAMet</th>
                <th>MultipleJobID</th>
                <th>ExtraTime</th>
                <th>AfterHour</th>
                <th>Weekend</th>
                <th>Extratime (Block)</th>
                <th>Charge</th>
            </tr>
        </thead>
        <tbody>
"""

    for wo in work_orders_data_sorted:
        if wo:  # Solo incluir si hay datos
            job_type = wo.get('job_type', 'N/A')
            job_type_class = get_jobtype_class(job_type)

            # Agregar clase especial si el trabajo está en estado "On Site"
            row_class = 'status-onsite' if wo.get('is_onsite', False) else ''

            html_content += f"""
            <tr class="{row_class}">
                <td>{wo.get('job_id', 'N/A')}</td>
                <td>{wo.get('fsp', '')}</td>
                <td>{wo.get('client_id', 'N/A')}</td>
                <td><span class="{job_type_class}">{job_type}</span></td>
                <td>{wo.get('terminal_id', '')}</td>
                <td>{wo.get('required_by', '')}</td>
                <td>{wo.get('merchant_name', '')}</td>
                <td>{wo.get('suburb', '')}</td>
                <td>{wo.get('postcode', '')}</td>
                <td>{wo.get('area', 'N/A')}</td>
                <td>{wo.get('onsite_datetime', 'N/A')}</td>
                <td>{wo.get('device_type', 'N/A')}</td>
                <td>{wo.get('project_no', '')}</td>
                <td>{wo.get('billable', '')}</td>
                <td>{wo.get('fix', '')}</td>
                <td>{wo.get('sla_met', '')}</td>
                <td>{wo.get('multiple_job_id', '')}</td>
                <td>{wo.get('extra_time', '')}</td>
                <td>{wo.get('after_hour', 'N/A')}</td>
                <td>{wo.get('weekend', 'N/A')}</td>
                <td>{wo.get('extratime_block', '')}</td>
                <td>{wo.get('charge', '')}</td>
            </tr>
"""

    html_content += """
        </tbody>
    </table>

    <div class="footer">
        <p>This invoice was automatically generated</p>
    </div>
</body>
</html>
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nHTML generado exitosamente: {filepath}")
    return filepath


def main(progress_callback=None, filters=None):
    """Función principal del script con soporte para filtros opcionales."""
    print("Iniciando generación de invoice...")

    # Extract filters if provided
    if filters is None:
        filters = {}

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    search_string = filters.get('search_string', '')
    record_limit = filters.get('record_limit', 200)

    def update_progress(message, progress=0, total=0, errors=None):
        """Helper function to update progress"""
        if progress_callback:
            progress_callback(message, progress, total, errors or [])
        print(message)

    # Crear carpeta base para los resultados
    base_folder = Path(__file__).parent.parent / 'VerifoneWorkOrders'
    base_folder.mkdir(exist_ok=True)

    # Crear carpeta para esta ejecución con timestamp (incluye milisegundos)
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')[:-3]
    output_folder = base_folder / f'invoice_{timestamp}'
    output_folder.mkdir(exist_ok=True)

    # Obtener los IDs de work orders desde Header API
    update_progress("Obteniendo IDs de work orders desde Header API...", 0, 0)
    print("\n1. Obteniendo IDs de work orders desde Header API...")
    print(f"   Filtros aplicados:")
    print(f"   - Search String: '{search_string}'" if search_string else "   - Search String: (ninguno)")
    print(f"   - Record Limit: {record_limit}")
    if date_from and date_to:
        print(f"   - Date Range: {date_from} to {date_to}")
    work_order_ids, header_response = fetch_all_work_order_ids(search_string=search_string, page_size=record_limit)

    if not work_order_ids:
        print("\n✗ No se pudieron obtener IDs desde Header API")
        print("  Intentando cargar desde allWO.json como fallback...")
        try:
            work_order_ids = load_work_order_ids()
            print(f"   ✓ {len(work_order_ids)} IDs cargados desde allWO.json")
        except Exception as e:
            print(f"   ✗ Error cargando allWO.json: {e}")
            return
    else:
        # Guardar los IDs obtenidos en allWO.json
        try:
            with open('allWO.json', 'w') as f:
                json.dump(work_order_ids, f, indent=2)
            print(f"   ✓ {len(work_order_ids)} IDs guardados en allWO.json")
        except Exception as e:
            print(f"   ⚠️  Error guardando allWO.json: {e}")

    # Guardar la respuesta Header en un archivo para debug
    if header_response:
        header_file = output_folder / 'header.json'
        with open(header_file, 'w') as f:
            json.dump(header_response, f, indent=2)
        print(f"   Respuesta Header guardada en: {header_file}")

    print(f"   Total de IDs obtenidos: {len(work_order_ids)}")
    print(f"   Carpeta de salida: {output_folder}")

    # Limitar según configuración (0 = todos)
    max_work_orders = int(os.getenv('MAX_WORK_ORDERS', '5'))
    if max_work_orders > 0:
        limited_ids = work_order_ids[:max_work_orders]
        print(f"\n2. Limitando a los primeros {len(limited_ids)} work orders...")
    else:
        limited_ids = work_order_ids
        print(f"\n2. Procesando TODOS los work orders ({len(limited_ids)})...")

    # Hacer peticiones para cada work order EN PARALELO
    print("\n3. Haciendo peticiones al servidor en paralelo...")
    print(f"   Procesando {len(limited_ids)} work orders simultáneamente...")
    update_progress(f"Procesando {len(limited_ids)} work orders...", 0, len(limited_ids))

    start_time = time.time()
    work_orders_data = []
    successful = 0
    failed = 0
    error_list = []

    # Verificar que haya work orders para procesar
    if not limited_ids:
        print("\n✗ No hay work orders para procesar")
        update_progress("Error: No work orders found", len(limited_ids), len(limited_ids), ["No work orders found in header response"])
        return None

    # Configurar el número máximo de workers (threads)
    # Usar 10 threads para no sobrecargar el servidor
    max_workers = min(10, len(limited_ids))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas al executor
        future_to_wo = {
            executor.submit(process_single_work_order, wo_id, output_folder, i, len(limited_ids)): wo_id
            for i, wo_id in enumerate(limited_ids, 1)
        }

        # Procesar los resultados a medida que se completan
        for future in as_completed(future_to_wo):
            result = future.result()

            # Mostrar progreso
            progress = f"[{result['index']}/{result['total']}]"

            if result['success']:
                work_orders_data.append(result['data'])
                successful += 1
                print(f"   {progress} ✓ {result['wo_id']} - Procesado exitosamente")
                update_progress(
                    f"Procesando work order {successful + failed}/{len(limited_ids)}...",
                    successful + failed,
                    len(limited_ids),
                    error_list
                )
            else:
                failed += 1
                error_msg = result.get('error', 'Error desconocido')
                error_list.append(f"{result['wo_id']}: {error_msg}")
                print(f"   {progress} ✗ {result['wo_id']} - Falló: {error_msg}")
                update_progress(
                    f"Procesando work order {successful + failed}/{len(limited_ids)}...",
                    successful + failed,
                    len(limited_ids),
                    error_list
                )

    elapsed_time = time.time() - start_time
    print(f"\n   Tiempo total: {elapsed_time:.2f} segundos")
    print(f"   Exitosos: {successful} | Fallidos: {failed}")

    # Aplicar filtro por fecha si se especificó
    if date_from and date_to and work_orders_data:
        print("\n4. Aplicando filtro por fecha (On_Site_End_Time__c)...")
        update_progress("Filtrando por rango de fechas...", len(limited_ids), len(limited_ids), error_list)
        work_orders_data = filter_by_date_range(work_orders_data, date_from, date_to)

    # Calcular MultipleJobID para cada trabajo
    print("\n5. Calculando MultipleJobID (trabajos en misma fecha y dirección)...")
    update_progress("Calculando MultipleJobID...", len(limited_ids), len(limited_ids), error_list)
    if work_orders_data:
        work_orders_data = calculate_multiple_job_ids(work_orders_data)
        # Contar cuántos trabajos tienen MultipleJobID asignado
        multiple_jobs_count = sum(1 for wo in work_orders_data if wo.get('multiple_job_id', ''))
        print(f"   Trabajos con múltiples IDs encontrados: {multiple_jobs_count}")

    # Generar el HTML
    print("\n6. Generando archivo HTML...")
    update_progress("Generando archivo HTML...", len(limited_ids), len(limited_ids), error_list)
    if work_orders_data:
        html_file = generate_html(work_orders_data, output_folder)
        print(f"\n✓ Proceso completado exitosamente!")
        print(f"  Archivo HTML: {html_file}")
        print(f"  Total de work orders procesados: {len(work_orders_data)}")
        update_progress(
            f"Completado: {successful} exitosos, {failed} fallidos",
            len(limited_ids),
            len(limited_ids),
            error_list
        )
        return html_file
    else:
        print("\n✗ No se pudieron procesar work orders")
        print("  Revisa los archivos raw_response_*.json para debug")
        update_progress(
            "Error: No se pudieron procesar work orders",
            len(limited_ids),
            len(limited_ids),
            error_list
        )
        return None


if __name__ == '__main__':
    main()
