#!/usr/bin/env python3
"""
Flask Web Application for Verifone Invoice Management
Provides a web interface to manage credentials, parse requests, and generate invoices automatically
"""

import os
import sys
import json
import re
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv, set_key
from datetime import datetime
import threading

# Add directories to path for imports
current_dir = str(Path(__file__).parent)  # app/ directory
parent_dir = str(Path(__file__).parent.parent)  # project root
scripts_dir = str(Path(__file__).parent.parent / 'scripts')  # scripts/ directory

sys.path.insert(0, current_dir)  # For generate_invoice.py
sys.path.insert(0, parent_dir)   # For project root
sys.path.insert(0, scripts_dir)  # For scripts

# Import existing modules
from generate_invoice import main as generate_invoice_main
from update_credentials import update_credentials, update_ingenico_credentials
from fetch_ingenico_closed_jobs import search_closed_jobs
from urllib.parse import unquote

# Load environment variables from parent directory
load_dotenv(Path(__file__).parent.parent / '.env')

# Flask app with template and static folders in parent directory
app = Flask(__name__,
            template_folder=str(Path(__file__).parent.parent / 'templates'),
            static_folder=str(Path(__file__).parent.parent / 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS to allow Chrome extension to make requests
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global variable to track invoice generation status
generation_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': '',
    'result_file': None,
    'errors': []
}


@app.route('/')
def index():
    """Redirect to credentials page as default"""
    return redirect(url_for('credentials_page'))


@app.route('/dashboard')
def dashboard():
    """Optional dashboard page (if needed)"""
    return render_template('index.html')


@app.route('/credentials')
def credentials_page():
    """Page to manage credentials"""
    # Load current credentials from .env
    env_path = Path(__file__).parent.parent / '.env'
    credentials = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key] = value

    return render_template('credentials.html', credentials=credentials)


@app.route('/api/parse-request', methods=['POST'])
def parse_request():
    """
    Parse a browser request (either CURL or plain text from browser DevTools)
    and convert it to credentials format
    """
    data = request.json
    request_text = data.get('request_text', '').strip()
    credential_type = data.get('credential_type', 'HEADER')  # HEADER, FIRST, or PII

    if not request_text:
        return jsonify({'error': 'No request text provided'}), 400

    try:
        # Detect if it's a CURL command or plain text from browser
        if request_text.startswith('curl'):
            # It's already a CURL command
            curl_command = request_text
        else:
            # It's plain text from browser DevTools - convert to CURL
            curl_command = convert_browser_request_to_curl(request_text)
            if not curl_command:
                return jsonify({'error': 'Could not parse the request. Please provide either a complete CURL command or copy all request details from browser DevTools'}), 400

        # Extract credentials from CURL
        result = extract_credentials_from_curl(curl_command, credential_type)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('message', 'Failed to extract credentials')}), 400

    except Exception as e:
        return jsonify({'error': f'Error parsing request: {str(e)}'}), 500


