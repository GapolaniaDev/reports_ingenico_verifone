#!/usr/bin/env python3
"""
Script to generate red and green status icons for the Aura cURL Interceptor extension
Red = Incomplete (default)
Green = All interceptors captured
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
os.makedirs('icons', exist_ok=True)

def create_status_icon(size, color, filename):
    """Create a status icon with the specified color"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw circle background
    padding = size // 10
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=color,
        outline=(255, 255, 255, 255),
        width=max(2, size // 32)
    )

    # Draw lightning bolt symbol
    center_x = size // 2
    center_y = size // 2
    bolt_size = size // 3

    # Lightning bolt points
    points = [
        (center_x + bolt_size // 4, center_y - bolt_size),
        (center_x - bolt_size // 4, center_y),
        (center_x + bolt_size // 8, center_y),
        (center_x - bolt_size // 4, center_y + bolt_size),
        (center_x + bolt_size // 4, center_y + bolt_size // 6),
        (center_x - bolt_size // 8, center_y + bolt_size // 6),
    ]

    draw.polygon(points, fill=(255, 255, 255, 255))

    # Save the image
    img.save(filename, 'PNG')
    print(f"✓ Created {filename}")

# Red icons (incomplete state)
create_status_icon(16, (239, 68, 68, 255), 'icons/icon16-red.png')  # #ef4444
create_status_icon(48, (239, 68, 68, 255), 'icons/icon48-red.png')
create_status_icon(128, (239, 68, 68, 255), 'icons/icon128-red.png')

# Green icons (complete state)
create_status_icon(16, (16, 185, 129, 255), 'icons/icon16-green.png')  # #10b981
create_status_icon(48, (16, 185, 129, 255), 'icons/icon48-green.png')
create_status_icon(128, (16, 185, 129, 255), 'icons/icon128-green.png')

# Blue icons (Work Orders List)
create_status_icon(16, (59, 130, 246, 255), 'icons/icon16-blue.png')  # #3b82f6
create_status_icon(48, (59, 130, 246, 255), 'icons/icon48-blue.png')
create_status_icon(128, (59, 130, 246, 255), 'icons/icon128-blue.png')

print("\n✅ All status icons created successfully!")
print("🔴 Red icons (incomplete): icon*-red.png")
print("🟢 Green icons (complete): icon*-green.png")
print("🔵 Blue icons (Work Orders List): icon*-blue.png")
