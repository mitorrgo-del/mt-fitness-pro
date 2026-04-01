class IconMapper {
  static const String _baseUrl = 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises';

  static String? getExerciseImageUrl(String name) {
    final lower = name.toLowerCase();
    
    // PECHO
    if (lower.contains('banca') && lower.contains('plano') && lower.contains('barra')) return '$_baseUrl/Barbell_Bench_Press/0.jpg';
    if (lower.contains('banca') && lower.contains('inclinado') && lower.contains('barra')) return '$_baseUrl/Barbell_Incline_Bench_Press/0.jpg';
    if (lower.contains('banca') && lower.contains('plano') && lower.contains('mancuerna')) return '$_baseUrl/Dumbbell_Bench_Press/0.jpg';
    if (lower.contains('banca') && lower.contains('inclinado') && lower.contains('mancuerna')) return '$_baseUrl/Dumbbell_Incline_Bench_Press/0.jpg';
    if (lower.contains('apertura')) return '$_baseUrl/Dumbbell_Fly/0.jpg';
    if (lower.contains('cruce') && lower.contains('polea')) return '$_baseUrl/Cable_Crossover/0.jpg';
    if (lower.contains('peck') || lower.contains('deck') || lower.contains('mariposa')) return '$_baseUrl/Butterfly/0.jpg';
    if (lower.contains('flexion') || lower.contains('pushup')) return '$_baseUrl/Push-up/0.jpg';
    if (lower.contains('fondos') && lower.contains('paralela')) return '$_baseUrl/Chest_Dip/0.jpg';
    if (lower.contains('pullover')) return '$_baseUrl/Dumbbell_Pullover/0.jpg';

    // ESPALDA
    if (lower.contains('dominada')) return '$_baseUrl/Pull-up/0.jpg';
    if (lower.contains('jalon') && lower.contains('pecho')) return '$_baseUrl/Cable_Pulldown/0.jpg';
    if (lower.contains('remo') && lower.contains('barra')) return '$_baseUrl/Barbell_Bent_Over_Row/0.jpg';
    if (lower.contains('remo') && lower.contains('mancuerna')) return '$_baseUrl/Dumbbell_One_Arm_Row/0.jpg';
    if (lower.contains('gironda') || (lower.contains('remo') && lower.contains('polea'))) return '$_baseUrl/Cable_Seated_Row/0.jpg';
    if (lower.contains('punta') || lower.contains('barra t')) return '$_baseUrl/T-Bar_Row/0.jpg';
    if (lower.contains('peso muerto') && !lower.contains('rumano')) return '$_baseUrl/Barbell_Deadlift/0.jpg';
    if (lower.contains('hiperextension')) return '$_baseUrl/Hyperextension/0.jpg';

    // PIERNA
    if (lower.contains('sentadilla') && lower.contains('frontal')) return '$_baseUrl/Barbell_Front_Squat/0.jpg';
    if (lower.contains('sentadilla') && lower.contains('hack')) return '$_baseUrl/Hack_Squat/0.jpg';
    if (lower.contains('bulgara')) return '$_baseUrl/Bulgarian_Split_Squat/0.jpg';
    if (lower.contains('sentadilla')) return '$_baseUrl/Barbell_Squat/0.jpg';
    if (lower.contains('prensa')) return '$_baseUrl/Leg_Press/0.jpg';
    if (lower.contains('extension') && lower.contains('cuad')) return '$_baseUrl/Leg_Extension/0.jpg';
    if (lower.contains('curl femoral')) return '$_baseUrl/Lying_Leg_Curl/0.jpg';
    if (lower.contains('peso muerto rumano')) return '$_baseUrl/Romanian_Deadlift/0.jpg';
    if (lower.contains('zancada') || lower.contains('lunge')) return '$_baseUrl/Barbell_Lunge/0.jpg';
    if (lower.contains('thrust') || lower.contains('puente')) return '$_baseUrl/Barbell_Glute_Bridge/0.jpg';
    if (lower.contains('gemelo') || lower.contains('talon')) return '$_baseUrl/Standing_Calf_Raise/0.jpg';

    // HOMBRO
    if (lower.contains('press militar') || lower.contains('press hombro')) return '$_baseUrl/Barbell_Shoulder_Press/0.jpg';
    if (lower.contains('arnold')) return '$_baseUrl/Arnold_Press/0.jpg';
    if (lower.contains('lateral')) return '$_baseUrl/Dumbbell_Lateral_Raise/0.jpg';
    if (lower.contains('frontal')) return '$_baseUrl/Dumbbell_Front_Raise/0.jpg';
    if (lower.contains('pajaro') || lower.contains('posterior')) return '$_baseUrl/Dumbbell_Reverse_Fly/0.jpg';
    if (lower.contains('menton')) return '$_baseUrl/Barbell_Upright_Row/0.jpg';
    if (lower.contains('face')) return '$_baseUrl/Face_Pull/0.jpg';
    if (lower.contains('encogimiento')) return '$_baseUrl/Barbell_Shrug/0.jpg';

    // BICEPS
    if (lower.contains('curl') && lower.contains('barra')) return '$_baseUrl/Barbell_Curl/0.jpg';
    if (lower.contains('martillo')) return '$_baseUrl/Dumbbell_Hammer_Curl/0.jpg';
    if (lower.contains('predicador') || lower.contains('scott')) return '$_baseUrl/Barbell_Preacher_Curl/0.jpg';
    if (lower.contains('concentrado')) return '$_baseUrl/Dumbbell_Concentration_Curl/0.jpg';
    if (lower.contains('curl') && lower.contains('mancuerna')) return '$_baseUrl/Dumbbell_Bicep_Curl/0.jpg';
    if (lower.contains('curl') && lower.contains('polea')) return '$_baseUrl/Cable_Curl/0.jpg';

    // TRICEPS
    if (lower.contains('frances') || lower.contains('skull')) return '$_baseUrl/Barbell_Lying_Triceps_Extension/0.jpg';
    if (lower.contains('polea') && lower.contains('tricep')) return '$_baseUrl/Cable_Triceps_Pushdown/0.jpg';
    if (lower.contains('patada')) return '$_baseUrl/Dumbbell_Triceps_Kickback/0.jpg';
    if (lower.contains('fondos') && lower.contains('banco')) return '$_baseUrl/Bench_Dip/0.jpg';
    if (lower.contains('press') && lower.contains('cerrado')) return '$_baseUrl/Close-Grip_Barbell_Bench_Press/0.jpg';

    // CORE
    if (lower.contains('crunch')) return '$_baseUrl/Crunch/0.jpg';
    if (lower.contains('pierna') && lower.contains('eleva')) return '$_baseUrl/Hanging_Leg_Raise/0.jpg';
    if (lower.contains('plancha') || lower.contains('plank')) return '$_baseUrl/Front_Plank/0.jpg';
    if (lower.contains('rueda')) return '$_baseUrl/Ab_Roller/0.jpg';
    
    return null; 
  }

  static String getExerciseDrawing(String name, String? muscleGroup) {
    if (muscleGroup != null) {
        final mg = muscleGroup.toLowerCase();
        if (mg == 'pecho') return '🦍';
        if (mg == 'espalda') return '🐢';
        if (mg == 'pierna') return '🦵';
        if (mg == 'hombro') return '🦅';
        if (mg == 'bíceps') return '💪';
        if (mg == 'tríceps') return '🦾';
        if (mg == 'core') return '🍫';
    }
    return '🏋️‍♂️';
  }

  static String getFoodDrawing(String name, String? category) {
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
    
    if (category != null) {
        final cat = category.toLowerCase();
        if (cat.contains('proteína')) return '🥩';
        if (cat.contains('hidrato')) return '🍚';
        if (cat.contains('grasa')) return '🥑';
        if (cat.contains('verdura')) return '🥗';
        if (cat.contains('fruta')) return '🍎';
        if (cat.contains('lácteo')) return '🥛';
    }
    return '🍽️';
  }
}