@app.route('/api/update-credentials', methods=['POST'])
def update_credentials_endpoint():
    """Update credentials in .env file"""
    data = request.json
    credentials = data.get('credentials', {})

    if not credentials:
        return jsonify({'error': 'No credentials provided'}), 400

    try:
        env_path = Path(__file__).parent.parent / '.env'

        # Leer el contenido actual del .env
        with open(env_path, 'r') as f:
            env_lines = f.readlines()

        # Debug: Log all credentials being updated
        print(f"[DEBUG] ===== UPDATING CREDENTIALS =====")
        print(f"[DEBUG] Number of credentials: {len(credentials)}")
        for key in credentials.keys():
            if 'TOKEN' in key:
                print(f"[DEBUG] Token credential: {key} = {credentials[key][:100]}...")
            else:
                print(f"[DEBUG] Credential: {key} (length: {len(str(credentials[key]))})")

        # Flag to track if we need to write the file manually
        has_cookie_string = False

        # Actualizar cada credencial
        for key, value in credentials.items():
            if key == 'HEADER_COOKIE_STRING':
                print(f"[DEBUG] Saving HEADER_COOKIE_STRING (length: {len(value)})")
                print(f"[DEBUG] First 200 chars: {value[:200]}")

                has_cookie_string = True

                # Para HEADER_COOKIE_STRING, usar comillas simples para envolver el valor
                # porque el contenido tiene comillas dobles internas
                # Si el valor tiene comillas simples, escaparlas
                escaped_value = value.replace("'", "\\'")

                # Buscar la línea que contiene HEADER_COOKIE_STRING y actualizarla
                found = False
                for i, line in enumerate(env_lines):
                    if line.startswith('HEADER_COOKIE_STRING='):
                        # Usar comillas simples para envolver el valor
                        env_lines[i] = f"HEADER_COOKIE_STRING='{escaped_value}'\n"
                        found = True
                        break

                # Si no se encontró, agregarla al final
                if not found:
                    env_lines.append(f"HEADER_COOKIE_STRING='{escaped_value}'\n")
            else:
                # Para otras credenciales (incluyendo AURA_TOKEN_*), actualizar en env_lines
                print(f"[DEBUG] Saving {key} (length: {len(str(value))})")

                # Buscar la línea que contiene esta variable y actualizarla
                found = False
                for i, line in enumerate(env_lines):
                    if line.startswith(f'{key}='):
                        # Actualizar la línea con el nuevo valor
                        env_lines[i] = f"{key}='{value}'\n"
                        found = True
                        print(f"[DEBUG] Updated {key} in .env file (line {i+1})")
                        break

                # Si no se encontró, agregarla al final
                if not found:
                    env_lines.append(f"{key}='{value}'\n")
                    print(f"[DEBUG] Added {key} to .env file (new line)")

        # SIEMPRE escribir el archivo después de hacer cambios
        print(f"[DEBUG] Writing .env file with {len(credentials)} updated credentials...")
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        print(f"[DEBUG] ✅ .env file written successfully")

        # Reload environment variables
        load_dotenv(override=True)

        # Verificar que HEADER_COOKIE_STRING se guardó correctamente
        if 'HEADER_COOKIE_STRING' in credentials:
            saved_value = os.getenv('HEADER_COOKIE_STRING', '')
            print(f"[DEBUG] Verified HEADER_COOKIE_STRING after save (length: {len(saved_value)})")
            print(f"[DEBUG] First 200 chars: {saved_value[:200]}")

        # Verificar que los tokens se guardaron correctamente
        for key in credentials.keys():
            if 'TOKEN' in key:
                saved_value = os.getenv(key, '')
                print(f"[DEBUG] ===== VERIFIED {key} AFTER SAVE =====")
                print(f"[DEBUG] Length: {len(saved_value)}")
                print(f"[DEBUG] First 100 chars: {saved_value[:100]}")
                print(f"[DEBUG] Last 50 chars: ...{saved_value[-50:]}")
                if saved_value != credentials[key]:
                    print(f"[WARNING] ❌ {key} MISMATCH!")
                    print(f"[WARNING] Expected: {credentials[key][:100]}...")
                    print(f"[WARNING] Got: {saved_value[:100]}...")
                else:
                    print(f"[DEBUG] ✅ {key} matches!")

        return jsonify({'success': True, 'message': f'Updated {len(credentials)} credentials successfully'})
    except Exception as e:
        return jsonify({'error': f'Error updating credentials: {str(e)}'}), 500


@app.route('/api/generate-invoice', methods=['POST'])
def generate_invoice():
    """Trigger invoice generation with optional filters"""
    global generation_status

    if generation_status['running']:
        return jsonify({'error': 'Invoice generation is already running'}), 400

    # Get filter parameters from request
    data = request.json or {}
    filters = {
        'date_from': data.get('date_from'),
        'date_to': data.get('date_to'),
        'search_string': data.get('search_string', ''),
        'record_limit': data.get('record_limit', 200)
    }

    # Reset status
    generation_status = {
        'running': True,
        'progress': 0,
        'total': 0,
        'message': 'Starting invoice generation...',
        'result_file': None,
        'errors': [],
        'filters': filters
    }

    # Run generation in a separate thread with filters
    thread = threading.Thread(target=run_invoice_generation, args=(filters,))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Invoice generation started'})


@app.route('/api/generation-status')
def generation_status_endpoint():
    """Get current status of invoice generation"""
    return jsonify(generation_status)


@app.route('/viewer')
def viewer():
    """Invoice viewer page"""
    return render_template('viewer.html')


