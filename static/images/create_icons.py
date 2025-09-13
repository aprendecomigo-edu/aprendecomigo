#!/usr/bin/env python3
"""
Create placeholder PWA icons for Aprende Comigo.
Creates simple colored squares with "AC" text as placeholders.
"""

import os

from PIL import Image, ImageDraw, ImageFont


def create_icon(size, output_path):
    """Create a simple icon with the given size."""
    # Create a new image with a gradient background
    img = Image.new("RGB", (size, size), color="#3B82F6")  # Blue background

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Draw a circular background
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#FFFFFF",  # White circle
    )

    # Add text "AC" (Aprende Comigo)
    text = "AC"

    # Use default font since we can't guarantee specific fonts are available
    font = ImageFont.load_default()

    # Calculate text position (center)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2

    # Draw the text
    draw.text((x, y), text, fill="#3B82F6", font=font)

    # Save the image
    img.save(output_path, "PNG")
    print(f"Created {output_path}")


# Create the icons
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create 192x192 icon
    create_icon(192, os.path.join(script_dir, "icon-192.png"))

    # Create 512x512 icon
    create_icon(512, os.path.join(script_dir, "icon-512.png"))

    print("PWA icons created successfully!")
