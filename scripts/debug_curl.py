#!/usr/bin/env python3
"""
Debug cURL Generator
Genera el comando cURL exacto que Python ejecuta para depuración
"""
import os
import json
import sys
from dotenv import load_dotenv
from urllib.parse import unquote

# Cargar variables de entorno
load_dotenv()


def build_cookie_string():
    """Construye el string de cookies."""
    cookies = [
        f"renderCtx={unquote(os.getenv('COOKIE_RENDER_CTX',''))}",
        f"CookieConsentPolicy={os.getenv('COOKIE_CONSENT_POLICY','')}",
        f"LSKey-c$CookieConsentPolicy={os.getenv('COOKIE_CONSENT_POLICY','')}",
        f"BrowserId={os.getenv('COOKIE_BROWSER_ID','')}",
        f"autocomplete={os.getenv('COOKIE_AUTOCOMPLETE','')}",
        f"sid_Client={os.getenv('COOKIE_SID_CLIENT','')}",
        f"inst={os.getenv('COOKIE_INST','')}",
        f"oid={os.getenv('COOKIE_OID','')}",
        f"__Secure-has-sid={os.getenv('COOKIE_SECURE_HAS_SID','')}",
        f"79eb100099b9a8bf={os.getenv('COOKIE_79EB','')}",
        f"ssostartpage={os.getenv('COOKIE_SSO_START_PAGE','')}",
        f"saml_request_id={os.getenv('COOKIE_SAML_REQUEST_ID','')}",
        f"oinfo={os.getenv('COOKIE_OINFO','')}",
        f"sid={os.getenv('COOKIE_SID','')}",
        f"clientSrc={os.getenv('COOKIE_CLIENT_SRC','')}"
    ]
    return "; ".join(cookies)


def debug_header_request():
    """Opción 1: Debug petición de cabecera (lista de Work Orders)"""
    print("\n" + "="*70)
    print("OPCIÓN 1: DEBUG PETICIÓN CABECERA (Header)")
    print("="*70)
    print()

    # Message para obtener lista de work orders
    message = {
        "actions": [{
            "id": "6975;a",
            "descriptor": "serviceComponent://ui.force.components.controllers.lists.listViewDataManager.ListViewDataManagerController/ACTION$getItems",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "filterName": os.getenv('FILTER_NAME', 'Technician_Work_Order_List_View'),
                "entityName": "WorkOrder",
                "pageSize": int(os.getenv('HEADER_PAGE_SIZE', 200)),
                "layoutType": "LIST",
                "sortBy": None,
                "getCount": False,
                "enableRowActions": False,
                "offset": 0
            },
            "storable": True
        }]
    }

    # Aura context para header
    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID_HEADER', os.getenv('AURA_FWUID', '')),
        "app": os.getenv('AURA_APP_HEADER', 'siteforce:communityApp'),
        "loaded": json.loads(os.getenv('AURA_LOADED_HEADER', '{}')),
        "dn": [],
        "globals": {},
        "uad": True
    }

    url = os.getenv('API_URL_HEADER', '')
    aura_token = os.getenv('AURA_TOKEN_HEADER', os.getenv('AURA_TOKEN', ''))
    page_uri = os.getenv('AURA_PAGE_URI_HEADER', '/verifonefs/s/recordlist/WorkOrder/Default?WorkOrder-filterId=Technician_Work_Order_List_View')
    referer = os.getenv('REFERER_HEADER', 'https://verifone123.my.site.com/verifonefs/s/recordlist/WorkOrder/Default?WorkOrder-filterId=Technician_Work_Order_List_View')

    print_curl(url, message, aura_context, page_uri, aura_token, referer)


def debug_first_request():
    """Opción 2: Debug primera petición (detalles de un Work Order específico)"""
    print("\n" + "="*70)
    print("OPCIÓN 2: DEBUG PRIMERA PETICIÓN (Detalles Work Order)")
    print("="*70)
    print()

    # Pedir el Work Order ID
    work_order_id = input("Ingresa el Work Order ID (ej: 0WOVy00000FdCofOAF): ").strip()
    if not work_order_id:
        print("❌ ID requerido")
        return

    print()

    # Message para obtener detalles del work order
    message = {
        "actions": [{
            "id": "69;a",
            "descriptor": "serviceComponent://ui.force.components.controllers.recordGlobalValueProvider.RecordGvpController/ACTION$getRecord",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "recordIds": [work_order_id],
                "fields": [
                    "WorkOrder.WorkOrderNumber",
                    "WorkOrder.Status",
                    "WorkOrder.Bank_Brand__r.Name",
                    "WorkOrder.Client__r.Name",
                    "WorkOrder.Work_Type__c",
                    "WorkOrder.Service_Appointment__r.EarliestStartTime",
                    "WorkOrder.Work_Order_External__c",
                    "WorkOrder.Device_Type__c",
                    "WorkOrder.GCL_Project_Number__c",
                    "WorkOrder.Service_Appointment__r.SchedStartTime"
                ],
                "optionalFields": []
            }
        }]
    }

    # Aura context para primera petición
    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID', ''),
        "app": os.getenv('AURA_APP_VERSION', 'siteforce:communityApp'),
        "loaded": {
            f"APPLICATION@markup://{os.getenv('AURA_APP_VERSION', 'siteforce:communityApp')}": os.getenv('AURA_APP_VERSION', '')
        },
        "dn": [],
        "globals": {},
        "uad": True
    }

    url = os.getenv('API_URL', '')
    aura_token = os.getenv('AURA_TOKEN', '')
    page_uri = f"{os.getenv('AURA_PAGE_URI_BASE', '/verifonefs/s/detail/')}{work_order_id}"
    referer = f"{os.getenv('REFERER_BASE_URL', 'https://verifone123.my.site.com/verifonefs/s/detail/')}{work_order_id}"

    print_curl(url, message, aura_context, page_uri, aura_token, referer)