@app.route('/api/get-latest-invoice')
def get_latest_invoice():
    """Get the path to the latest generated invoice"""
    verifone_folder = Path(__file__).parent.parent / 'VerifoneWorkOrders'

    if not verifone_folder.exists():
        return jsonify({'error': 'No invoices found'}), 404

    # Find the latest folder
    invoice_folders = sorted(verifone_folder.glob('invoice_*'), reverse=True)

    if not invoice_folders:
        return jsonify({'error': 'No invoices found'}), 404

    # Find the HTML file in the latest folder
    latest_folder = invoice_folders[0]
    html_files = list(latest_folder.glob('*.html'))

    if not html_files:
        return jsonify({'error': 'No HTML file found in latest invoice folder'}), 404

    return jsonify({
        'success': True,
        'folder': str(latest_folder),
        'file': str(html_files[0])
    })


def convert_browser_request_to_curl(request_text):
    """
    Convert plain text from browser DevTools to CURL command
    Expected format: the text contains headers like "cookie:", "content-type:", etc.
    and form data if applicable
    """
    try:
        lines = request_text.split('\n')

        # Extract key components
        url = None
        method = 'POST'
        headers = {}
        form_data = {}

        # Parse line by line
        in_form_data = False
        in_query_params = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Check for URL
            if line.lower().startswith('request url'):
                url = line.split(None, 2)[-1] if len(line.split(None, 2)) > 2 else None

            # Check for method
            elif line.lower().startswith('request method'):
                method = line.split(None, 2)[-1] if len(line.split(None, 2)) > 2 else 'POST'

            # Check for form data section
            elif line.lower() == 'form data':
                in_form_data = True
                in_query_params = False
                continue

            # Check for query string parameters section
            elif line.lower() == 'query string parameters':
                in_query_params = True
                in_form_data = False
                continue

            # Parse form data
            elif in_form_data and line:
                if '\n' in line or not ':' in line:
                    # Skip complex lines
                    continue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    form_data[key] = value

            # Parse headers (anything with ':' that's not in form data)
            elif ':' in line and not in_form_data and not in_query_params:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    headers[key.lower()] = value

        if not url:
            return None

        # Build CURL command
        curl_parts = [f"curl '{url}'"]
        curl_parts.append(f"-X {method}")

        # Add headers
        for key, value in headers.items():
            curl_parts.append(f"-H '{key}: {value}'")

        # Add form data
        if form_data:
            for key, value in form_data.items():
                curl_parts.append(f"--data-urlencode '{key}={value}'")

        return ' \\\n  '.join(curl_parts)

    except Exception as e:
        print(f"Error converting browser request to CURL: {e}")
        return None


