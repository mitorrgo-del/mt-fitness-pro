import os
import re

# Correct path for assets in the project
images_dir = "mt_fitness_app/assets/images"
image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png'))]

# Translation bridge for better matching
translations = {
    'pecho': 'chest',
    'espalda': 'back',
    'hombro': 'shoulder',
    'biceps': 'bicep',
    'triceps': 'tricep',
    'pierna': 'leg',
    'cuadriceps': 'quad',
    'isquios': 'hamstring',
    'gluteo': 'glute',
    'gemelo': 'calf',
    'core': 'abs',
    'abdominal': 'crunch',
    'barra': 'barbell',
    'mancuerna': 'dumbbell',
    'mancuernas': 'dumbbell',
    'polea': 'cable',
    'maquina': 'machine',
    'sentadilla': 'squat',
    'peso muerto': 'deadlift',
    'press': 'press',
    'aperturas': 'fly',
    'remo': 'row',
    'dominadas': 'pullup',
    'fondos': 'dip',
    'zancada': 'lunge',
    'extension': 'extension',
    'curl': 'curl',
    'elevacion': 'raise',
    'inclinado': 'incline',
    'declinado': 'decline',
    'plano': 'flat',
}

def slugify(text):
    # Remove separators and lower
    return "".join(re.findall(r'[a-zA-Z0-9]', text.lower()))

def get_keywords(text):
    text = text.lower()
    for sp, en in translations.items():
        if sp in text:
            text += " " + en
    return set(re.findall(r'[a-z0-9]+', text))

# Build a mapping of slug -> filename
slug_to_file = {}
for f in image_files:
    if "_icon_" in f:
        continue
    name_only = os.path.splitext(f)[0]
    slug = slugify(name_only)
    slug_to_file[slug] = f

mapping_entries = []
for slug, filename in slug_to_file.items():
    mapping_entries.append(f"    '{slug}': 'assets/images/{filename}',")

mapping_js = "\n".join(mapping_entries)

# Build translations mapping for Dart
trans_entries = []
for k, v in translations.items():
    trans_entries.append(f"    '{k}': '{v}',")
trans_js = "\n".join(trans_entries)

dart_code = f"""import 'package:flutter/material.dart';

class IconMapper {{
  static const Map<String, String> _allImages = {{
{mapping_js}
  }};

  static const Map<String, String> _translations = {{
{trans_js}
  }};

  static String _slugify(String text) {{
      return text.toLowerCase().replaceAll(RegExp(r'[^a-zA-Z0-9]'), '');
  }}

  static String? getExerciseImageUrl(String name, [String? muscleGroup]) {{
    if (name.isEmpty) return null;
    
    String searchTitle = name.toLowerCase();
    
    // 1. Try exact slug match
    final directSlug = _slugify(name);
    if (_allImages.containsKey(directSlug)) return _allImages[directSlug];
    
    // 2. Try translating and matching
    String translatedName = searchTitle;
    _translations.forEach((es, en) {{
      if (searchTitle.contains(es)) translatedName += en;
    }});
    
    final translatedSlug = _slugify(translatedName);
    if (_allImages.containsKey(translatedSlug)) return _allImages[translatedSlug];
    
    // 3. Score-based matching (Highest overlap of keywords)
    String? bestMatch;
    int maxScore = 0;
    
    for (var entry in _allImages.entries) {{
      int score = 0;
      if (translatedSlug.contains(entry.key)) score += 10;
      if (entry.key.contains(directSlug)) score += 5;
      
      if (score > maxScore) {{
        maxScore = score;
        bestMatch = entry.value;
      }}
    }}

    if (bestMatch != null && maxScore >= 5) return bestMatch;

    // 4. Muscle Group Fallbacks
    if (muscleGroup != null) {{
      final mg = muscleGroup.toLowerCase();
      if (mg.contains('pecho')) return 'assets/images/pecho_icon_1775126194087.png';
      if (mg.contains('espalda')) return 'assets/images/espalda_icon_1775126212481.png';
      if (mg.contains('pierna')) return 'assets/images/pierna_icon_1775126227797.png';
      if (mg.contains('hombro')) return 'assets/images/hombro_icon_1775126243283.png';
      if (mg.contains('biceps')) return 'assets/images/biceps_icon_1775126261867.png';
      if (mg.contains('triceps')) return 'assets/images/triceps_icon_1775126276135.png';
      if (mg.contains('core')) return 'assets/images/core_icon_1775126289413.png';
    }}
    
    return null;
  }}

  static String getExerciseDrawing(String name, String? muscleGroup) {{
    if (muscleGroup != null) {{
        final mg = muscleGroup.toLowerCase();
        if (mg == 'pecho') return '🦍';
        if (mg == 'espalda') return '🐢';
        if (mg == 'pierna') return '🦵';
        if (mg == 'hombro') return '🦅';
        if (mg == 'bíceps') return '💪';
        if (mg == 'tríceps') return '🦾';
        if (mg == 'core') return '🍫';
    }}
    return '🏋️‍♂️';
  }}
}}
"""

output_path = "mt_fitness_app/lib/utils/icon_mapper.dart"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.write(dart_code)

print("IconMapper.dart generated successfully!")
