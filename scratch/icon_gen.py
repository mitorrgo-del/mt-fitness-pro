import os
from PIL import Image

src = 'mt_fitness_app/assets/images/logo_oro.png'
img = Image.open(src)

targets = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

base_dir = 'mt_fitness_app/android/app/src/main/res'

for folder, size in targets.items():
    path = os.path.join(base_dir, folder, 'ic_launcher.png')
    if os.path.exists(path):
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(path)
        print(f'Updated {path} ({size}x{size})')

img.close()
