import os
from PIL import Image

src = 'mt_fitness_app/assets/images/logo_oro.png'
base_dir = 'mt_fitness_app/android/app/src/main/res'

targets = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# 1. Update Legacy ic_launcher.png (Gold on Black)
img = Image.open(src)
for folder, size in targets.items():
    path = os.path.join(base_dir, folder, 'ic_launcher.png')
    # Create black background
    bg = Image.new('RGB', (size, size), (0, 0, 0))
    # Resize logo to 80% of size
    logo_size = int(size * 0.8)
    logo = img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    # Center it
    offset = (size - logo_size) // 2
    bg.paste(logo, (offset, offset), logo if logo.mode == 'RGBA' else None)
    bg.save(path)
    print(f'Updated Legacy Icon: {path}')

# 2. Update Adaptive ic_launcher_foreground.png (Transparent with padding)
# Standard Adaptive size is 108x108 units. We will scale based on xxxhdpi (192-324px)
# Actually, we can use the same mipmap sizes.
for folder, size in targets.items():
    path = os.path.join(base_dir, folder, 'ic_launcher_foreground.png')
    # Use 108/72 ratio roughly for adaptive icons (logo should be 66% of total area)
    # Total size for adaptive icon in folders is usually larger, but we'll match mipmap sizes for now
    # or just use 108 * density. 
    # For simplicity, we use same 'size' as ic_launcher but with more padding
    fg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    logo_size = int(size * 0.6) # Smaller to stay in safe zone
    logo = img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    offset = (size - logo_size) // 2
    fg.paste(logo, (offset, offset), logo if logo.mode == 'RGBA' else None)
    fg.save(path)
    print(f'Updated Foreground Icon: {path}')

img.close()
