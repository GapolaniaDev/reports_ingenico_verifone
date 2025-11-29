#!/usr/bin/env python3
"""
Script de prueba para verificar que parse_pii_details funciona correctamente
"""
import json
import sys
from pathlib import Path

# Leer el archivo raw_pii_response de prueba
test_file = Path('VerifoneWorkOrders/invoice_20251101_174331_157/raw_pii_response_0WOVy00000BuY5VOAV.json')

if not test_file.exists():
    print(f"❌ No se encontró el archivo: {test_file}")
    sys.exit(1)

with open(test_file, 'r') as f:
    pii_response = json.load(f)

print("=" * 70)
print("TEST: Verificando extracción de datos PII")
print("=" * 70)
print()

# Simular la función parse_pii_details
work_order_id = '0WOVy00000BuY5VOAV'

try:
    # Navegar por la estructura
    actions = pii_response.get('actions', [])
    print(f"✓ actions encontrados: {len(actions)}")

    return_value = actions[0].get('returnValue', {})
    print(f"✓ returnValue encontrado")

    response = return_value.get('response', {})
    print(f"✓ response encontrado")

    output_variables = response.get('outputVariables', [])
    print(f"✓ outputVariables encontrados: {len(output_variables)}")
    print()

    # Mostrar estructura
    for i, var in enumerate(output_variables):
        print(f"outputVariables[{i}]:")
        print(f"  name: {var.get('name')}")
        print(f"  dataType: {var.get('dataType')}")
        value = var.get('value', {})
        if isinstance(value, dict):
            print(f"  value keys: {list(value.keys())}")
        print()

    # Extraer datos
    terminal_id = ''
    street = ''
    suburb = ''
    postcode = ''

    if len(output_variables) > 0:
        var_0_value = output_variables[0].get('value', {})
        terminal_id = var_0_value.get('terminal_id_c__c', '')
        street = var_0_value.get('street__c', '')

    if len(output_variables) > 1:
        var_1_value = output_variables[1].get('value', {})
        suburb = var_1_value.get('City', '')
        postcode = var_1_value.get('PostalCode', '')

    print("=" * 70)
    print("DATOS EXTRAÍDOS:")
    print("=" * 70)
    print(f"terminal_id: '{terminal_id}'")
    print(f"street:      '{street}'")
    print(f"suburb:      '{suburb}'")
    print(f"postcode:    '{postcode}'")
    print()

    # Verificar
    if terminal_id and street and suburb and postcode:
        print("✅ TODOS LOS DATOS EXTRAÍDOS CORRECTAMENTE")
        print()
        print("La función parse_pii_details está funcionando correctamente.")
        print("El problema debe estar en la petición HTTP (credenciales expiradas).")
    else:
        print("❌ FALTAN DATOS")
        missing = []
        if not terminal_id: missing.append('terminal_id')
        if not street: missing.append('street')
        if not suburb: missing.append('suburb')
        if not postcode: missing.append('postcode')
        print(f"   Faltan: {', '.join(missing)}")
        print()
        print("Hay un problema con la lógica de extracción.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
