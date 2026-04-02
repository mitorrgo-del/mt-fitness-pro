import os
import shutil

src_dir = "free_ex_db/exercises"
dst_dir = "mt_fitness_app/assets/images"

os.makedirs(dst_dir, exist_ok=True)

copied = 0
for folder in os.listdir(src_dir):
    folder_path = os.path.join(src_dir, folder)
    if os.path.isdir(folder_path):
        img_src = os.path.join(folder_path, "0.jpg")
        img_dst = os.path.join(dst_dir, f"{folder}.jpg")
        if os.path.exists(img_src):
            shutil.copy2(img_src, img_dst)
            copied += 1

print(f"Copied {copied} images to {dst_dir}")
