import os
import re

images_dir = "mt_fitness_app/assets/images"
image_files = os.listdir(images_dir)

# Helper to find closest image
def find_image(keyword):
    for f in image_files:
        if keyword.lower() in f.lower():
            return f
    return None

mapping = []
def add_map(lower_condition, keyword, default_img=None):
    img = find_image(keyword) if keyword else default_img
    if not img and default_img:
        img = default_img
    if img:
        mapping.append(f"    if ({lower_condition}) return 'assets/images/{img}';")

# Pecho
add_map("lower.contains('banca') && lower.contains('inclinado') && lower.contains('mancuerna')", "Dumbbell_Incline_Bench_Press")
add_map("lower.contains('banca') && lower.contains('plano') && lower.contains('mancuerna')", "Dumbbell_Bench_Press")
add_map("lower.contains('banca') && lower.contains('inclinado') && lower.contains('barra')", "Barbell_Incline_Bench_Press")
add_map("lower.contains('banca') && lower.contains('plano') && lower.contains('barra')", "Barbell_Bench_Press")
add_map("lower.contains('apertura')", "Dumbbell_Fly")
add_map("lower.contains('cruce') && lower.contains('polea')", "Cable_Crossover")
add_map("lower.contains('peck') || lower.contains('deck') || lower.contains('mariposa')", "Butterfly")
add_map("lower.contains('flexion') || lower.contains('push-up') || lower.contains('pushup')", "Push-Up")
add_map("lower.contains('fondos') && lower.contains('paralela')", "Chest_Dip")
add_map("lower.contains('pullover')", "Dumbbell_Pullover")

# Espalda
add_map("lower.contains('dominada')", "Pull-up")
add_map("lower.contains('jalon') && lower.contains('pecho')", "Cable_Pulldown")
add_map("lower.contains('remo') && lower.contains('barra')", "Barbell_Bent_Over_Row")
add_map("lower.contains('remo') && lower.contains('mancuerna')", "Dumbbell_One_Arm_Row")
add_map("lower.contains('gironda') || (lower.contains('remo') && lower.contains('polea'))", "Cable_Seated_Row")
add_map("lower.contains('punta') || lower.contains('barra t')", "T-Bar_Row")
add_map("lower.contains('peso muerto') && !lower.contains('rumano')", "Barbell_Deadlift")
add_map("lower.contains('hiperextension')", "Hyperextension")

# Pierna
add_map("lower.contains('sentadilla') && lower.contains('frontal')", "Barbell_Front_Squat")
add_map("lower.contains('sentadilla') && lower.contains('hack')", "Hack_Squat")
add_map("lower.contains('bulgara')", "Bulgarian_Split_Squat")
add_map("lower.contains('sentadilla')", "Barbell_Squat")
add_map("lower.contains('prensa')", "Leg_Press")
add_map("lower.contains('extension') && lower.contains('cuad')", "Leg_Extension")
add_map("lower.contains('curl femoral')", "Lying_Leg_Curl")
add_map("lower.contains('peso muerto rumano')", "Romanian_Deadlift")
add_map("lower.contains('zancada') || lower.contains('lunge')", "Barbell_Lunge")
add_map("lower.contains('thrust') || lower.contains('puente')", "Barbell_Glute_Bridge")
add_map("lower.contains('gemelo') || lower.contains('talon')", "Standing_Calf_Raise")

# Hombro
add_map("lower.contains('press militar') || lower.contains('press hombro')", "Barbell_Shoulder_Press")
add_map("lower.contains('arnold')", "Arnold_Press")
add_map("lower.contains('lateral')", "Dumbbell_Lateral_Raise")
add_map("lower.contains('frontal')", "Dumbbell_Front_Raise")
add_map("lower.contains('pajaro') || lower.contains('posterior')", "Dumbbell_Reverse_Fly")
add_map("lower.contains('menton')", "Barbell_Upright_Row")
add_map("lower.contains('face')", "Face_Pull")
add_map("lower.contains('encogimiento')", "Barbell_Shrug")

# Biceps
add_map("lower.contains('curl') && lower.contains('barra')", "Barbell_Curl")
add_map("lower.contains('martillo')", "Hammer_Curl")
add_map("lower.contains('predicador') || lower.contains('scott')", "Preacher_Curl")
add_map("lower.contains('concentrado')", "Concentration_Curl")
add_map("lower.contains('curl') && lower.contains('mancuerna')", "Dumbbell_Bicep_Curl")
add_map("lower.contains('curl') && lower.contains('polea')", "Cable_Curl")

# Triceps
add_map("lower.contains('frances') || lower.contains('skull')", "Skull_Crusher", "Barbell_Lying_Triceps_Extension.jpg")
add_map("lower.contains('polea') && lower.contains('tricep')", "Triceps_Pushdown")
add_map("lower.contains('patada')", "Triceps_Kickback")
add_map("lower.contains('fondos') && lower.contains('banco')", "Bench_Dip")
add_map("lower.contains('press') && lower.contains('cerrado')", "Close-Grip_Barbell_Bench_Press", "Barbell_Bench_Press.jpg")

# Core
add_map("lower.contains('crunch')", "Crunch")
add_map("lower.contains('pierna') && lower.contains('eleva')", "Hanging_Leg_Raise")
add_map("lower.contains('plancha') || lower.contains('plank')", "Plank")
add_map("lower.contains('rueda')", "Ab_Roller")

# Inject list into standard code
mapping_str = "\n".join(mapping)

dart_code = f"""class IconMapper {{
  static String? getExerciseImageUrl(String name, [String? muscleGroup]) {{
    final lower = name.toLowerCase();
    
{mapping_str}

    // Fallbacks if nothing matched exactly
    if (muscleGroup != null) {{
      final mg = muscleGroup.toLowerCase();
      if (mg == 'pecho') return 'assets/images/pecho.png';
      if (mg == 'espalda') return 'assets/images/espalda.png';
      if (mg == 'pierna') return 'assets/images/pierna.png';
      if (mg == 'hombro') return 'assets/images/hombro.png';
      if (mg == 'bíceps' || mg == 'biceps') return 'assets/images/biceps.png';
      if (mg == 'tríceps' || mg == 'triceps') return 'assets/images/triceps.png';
      if (mg == 'core') return 'assets/images/core.png';
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