def debug_pii_request():
    """Opción 3: Debug petición PII (información sensible del Work Order)"""
    print("\n" + "="*70)
    print("OPCIÓN 3: DEBUG PETICIÓN PII (Información Sensible)")
    print("="*70)
    print()

    # Pedir el Work Order ID
    work_order_id = input("Ingresa el Work Order ID (ej: 0WOVy00000FdCofOAF): ").strip()
    if not work_order_id:
        print("❌ ID requerido")
        return

    print()

    # Message para obtener información PII
    # IMPORTANTE: arguments debe ser un STRING JSON, no un objeto
    message = {
        "actions": [{
            "id": "69;a",
            "descriptor": "aura://FlowRuntimeConnectController/ACTION$startFlow",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "flowDevName": os.getenv('FLOW_DEV_NAME', 'PII_Display_Work_Order_Details_Screen'),
                "arguments": f'[{{"name":"recordId","type":"String","value":"{work_order_id}"}}]',
                "enableTrace": False,
                "enableRollbackMode": False,
                "debugAsUserId": "",
                "useLatestSubflow": False,
                "isBuilderDebug": False
            }
        }]
    }

    # Aura context para PII
    aura_context = {
        "mode": "PROD",
        "fwuid": os.getenv('AURA_FWUID_PII', 'VFJhRGxfRlFsN29ySGg2SXFsaUZsQTFLcUUxeUY3ZVB6dE9hR0VheDVpb2cxMy4zMzU1NDQzMi4yNTE2NTgyNA'),
        "app": os.getenv('AURA_APP_PII', 'c:vfDisplayPiiDetailsApp'),
        "loaded": {
            f"APPLICATION@markup://{os.getenv('AURA_APP_PII', 'c:vfDisplayPiiDetailsApp')}": os.getenv('AURA_APP_VERSION_PII', '782_88YMcANMrqse-dq9ixl0Ng')
        },
        "dn": [],
        "globals": {},
        "uad": True
    }

    url = os.getenv('API_URL_PII', 'https://verifone123.my.site.com/verifonefs/aura?r=2&aura.FlowRuntimeConnect.startFlow=1')
    aura_token = os.getenv('AURA_TOKEN_PII', '')

    # Formato completo del pageURI con todos los parámetros
    # Generar un nonce simple (en producción usa un hash real)
    import hashlib
    import time
    nonce = hashlib.sha256(f"{work_order_id}{time.time()}".encode()).hexdigest()

    origin_url = os.getenv('ORIGIN_URL', 'https://verifone123.my.site.com')
    page_uri = f"/verifonefs/VF_DisplayPIIDetailsWorkOrderPage?id={work_order_id}&tour=&isdtp=p1&sfdcIFrameOrigin={origin_url}&sfdcIFrameHost=web&nonce={nonce}&ltn_app_id=&clc=0"
    referer = f"{origin_url}{page_uri}"

    print_curl(url, message, aura_context, page_uri, aura_token, referer)


def print_curl(url, message, aura_context, page_uri, aura_token, referer):
    """Imprime el comando cURL formateado"""
    cookies = build_cookie_string()

    print(f"curl '{url}' \\")
    print("  -X POST \\")
    print("  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \\")
    print("  -H 'Accept: */*' \\")
    print(f"  -H 'Origin: {os.getenv('ORIGIN_URL', 'https://verifone123.my.site.com')}' \\")
    print(f"  -H 'Referer: {referer}' \\")
    print(f"  -H 'User-Agent: {os.getenv('USER_AGENT', 'Mozilla/5.0')}' \\")
    print(f"  -H 'Accept-Language: {os.getenv('ACCEPT_LANGUAGE', 'en-AU,en-GB;q=0.9')}' \\")
    print(f"  -H 'Cookie: {cookies}' \\")
    print(f"  --data-urlencode 'message={json.dumps(message, separators=(',', ':'))}' \\")
    print(f"  --data-urlencode 'aura.context={json.dumps(aura_context, separators=(',', ':'))}' \\")
    print(f"  --data-urlencode 'aura.pageURI={page_uri}' \\")
    print(f"  --data-urlencode 'aura.token={aura_token}' \\")
    print("  -sS")
    print()


def main():
    """Función principal con menú"""
    print("="*70)
    print("             DEBUG cURL GENERATOR - Verifone Invoice")
    print("="*70)
    print()
    print("Selecciona qué petición quieres debugear:")
    print()
    print("  1. Petición CABECERA (Header) - Lista de Work Orders")
    print("  2. Petición PRIMERA - Detalles de un Work Order específico")
    print("  3. Petición PII - Información sensible (terminal_id, dirección, etc.)")
    print()
    print("  0. Salir")
    print()

    try:
        opcion = input("Opción [1-3]: ").strip()

        if opcion == '1':
            debug_header_request()
        elif opcion == '2':
            debug_first_request()
        elif opcion == '3':
            debug_pii_request()
        elif opcion == '0':
            print("Saliendo...")
            return
        else:
            print("❌ Opción inválida")
            return

        print()
        print("="*70)
        print("TIP: Puedes copiar el comando cURL y ejecutarlo directamente")
        print("     para ver la respuesta del servidor y debugear el problema.")
        print()
        print("     Para ver la respuesta formateada:")
        print("     <comando_curl> | python3 -m json.tool")
        print("="*70)
        print()

    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario")
        return


if __name__ == '__main__':
    main()
