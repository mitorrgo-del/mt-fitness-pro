class IconMapper {
  static String? getExerciseImageUrl(String name, [String? muscleGroup]) {
    final lower = name.toLowerCase();
    
    if (lower.contains('banca') && lower.contains('plano') && lower.contains('mancuerna')) return 'assets/images/Decline_Dumbbell_Bench_Press.jpg';
    if (lower.contains('banca') && lower.contains('inclinado') && lower.contains('barra')) return 'assets/images/Barbell_Incline_Bench_Press_-_Medium_Grip.jpg';
    if (lower.contains('banca') && lower.contains('plano') && lower.contains('barra')) return 'assets/images/Barbell_Bench_Press_-_Medium_Grip.jpg';
    if (lower.contains('apertura')) return 'assets/images/Decline_Dumbbell_Flyes.jpg';
    if (lower.contains('cruce') && lower.contains('polea')) return 'assets/images/Cable_Crossover.jpg';
    if (lower.contains('peck') || lower.contains('deck') || lower.contains('mariposa')) return 'assets/images/Butterfly.jpg';
    if (lower.contains('flexion') || lower.contains('push-up') || lower.contains('pushup')) return 'assets/images/Clock_Push-Up.jpg';
    if (lower.contains('pullover')) return 'assets/images/Bent-Arm_Dumbbell_Pullover.jpg';
    if (lower.contains('dominada')) return 'assets/images/Band_Assisted_Pull-Up.jpg';
    if (lower.contains('jalon') && lower.contains('pecho')) return 'assets/images/Underhand_Cable_Pulldowns.jpg';
    if (lower.contains('punta') || lower.contains('barra t')) return 'assets/images/Lying_T-Bar_Row.jpg';
    if (lower.contains('peso muerto') && !lower.contains('rumano')) return 'assets/images/Barbell_Deadlift.jpg';
    if (lower.contains('hiperextension')) return 'assets/images/Hyperextensions_Back_Extensions.jpg';
    if (lower.contains('sentadilla') && lower.contains('hack')) return 'assets/images/Barbell_Hack_Squat.jpg';
    if (lower.contains('sentadilla')) return 'assets/images/Barbell_Squat.jpg';
    if (lower.contains('prensa')) return 'assets/images/Calf_Press_On_The_Leg_Press_Machine.jpg';
    if (lower.contains('extension') && lower.contains('cuad')) return 'assets/images/Leg_Extensions.jpg';
    if (lower.contains('curl femoral')) return 'assets/images/Lying_Leg_Curls.jpg';
    if (lower.contains('peso muerto rumano')) return 'assets/images/Romanian_Deadlift.jpg';
    if (lower.contains('zancada') || lower.contains('lunge')) return 'assets/images/Barbell_Lunge.jpg';
    if (lower.contains('thrust') || lower.contains('puente')) return 'assets/images/Barbell_Glute_Bridge.jpg';
    if (lower.contains('gemelo') || lower.contains('talon')) return 'assets/images/Rocking_Standing_Calf_Raise.jpg';
    if (lower.contains('press militar') || lower.contains('press hombro')) return 'assets/images/Barbell_Shoulder_Press.jpg';
    if (lower.contains('arnold')) return 'assets/images/Kettlebell_Arnold_Press.jpg';
    if (lower.contains('face')) return 'assets/images/Face_Pull.jpg';
    if (lower.contains('encogimiento')) return 'assets/images/Barbell_Shrug.jpg';
    if (lower.contains('curl') && lower.contains('barra')) return 'assets/images/Barbell_Curl.jpg';
    if (lower.contains('martillo')) return 'assets/images/Alternate_Hammer_Curl.jpg';
    if (lower.contains('predicador') || lower.contains('scott')) return 'assets/images/Cable_Preacher_Curl.jpg';
    if (lower.contains('concentrado')) return 'assets/images/Concentration_Curls.jpg';
    if (lower.contains('curl') && lower.contains('mancuerna')) return 'assets/images/Dumbbell_Bicep_Curl.jpg';
    if (lower.contains('curl') && lower.contains('polea')) return 'assets/images/High_Cable_Curls.jpg';
    if (lower.contains('frances') || lower.contains('skull')) return 'assets/images/Band_Skull_Crusher.jpg';
    if (lower.contains('polea') && lower.contains('tricep')) return 'assets/images/Reverse_Grip_Triceps_Pushdown.jpg';
    if (lower.contains('fondos') && lower.contains('banco')) return 'assets/images/Bench_Dips.jpg';
    if (lower.contains('press') && lower.contains('cerrado')) return 'assets/images/Close-Grip_Barbell_Bench_Press.jpg';
    if (lower.contains('crunch')) return 'assets/images/Ab_Crunch_Machine.jpg';
    if (lower.contains('pierna') && lower.contains('eleva')) return 'assets/images/Hanging_Leg_Raise.jpg';
    if (lower.contains('plancha') || lower.contains('plank')) return 'assets/images/Plank.jpg';
    if (lower.contains('rueda')) return 'assets/images/Ab_Roller.jpg';

    // Fallbacks if nothing matched exactly
    if (muscleGroup != null) {
      final mg = muscleGroup.toLowerCase();
      if (mg == 'pecho') return 'assets/images/pecho.png';
      if (mg == 'espalda') return 'assets/images/espalda.png';
      if (mg == 'pierna') return 'assets/images/pierna.png';
      if (mg == 'hombro') return 'assets/images/hombro.png';
      if (mg == 'bíceps' || mg == 'biceps') return 'assets/images/biceps.png';
      if (mg == 'tríceps' || mg == 'triceps') return 'assets/images/triceps.png';
      if (mg == 'core') return 'assets/images/core.png';
    }
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
