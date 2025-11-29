#!/usr/bin/env python3
"""
Script para generar los iconos de la extensión
Requiere: pip install pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Crea un icono con gradiente púrpura y símbolo de rayo"""

    # Crear imagen con fondo transparente
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dibujar rectángulo redondeado con gradiente simulado
    # Color púrpura del gradiente
    color1 = (102, 126, 234)  # #667eea
    color2 = (118, 75, 162)   # #764ba2

    # Crear gradiente vertical
    for y in range(size):
        # Interpolar colores
        ratio = y / size
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)

        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b, 255))

    # Dibujar borde redondeado
    radius = int(size * 0.2)

    # Crear máscara para esquinas redondeadas
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=255)

    # Aplicar máscara
    img.putalpha(mask)

    # Dibujar rayo (⚡) en blanco
    scale = size / 128
    offset_x = int(size * 0.3)
    offset_y = int(size * 0.2)

    # Puntos del rayo
    lightning = [
        (offset_x + int(35 * scale), offset_y + int(15 * scale)),
        (offset_x + int(25 * scale), offset_y + int(50 * scale)),
        (offset_x + int(35 * scale), offset_y + int(50 * scale)),
        (offset_x + int(25 * scale), offset_y + int(85 * scale)),
        (offset_x + int(45 * scale), offset_y + int(55 * scale)),
        (offset_x + int(35 * scale), offset_y + int(55 * scale)),
        (offset_x + int(45 * scale), offset_y + int(15 * scale)),
    ]

    draw.polygon(lightning, fill=(255, 255, 255, 255))

    # Guardar imagen
    img.save(output_path, 'PNG')
    print(f"✓ Icono creado: {output_path}")

def main():
    """Crear los tres tamaños de iconos"""

    # Crear carpeta icons si no existe
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    # Crear iconos en diferentes tamaños
    sizes = [16, 48, 128]

    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon{size}.png')
        create_icon(size, output_path)

    print("\n✅ Todos los iconos creados exitosamente!")
    print(f"📁 Ubicación: {icons_dir}")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: Se requiere Pillow (PIL)")
        print("Instala con: pip install pillow")
        print("\nAlternativamente, abre generate-icons.html en tu navegador")
        print("y descarga los iconos manualmente.")
