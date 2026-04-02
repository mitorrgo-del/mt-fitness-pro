class IconMapper {
  static String? getExerciseImageUrl(String name, [String? muscleGroup]) {
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
