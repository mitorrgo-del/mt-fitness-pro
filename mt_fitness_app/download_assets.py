import os
import urllib.request
import json
import time

TARGET_DIR = "assets/exercises"
os.makedirs(TARGET_DIR, exist_ok=True)

# Common mappings based on icon_mapper.dart
target_downloads = {
    # Chest
    "Barbell_Bench_Press_-_Medium_Grip": "bench_press_barra.jpg",
    "Dumbbell_Bench_Press": "bench_press_mancuerna.jpg",
    "Butterfly": "peck_deck.jpg",
    "Cable_Crossover": "cruce_poleas.jpg",
    "Push-up": "flexiones.jpg",
    "Chest_Dip": "fondos_pecho.jpg",
    # Back
    "Pull-up": "dominadas.jpg",
    "Cable_Pulldown": "jalon_pecho.jpg",
    "Barbell_Bent_Over_Row": "remo_barra.jpg",
    "Dumbbell_One_Arm_Row": "remo_mancuerna.jpg",
    "Cable_Seated_Row": "remo_gironda.jpg",
    # Legs
    "Barbell_Squat": "sentadilla_barra.jpg",
    "Leg_Press": "prensa.jpg",
    "Leg_Extension": "extension_cuad.jpg",
    "Lying_Leg_Curl": "curl_femoral.jpg",
    "Romanian_Deadlift": "peso_muerto_rumano.jpg",
    "Barbell_Lunge": "zancadas.jpg",
    "Barbell_Glute_Bridge": "hip_thrust.jpg",
    "Standing_Calf_Raise": "gemelos.jpg",
    # Shoulders
    "Barbell_Shoulder_Press": "press_militar.jpg",
    "Arnold_Dumbbell_Press": "press_arnold.jpg",
    "Dumbbell_Lateral_Raise": "elevaciones_laterales.jpg",
    "Dumbbell_Front_Raise": "elevaciones_frontales.jpg",
    "Face_Pull": "face_pull.jpg",
    # Biceps
    "Barbell_Curl": "curl_biceps_barra.jpg",
    "Dumbbell_Hammer_Curl": "curl_martillo.jpg",
    "Dumbbell_Bicep_Curl": "curl_biceps_mancuerna.jpg",
    "Cable_Curl": "curl_polea.jpg",
    # Triceps
    "Cable_Triceps_Pushdown": "extension_triceps_polea.jpg",
    "Bench_Dip": "fondos_triceps.jpg",
    # Core
    "Crunch": "crunch_abdominal.jpg",
    "Front_Plank": "plancha.jpg",
    "Hanging_Leg_Raise": "elevacion_piernas.jpg"
}

BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises"

for src_folder, dst_filename in target_downloads.items():
    url = f"{BASE_URL}/{src_folder}/0.jpg"
    dst_path = os.path.join(TARGET_DIR, dst_filename)
    if not os.path.exists(dst_path):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(dst_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Downloaded {dst_filename}")
            time.sleep(0.5) # respect rate limit slightly
        except Exception as e:
            print(f"Failed to download {url}: {e}")

print("Done downloading assets.")