def extract_credentials_from_curl(curl_command, credential_type):
    """Extract credentials from a CURL command"""
    try:
        # Extract cookies - guardar el string completo tal como viene
        cookie_match = re.search(r"-H ['\"]Cookie: ([^'\"]+)['\"]", curl_command)
        if not cookie_match:
            return {'success': False, 'message': 'No cookies found in CURL command'}

        cookie_string = cookie_match.group(1)

        # Debug: Print cookie string
        print(f"[DEBUG] Cookie string extracted (length: {len(cookie_string)})")
        print(f"[DEBUG] Cookie string: {cookie_string[:200]}...")

        # Extract token - intenta primero con --data-urlencode, luego con --data-raw
        token_match = re.search(r'--data-urlencode\s+[\'"]aura\.token=([^\'\"]+)[\'"]', curl_command)
        if not token_match:
            # Si no encuentra con --data-urlencode, intenta con --data-raw
            token_match = re.search(r'--data-raw\s+[\'"]aura\.token=([^\'\"]+)[\'"]', curl_command)

        if not token_match:
            return {'success': False, 'message': 'No aura.token found in CURL command'}

        aura_token = token_match.group(1).strip()

        # Debug: Print token
        print(f"[DEBUG] aura.token extracted (length: {len(aura_token)})")
        print(f"[DEBUG] aura.token (first 100 chars): {aura_token[:100]}")
        print(f"[DEBUG] aura.token (last 50 chars): {aura_token[-50:]}")

        # Initialize credentials with the complete cookie string
        credentials = {
            'HEADER_COOKIE_STRING': cookie_string
        }

        # Determine which token to update
        if credential_type == 'HEADER':
            token_var = 'AURA_TOKEN_HEADER'
        elif credential_type == 'FIRST':
            token_var = 'AURA_TOKEN'
        elif credential_type == 'PII':
            token_var = 'AURA_TOKEN_PII'
        else:
            return {'success': False, 'message': f'Invalid credential type: {credential_type}'}

        credentials[token_var] = aura_token

        # Debug: Log which token variable is being updated
        print(f"[DEBUG] Credential type: {credential_type}")
        print(f"[DEBUG] Token variable being updated: {token_var}")
        print(f"[DEBUG] Token value being saved: {aura_token[:100]}...")
        print(f"[DEBUG] Token value (last 50 chars): ...{aura_token[-50:]}")

        # Si es tipo HEADER, extraer el sid real de las cookies (NO usar aura token)
        # El sid de las cookies es diferente al aura.token
        if credential_type == 'HEADER':
            # El sid ya fue extraído del cookie string en el paso anterior
            # No hacemos nada aquí, se usa el valor de las cookies directamente
            pass

            # Extraer X-SFDC headers si están presentes
            x_sfdc_page_scope_match = re.search(r"-H ['\"]X-SFDC-Page-Scope-Id:\s*([^'\"]+)['\"]", curl_command)
            if x_sfdc_page_scope_match:
                credentials['X_SFDC_PAGE_SCOPE_ID_HEADER'] = x_sfdc_page_scope_match.group(1).strip()

            x_sfdc_request_id_match = re.search(r"-H ['\"]X-SFDC-Request-Id:\s*([^'\"]+)['\"]", curl_command)
            if x_sfdc_request_id_match:
                credentials['X_SFDC_REQUEST_ID_HEADER'] = x_sfdc_request_id_match.group(1).strip()

            # Extraer el filterId del Referer
            referer_match = re.search(r"-H ['\"]Referer:\s*([^'\"]+)['\"]", curl_command)
            if referer_match:
                referer_url = referer_match.group(1).strip()
                # Extraer filterId de la URL del Referer
                filter_id_match = re.search(r'WorkOrder-filterId=([^&\s]+)', referer_url)
                if filter_id_match:
                    filter_id = filter_id_match.group(1)
                    credentials['HEADER_FILTER_ID'] = filter_id
                    # También construir AURA_PAGE_URI_HEADER dinámicamente
                    credentials['AURA_PAGE_URI_HEADER'] = f'/verifonefs/s/recordlist/WorkOrder/Default?WorkOrder-filterId={filter_id}'
                # Guardar el Referer completo también
                credentials['REFERER_HEADER'] = referer_url

        # Si es tipo HEADER, extraer también los parámetros del mensaje
        if credential_type == 'HEADER':
            # Extraer el mensaje JSON del cURL
            message_match = re.search(r'message=([^&\s\'\"]+)', curl_command)
            if message_match:
                try:
                    # Decodificar URL y parsear JSON
                    message_json_str = unquote(message_match.group(1))
                    message_data = json.loads(message_json_str)

                    # Buscar parámetros en las actions
                    actions = message_data.get('actions', [])
                    for action in actions:
                        params = action.get('params', {})

                        # Extraer entityName/entityKeyPrefixOrApiName
                        if 'entityName' in params:
                            credentials['HEADER_ENTITY_NAME'] = params['entityName']
                        elif 'listReference' in params:
                            list_ref = params['listReference']
                            if 'entityKeyPrefixOrApiName' in list_ref:
                                credentials['HEADER_ENTITY_NAME'] = list_ref['entityKeyPrefixOrApiName']
                            if 'listViewIdOrName' in list_ref:
                                credentials['HEADER_LIST_VIEW_ID'] = list_ref['listViewIdOrName']

                        # Extraer filterName
                        if 'filterName' in params:
                            credentials['FILTER_NAME'] = params['filterName']

                        # Extraer layoutType
                        if 'layoutType' in params:
                            credentials['HEADER_LAYOUT_TYPE'] = params['layoutType']

                        # Extraer layoutMode
                        if 'layoutMode' in params:
                            credentials['HEADER_LAYOUT_MODE'] = params['layoutMode']

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"[WARNING] No se pudieron extraer parámetros del mensaje: {e}")

        return {
            'success': True,
            'credentials': credentials,
            'token_type': token_var,
            'cookies_found': len([k for k in credentials.keys() if k.startswith('COOKIE_')]),
            'message': f'Extracted {len(credentials)} credentials successfully'
        }

    except Exception as e:
        return {'success': False, 'message': f'Error extracting credentials: {str(e)}'}


