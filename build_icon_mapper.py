import os
import re

images_dir = "mt_fitness_app/assets/images"
image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png'))]

def slugify(text):
    # Remove separators and lower
    return "".join(re.findall(r'[a-zA-Z0-9]', text.lower()))

# Build a mapping of slug -> filename
slug_to_file = {}
for f in image_files:
    # Skip icons we use for fallbacks
    if "_icon_" in f:
        continue
    
    name_only = os.path.splitext(f)[0]
    slug = slugify(name_only)
    slug_to_file[slug] = f

mapping_entries = []
for slug, filename in slug_to_file.items():
    mapping_entries.append(f"    '{slug}': 'assets/images/{filename}',")

mapping_js = "\n".join(mapping_entries)

dart_code = f"""class IconMapper {{
  static const Map<String, String> _allImages = {{
{mapping_js}
  }};

  static String _slugify(String text) {{
      return text.toLowerCase().replaceAll(RegExp(r'[^a-zA-Z0-9]'), '');
  }}

  static String? getExerciseImageUrl(String name, [String? muscleGroup]) {{
    if (name.isEmpty) return null;
    
    final slug = _slugify(name);
    
    // 1. Try exact slug match
    if (_allImages.containsKey(slug)) return _allImages[slug];
    
    // 2. Try partial match in Name
    for (var entry in _allImages.entries) {{
        if (slug.contains(entry.key) || entry.key.contains(slug)) return entry.value;
    }}

    // 3. Muscle Group Fallbacks
    if (muscleGroup != null) {{
      final mg = muscleGroup.toLowerCase();
      if (mg.contains('pecho') || mg.contains('pectoral')) return 'assets/images/pecho_icon_1775126194087.png';
      if (mg.contains('espalda') || mg.contains('dorsal')) return 'assets/images/espalda_icon_1775126212481.png';
      if (mg.contains('pierna') || mg.contains('cuad') || mg.contains('femoral') || mg.contains('glute')) return 'assets/images/pierna_icon_1775126227797.png';
      if (mg.contains('hombro') || mg.contains('delto')) return 'assets/images/hombro_icon_1775126243283.png';
      if (mg.contains('biceps') || mg.contains('bíceps')) return 'assets/images/biceps_icon_1775126261867.png';
      if (mg.contains('triceps') || mg.contains('tríceps')) return 'assets/images/triceps_icon_1775126276135.png';
      if (mg.contains('core') || mg.contains('abdominal') || mg.contains('abdomen')) return 'assets/images/core_icon_1775126289413.png';
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

  static String getFoodDrawing(String name, String? category) {{
    final lower = name.toLowerCase();
    if (lower.contains('pollo') || lower.contains('pavo')) return '🍗';
    if (lower.contains('ternera') || lower.contains('cerdo') || lower.contains('lomo') || lower.contains('jamón')) return '🥩';
    if (lower.contains('salmón') || lower.contains('atún') || lower.contains('merluza') || lower.contains('bacalao') || lower.contains('pescado') || lower.contains('lubina') || lower.contains('dorada') || lower.contains('sardina') || lower.contains('caballa') || lower.contains('trucha')) return '🐟';
    if (lower.contains('gamba') || lower.contains('langostino') || lower.contains('calamar') || lower.contains('pulpo') || lower.contains('cangrejo') || lower.contains('mejillón')) return '🦐';
    if (lower.contains('huevo') || lower.contains('clara')) return '🥚';
    if (lower.contains('tofu') || lower.contains('seitán') || lower.contains('heura') || lower.contains('soja')) return '🌱';
    if (lower.contains('arroz')) return '🍚';
    if (lower.contains('pasta') || lower.contains('espagueti') || lower.contains('macarrones')) return '🍝';
    if (lower.contains('avena') || lower.contains('cereal') || lower.contains('muesli')) return '🥣';
    if (lower.contains('patata') || lower.contains('boniato') || lower.contains('yuca')) return '🥔';
    if (lower.contains('pan') || lower.contains('biscote')) return '🍞';
    if (lower.contains('garbanzo') || lower.contains('lenteja') || lower.contains('judía') || lower.contains('guisante')) return '🧆';
    if (lower.contains('aceite')) return '🫒';
    if (lower.contains('aguacate')) return '🥑';
    if (lower.contains('nuez') || lower.contains('almendra') || lower.contains('cacahuete') || lower.contains('pistacho') || lower.contains('anacardo') || lower.contains('pecana') || lower.contains('avellana') || lower.contains('semilla') || lower.contains('piñón')) return '🥜';
    if (lower.contains('chocolate')) return '🍫';
    if (lower.contains('brócoli')) return '🥦';
    if (lower.contains('espinaca') || lower.contains('lechuga') || lower.contains('canónigo') || lower.contains('rúcula') || lower.contains('kale') || lower.contains('col')) return '🥬';
    if (lower.contains('tomate')) return '🍅';
    if (lower.contains('zanahoria')) return '🥕';
    if (lower.contains('champiñón') || lower.contains('seta')) return '🍄';
    if (lower.contains('manzana')) return '🍎';
    if (lower.contains('plátano')) return '🍌';
    if (lower.contains('naranja') || lower.contains('mandarina') || lower.contains('limón') || lower.contains('pomelo')) return '🍊';
    if (lower.contains('fresa') || lower.contains('arándano') || lower.contains('frambuesa') || lower.contains('mora') || lower.contains('cereza')) return '🍓';
    if (lower.contains('piña')) return '🍍';
    if (lower.contains('sandía')) return '🍉';
    if (lower.contains('uva')) return '🍇';
    if (lower.contains('leche')) return '🥛';
    if (lower.contains('yogur') || lower.contains('queso')) return '🧀';
    if (lower.contains('proteína') || lower.contains('whey') || lower.contains('creatina') || lower.contains('caseína')) return '🥤';
    if (lower.contains('miel') || lower.contains('azúcar')) return '🍯';
    
    if (category != null) {{
        final cat = category.toLowerCase();
        if (cat.contains('proteína')) return '🥩';
        if (cat.contains('hidrato')) return '🍚';
        if (cat.contains('grasa')) return '🥑';
        if (cat.contains('verdura')) return '🥗';
        if (cat.contains('fruta')) return '🍎';
        if (cat.contains('lácteo')) return '🥛';
    }}
    return '🍽️';
  }}
}}
"""

with open("mt_fitness_app/lib/utils/icon_mapper.dart", "w", encoding="utf-8") as f:
    f.write(dart_code)
