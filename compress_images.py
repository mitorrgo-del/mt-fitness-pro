import os
from PIL import Image

images_dir = "mt_fitness_app/assets/images"
image_files = os.listdir(images_dir)

compressed_count = 0
for f in image_files:
    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
        file_path = os.path.join(images_dir, f)
        try:
            with Image.open(file_path) as img:
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=60)
            compressed_count += 1
        except Exception as e:
            print(f"Failed to compress {f}: {e}")

print(f"Compressed {compressed_count} images.")