def run_invoice_generation(filters=None):
    """Run invoice generation in background with optional filters"""
    global generation_status

    def progress_callback(message, progress, total, errors):
        """Callback function to update progress"""
        generation_status['message'] = message
        generation_status['progress'] = progress
        generation_status['total'] = total
        generation_status['errors'] = errors[:10]  # Keep only last 10 errors

    try:
        generation_status['message'] = 'Generating invoice...'

        # Run the main function from generate_invoice.py with callback and filters
        result_file = generate_invoice_main(progress_callback=progress_callback, filters=filters)

        # Find the generated file if not returned
        if not result_file:
            verifone_folder = Path(__file__).parent.parent / 'VerifoneWorkOrders'
            invoice_folders = sorted(verifone_folder.glob('invoice_*'), reverse=True)

            if invoice_folders:
                latest_folder = invoice_folders[0]
                html_files = list(latest_folder.glob('*.html'))
                if html_files:
                    result_file = str(html_files[0])

        if result_file:
            generation_status['result_file'] = str(result_file)

        generation_status['running'] = False
        generation_status['message'] = 'Invoice generated successfully!'

    except Exception as e:
        generation_status['running'] = False
        generation_status['message'] = f'Error generating invoice: {str(e)}'
        generation_status['errors'].append(f'Fatal error: {str(e)}')


def generate_curl_command():
    """Generate cURL command for the HEADER request"""
    import os
    from generate_invoice import build_cookie_string

    url = os.getenv('API_URL_HEADER')
    origin = os.getenv('ORIGIN_URL')
    referer = os.getenv('REFERER_HEADER')

    # Build message payload with 3 actions (matching exact working request)
    entity_name = os.getenv('HEADER_ENTITY_NAME', 'WorkOrder')
    list_view_id = os.getenv('HEADER_LIST_VIEW_ID', 'Technician_Work_Order_List_View')
    filter_name = os.getenv('FILTER_NAME', 'Technician_Work_Order_List_View')
    layout_type = os.getenv('HEADER_LAYOUT_TYPE', 'LIST')
    layout_mode = os.getenv('HEADER_LAYOUT_MODE', 'EDIT')
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
                    "offset": 0
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

    import urllib.parse

    curl_parts = [
        f"curl '{url}' \\",
        "  -X POST \\",
        f"  -H 'Accept: application/json' \\",
        f"  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \\",
        f"  -H 'Origin: {origin}' \\",
        f"  -H 'Referer: {referer}' \\",
        f"  -H 'User-Agent: {os.getenv('USER_AGENT')}' \\",
        f"  -H 'X-SFDC-Page-Scope-Id: {os.getenv('X_SFDC_PAGE_SCOPE_ID_HEADER', '')}' \\",
        f"  -H 'X-SFDC-Request-Id: {os.getenv('X_SFDC_REQUEST_ID_HEADER', '')}' \\",
        f"  -H 'Cookie: {build_cookie_string()}' \\",
        f"  --data-raw 'message={json.dumps(message)}' \\",
        f"  --data-urlencode 'aura.context={json.dumps(aura_context)}' \\",
        f"  --data-urlencode 'aura.pageURI={os.getenv('AURA_PAGE_URI_HEADER')}' \\",
        f"  --data-urlencode 'aura.token={os.getenv('AURA_TOKEN_HEADER')}'"
    ]

    return '\n'.join(curl_parts)


@app.route('/api/test-header', methods=['POST'])
def test_header():
    """Test header request to Verifone to get work order IDs"""
    try:
        from generate_invoice import fetch_all_work_order_ids
        import requests

        print("\n[TEST HEADER] Iniciando test de petición HEADER...")

        # Generar cURL command
        curl_command = generate_curl_command()

        # Hacer la petición (modificamos para obtener también la respuesta raw)
        work_order_ids, raw_response = fetch_all_work_order_ids()

        # Validar que la petición fue exitosa
        # Si context.globalValueProviders[2].values existe, la petición fue exitosa
        request_successful = False
        total_records = 0
        if raw_response:
            try:
                context = raw_response.get('context', {})
                global_value_providers = context.get('globalValueProviders', [])

                # Verificar si existe el tercer elemento (índice 2) y tiene 'values'
                if len(global_value_providers) >= 3:
                    third_provider = global_value_providers[2]
                    if 'values' in third_provider:
                        request_successful = True
                        # Contar registros en context.globalValueProviders[2].values.records
                        records = third_provider.get('values', {}).get('records', {})
                        total_records = len(records) if isinstance(records, dict) else 0
                        print(f"[TEST HEADER] ✓ Petición exitosa: {total_records} registros encontrados")
            except (KeyError, IndexError, AttributeError, TypeError) as e:
                print(f"[TEST HEADER] ⚠️  Error validando estructura: {e}")

        # Si la petición no fue exitosa, retornar error
        if not request_successful:
            print("[TEST HEADER] ✗ Petición fallida: no existe context.globalValueProviders[2].values")
            return jsonify({
                'success': False,
                'error': 'Request failed: context.globalValueProviders[2].values not found',
                'message': '✗ Request structure invalid - check credentials',
                'raw_response': raw_response,
                'curl_command': curl_command
            }), 400

        if work_order_ids:
            print(f"[TEST HEADER] ✓ {len(work_order_ids)} work orders encontrados")

            # Construir respuesta con detalles
            return jsonify({
                'success': True,
                'total_work_orders': total_records,  # Usar el conteo de records
                'work_order_ids': work_order_ids,  # Todos los IDs
                'message': f'✓ Header test successful! Found {total_records} work orders',
                'full_response': work_order_ids,  # Solo IDs, no toda la respuesta raw
                'raw_response': raw_response,  # Respuesta completa para debugging
                'curl_command': curl_command  # cURL usado
            })
        else:
            print(f"[TEST HEADER] ⚠️ Petición exitosa pero sin work_order_ids (total_records: {total_records})")
            return jsonify({
                'success': True,
                'total_work_orders': total_records,  # Incluir el total de records
                'work_order_ids': [],
                'message': f'Response received. Found {total_records} records but no work_order_ids extracted',
                'raw_response': raw_response,
                'curl_command': curl_command
            })

    except Exception as e:
        error_msg = str(e)
        print(f"[TEST HEADER] ✗ Error: {error_msg}")

        # Try to generate curl even on error
        try:
            curl_command = generate_curl_command()
        except:
            curl_command = "Error: Could not generate cURL command"

        return jsonify({
            'success': False,
            'error': error_msg,
            'message': f'✗ Error: {error_msg}',
            'curl_command': curl_command
        }), 500


# ============================================
# INGENICO ENDPOINTS
# ============================================

@app.route('/ingenico')
def ingenico_page():
    """Página principal de Ingenico para buscar Closed Jobs"""
    return render_template('ingenico.html')


@app.route('/api/ingenico/get-filters')
def get_ingenico_filters():
    """Obtiene los filtros actuales desde .env para prellenar el formulario"""
    try:
        filters = {
            'assigned_to': os.getenv('INGENICO_ASSIGNED_TO', '5516'),
            'job_type': os.getenv('INGENICO_JOB_TYPE', 'ALL'),
            'from_date': os.getenv('INGENICO_FROM_DATE', '01/10/25'),
            'to_date': os.getenv('INGENICO_TO_DATE', '31/10/25'),
            'page_size': os.getenv('INGENICO_PAGE_SIZE', '100')
        }
        return jsonify({'success': True, 'filters': filters})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ingenico/search-closed-jobs', methods=['POST'])
def search_ingenico_closed_jobs():
    """
    Busca Closed Jobs en Ingenico con los filtros especificados.

    Request body:
    {
        "from_date": "01/10/25",
        "to_date": "31/10/25",
        "assigned_to": "5516",
        "job_type": "ALL",
        "page_size": "100"
    }

    Returns:
    {
        "success": true,
        "folder": "closedJobIngenico/20251102_220530_01-10-25to31-10-25/",
        "html_file": "...",
        "json_file": "...",
        "total_jobs": 35
    }
    """
    try:
        data = request.json
        filters = {
            'from_date': data.get('from_date', os.getenv('INGENICO_FROM_DATE', '01/10/25')),
            'to_date': data.get('to_date', os.getenv('INGENICO_TO_DATE', '31/10/25')),
            'assigned_to': data.get('assigned_to', os.getenv('INGENICO_ASSIGNED_TO', '5516')),
            'job_type': data.get('job_type', os.getenv('INGENICO_JOB_TYPE', 'ALL')),
            'page_size': data.get('page_size', os.getenv('INGENICO_PAGE_SIZE', '100'))
        }

        print(f"\n[INGENICO] Iniciando búsqueda con filtros: {filters}")

        # Llamar a la función de búsqueda
        result = search_closed_jobs(filters)

        if result['success']:
            print(f"[INGENICO] ✓ Búsqueda exitosa - {result['total_jobs']} trabajos encontrados")
            return jsonify(result)
        else:
            print(f"[INGENICO] ✗ Error: {result.get('message', 'Unknown error')}")
            return jsonify(result), 400

    except Exception as e:
        error_msg = f'Error al buscar Closed Jobs: {str(e)}'
        print(f"[INGENICO] ✗ Excepción: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/ingenico/update-credentials', methods=['POST'])
def update_ingenico_credentials_endpoint():
    """
    Actualiza las credenciales de Ingenico desde un comando cURL.

    Request body:
    {
        "curl_command": "curl 'https://services.ingenico.com.au/...' ..."
    }

    Returns:
    {
        "success": true,
        "message": "Credenciales actualizadas exitosamente"
    }
    """
    try:
        data = request.json
        curl_command = data.get('curl_command', '').strip()

        if not curl_command:
            return jsonify({'success': False, 'error': 'No se proporcionó comando cURL'}), 400

        if not curl_command.startswith('curl'):
            return jsonify({'success': False, 'error': 'El comando no parece ser un cURL válido'}), 400

        print(f"\n[INGENICO] Actualizando credenciales desde cURL...")

        # Llamar a la función de actualización
        success = update_ingenico_credentials(curl_command)

        if success:
            # Recargar variables de entorno
            load_dotenv(override=True)

            print(f"[INGENICO] ✓ Credenciales actualizadas exitosamente")
            return jsonify({
                'success': True,
                'message': 'Credenciales de Ingenico actualizadas exitosamente'
            })
        else:
            print(f"[INGENICO] ✗ Error al actualizar credenciales")
            return jsonify({
                'success': False,
                'error': 'No se pudieron actualizar las credenciales. Verifica el comando cURL.'
            }), 400

    except Exception as e:
        error_msg = f'Error al actualizar credenciales: {str(e)}'
        print(f"[INGENICO] ✗ Excepción: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/ingenico/list-downloads')
def list_ingenico_downloads():
    """
    Lista todas las descargas previas de Closed Jobs de Ingenico.

    Returns:
    {
        "success": true,
        "downloads": [
            {
                "folder": "20251102_220530_01-10-25to31-10-25",
                "timestamp": "2025-11-02 22:05:30",
                "date_range": "01/10/25 - 31/10/25",
                "total_jobs": 35,
                "json_file": "...",
                "html_file": "..."
            },
            ...
        ]
    }
    """
    try:
        base_folder = Path(__file__).parent.parent / 'closedJobIngenico'

        if not base_folder.exists():
            return jsonify({'success': True, 'downloads': []})

        downloads = []

        # Iterar carpetas ordenadas por fecha (más reciente primero)
        for folder in sorted(base_folder.glob('*'), reverse=True):
            if not folder.is_dir():
                continue

            # Buscar archivos JSON
            json_files = list(folder.glob('*.json'))
            if not json_files:
                continue

            json_file = json_files[0]

            # Leer metadata del JSON
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})

                    downloads.append({
                        'folder': folder.name,
                        'timestamp': metadata.get('fetch_timestamp', ''),
                        'date_range': f"{metadata.get('filters', {}).get('from_date', '')} - {metadata.get('filters', {}).get('to_date', '')}",
                        'total_jobs': metadata.get('total_jobs', 0),
                        'json_file': str(json_file),
                        'html_file': str(json_file).replace('.json', '.html')
                    })
            except Exception as e:
                print(f"Error leyendo {json_file}: {e}")
                continue

        return jsonify({'success': True, 'downloads': downloads})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
    """Serve favicon from static folder"""
    return send_file(Path(__file__).parent.parent / 'static' / 'favicon.ico', mimetype='image/x-icon')


if __name__ == '__main__':
    # Create templates folder if it doesn't exist
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)

    print("="*70)
    print("   INVOICE MANAGEMENT SYSTEM - Web Application")
    print("="*70)
    print()
    print("Starting Flask server...")
    print()
    print("Access the application at: http://localhost:8080")
    print()
    print("Features:")
    print("  • Verifone: Manage credentials, generate invoices")
    print("  • Ingenico: Search and download Closed Jobs")
    print("  • Parse browser requests automatically")
    print("  • View generated reports")
    print()
    print("="*70)
    print()

    app.run(debug=True, host='0.0.0.0', port=8080)
