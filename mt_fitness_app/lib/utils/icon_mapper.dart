class IconMapper {
  static const String _baseUrl = 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises';

  static String? getExerciseImageUrl(String name) {
    final lower = name.toLowerCase();
    
    // PECHO
    if (lower.contains('press banca plano con barra')) return '$_baseUrl/Barbell_Bench_Press/0.jpg';
    if (lower.contains('press banca inclinado con barra')) return '$_baseUrl/Barbell_Incline_Bench_Press/0.jpg';
    if (lower.contains('press banca declinado con barra')) return '$_baseUrl/Barbell_Decline_Bench_Press/0.jpg';
    if (lower.contains('press banca plano con mancuernas')) return '$_baseUrl/Dumbbell_Bench_Press/0.jpg';
    if (lower.contains('press banca inclinado con mancuernas')) return '$_baseUrl/Dumbbell_Incline_Bench_Press/0.jpg';
    if (lower.contains('press banca declinado con mancuernas')) return '$_baseUrl/Dumbbell_Decline_Bench_Press/0.jpg';
    if (lower.contains('aperturas planas con mancuernas') || lower.contains('aperturas planas')) return '$_baseUrl/Dumbbell_Fly/0.jpg';
    if (lower.contains('aperturas inclinadas')) return '$_baseUrl/Dumbbell_Incline_Fly/0.jpg';
    if (lower.contains('cruces en polea alta')) return '$_baseUrl/Cable_Crossover/0.jpg';
    if (lower.contains('cruces en polea baja')) return '$_baseUrl/Low_Cable_Crossover/0.jpg';
    if (lower.contains('peck deck') || lower.contains('maquina convergente')) return '$_baseUrl/Butterfly/0.jpg';
    if (lower.contains('flexiones inclinadas')) return '$_baseUrl/Incline_Push-up/0.jpg';
    if (lower.contains('flexiones declinadas')) return '$_baseUrl/Decline_Push-Up/0.jpg';
    if (lower.contains('flexiones') || lower.contains('pushup')) return '$_baseUrl/Push-up/0.jpg';
    if (lower.contains('pullover')) return '$_baseUrl/Dumbbell_Pullover/0.jpg';

    // ESPALDA
    if (lower.contains('dominadas supinas') || lower.contains('chin-up')) return '$_baseUrl/Chin-up/0.jpg';
    if (lower.contains('dominadas') || lower.contains('pull-up')) return '$_baseUrl/Pull-up/0.jpg';
    if (lower.contains('jalón al pecho') || lower.contains('jalon al pecho')) return '$_baseUrl/Cable_Pulldown/0.jpg';
    if (lower.contains('jalón tras nuca')) return '$_baseUrl/Cable_Rear_Pulldown/0.jpg';
    if (lower.contains('remo con barra')) return '$_baseUrl/Barbell_Bent_Over_Row/0.jpg';
    if (lower.contains('remo con mancuerna')) return '$_baseUrl/Dumbbell_One_Arm_Row/0.jpg';
    if (lower.contains('remo gironda') || lower.contains('polea baja')) return '$_baseUrl/Cable_Seated_Row/0.jpg';
    if (lower.contains('remo en punta') || lower.contains('barra t')) return '$_baseUrl/T-Bar_Row/0.jpg';
    if (lower.contains('peso muerto convencional')) return '$_baseUrl/Barbell_Deadlift/0.jpg';
    if (lower.contains('peso muerto sumo')) return '$_baseUrl/Sumo_Deadlift/0.jpg';
    if (lower.contains('hiperextensiones')) return '$_baseUrl/Hyperextension/0.jpg';

    // PIERNA
    if (lower.contains('sentadilla frontal')) return '$_baseUrl/Barbell_Front_Squat/0.jpg';
    if (lower.contains('sentadilla hack')) return '$_baseUrl/Hack_Squat/0.jpg';
    if (lower.contains('sentadilla búlgara') || lower.contains('bulgara')) return '$_baseUrl/Bulgarian_Split_Squat/0.jpg';
    if (lower.contains('sentadilla goblet')) return '$_baseUrl/Goblet_Squat/0.jpg';
    if (lower.contains('sentadilla') || lower.contains('squat')) return '$_baseUrl/Barbell_Squat/0.jpg';
    if (lower.contains('prensa')) return '$_baseUrl/Leg_Press/0.jpg';
    if (lower.contains('extensiones de cuádriceps') || lower.contains('extensiones de cuadriceps')) return '$_baseUrl/Leg_Extension/0.jpg';
    if (lower.contains('curl femoral tumbado')) return '$_baseUrl/Lying_Leg_Curl/0.jpg';
    if (lower.contains('curl femoral sentado')) return '$_baseUrl/Seated_Leg_Curl/0.jpg';
    if (lower.contains('peso muerto rumano')) return '$_baseUrl/Romanian_Deadlift/0.jpg';
    if (lower.contains('zancada') || lower.contains('lunge')) return '$_baseUrl/Barbell_Lunge/0.jpg';
    if (lower.contains('hip thrust') || lower.contains('puente')) return '$_baseUrl/Barbell_Glute_Bridge/0.jpg';
    if (lower.contains('gemelos') || lower.contains('talones')) return '$_baseUrl/Standing_Calf_Raise/0.jpg';

    // HOMBRO
    if (lower.contains('press militar con mancuernas')) return '$_baseUrl/Dumbbell_Seated_Shoulder_Press/0.jpg';
    if (lower.contains('press militar') || lower.contains('press de hombros')) return '$_baseUrl/Barbell_Shoulder_Press/0.jpg';
    if (lower.contains('press arnold')) return '$_baseUrl/Arnold_Press/0.jpg';
    if (lower.contains('elevaciones laterales en polea')) return '$_baseUrl/Cable_Lateral_Raise/0.jpg';
    if (lower.contains('elevaciones laterales')) return '$_baseUrl/Dumbbell_Lateral_Raise/0.jpg';
    if (lower.contains('elevaciones frontales')) return '$_baseUrl/Dumbbell_Front_Raise/0.jpg';
    if (lower.contains('pájaros') || lower.contains('posterior')) return '$_baseUrl/Dumbbell_Reverse_Fly/0.jpg';
    if (lower.contains('remo al mentón') || lower.contains('remo al menton')) return '$_baseUrl/Barbell_Upright_Row/0.jpg';
    if (lower.contains('encogimientos')) return '$_baseUrl/Barbell_Shrug/0.jpg';

    // BICEPS
    if (lower.contains('curl de bíceps con barra') || lower.contains('curl con barra')) return '$_baseUrl/Barbell_Curl/0.jpg';
    if (lower.contains('curl martillo')) return '$_baseUrl/Dumbbell_Hammer_Curl/0.jpg';
    if (lower.contains('curl predicador') || lower.contains('banco scott')) return '$_baseUrl/Barbell_Preacher_Curl/0.jpg';
    if (lower.contains('curl concentrado')) return '$_baseUrl/Dumbbell_Concentration_Curl/0.jpg';
    if (lower.contains('curl en polea')) return '$_baseUrl/Cable_Curl/0.jpg';
    if (lower.contains('curl de bíceps con mancuerna') || lower.contains('curl con mancuerna')) return '$_baseUrl/Dumbbell_Bicep_Curl/0.jpg';

    // TRICEPS
    if (lower.contains('press francés') || lower.contains('press frances') || lower.contains('skullcrusher')) return '$_baseUrl/Barbell_Lying_Triceps_Extension/0.jpg';
    if (lower.contains('extensión de tríceps tras nuca') || lower.contains('extension tras nuca')) return '$_baseUrl/Dumbbell_Seated_Triceps_Extension/0.jpg';
    if (lower.contains('extensiones en polea') || lower.contains('tríceps en polea')) return '$_baseUrl/Cable_Triceps_Pushdown/0.jpg';
    if (lower.contains('patada de tríceps') || lower.contains('patada de triceps')) return '$_baseUrl/Dumbbell_Triceps_Kickback/0.jpg';
    if (lower.contains('fondos en paralelas')) return '$_baseUrl/Triceps_Dip/0.jpg';
    if (lower.contains('fondos entre bancos')) return '$_baseUrl/Bench_Dip/0.jpg';

    // CORE
    if (lower.contains('crunch')) return '$_baseUrl/Crunch/0.jpg';
    if (lower.contains('elevación de piernas') || lower.contains('leg raise')) return '$_baseUrl/Hanging_Leg_Raise/0.jpg';
    if (lower.contains('plancha') || lower.contains('plank')) return '$_baseUrl/Front_Plank/0.jpg';
    if (lower.contains('rueda abdominal') || lower.contains('ab wheel')) return '$_baseUrl/Ab_Roller/0.jpg';
    if (lower.contains('russian twist')) return '$_baseUrl/Russian_Twist/0.jpg';

    // GENERIC FALLBACKS
    if (lower.contains('remo')) return '$_baseUrl/Barbell_Bent_Over_Row/0.jpg';
    if (lower.contains('curl')) return '$_baseUrl/Dumbbell_Bicep_Curl/0.jpg';
    
    return null; // Return null if no specific image is found, so we show the emoji fallback
  }

  static String getExerciseDrawing(String name, String? muscleGroup) {
    if (getExerciseImageUrl(name) != null) {
        return '🖼️'; // Just a marker, won't be used if URL is prioritized in UI
    }

    final lower = name.toLowerCase();
    if (lower.contains('sentadilla') || lower.contains('squat') || lower.contains('zancada')) return '🦵';
    if (lower.contains('press banca') || lower.contains('press de pecho') || lower.contains('flexion')) return '🛏️💪';
    if (lower.contains('dominadas') || lower.contains('pull') || lower.contains('jalón')) return '🧗‍♂️';
    if (lower.contains('peso muerto') || lower.contains('deadlift')) return '🏋️‍♂️';
    if (lower.contains('curl')) return '💪';
    if (lower.contains('plancha') || lower.contains('plank') || lower.contains('core') || lower.contains('abdominal') || lower.contains('crunch')) return '🧘‍♂️';
    if (lower.contains('remo')) return '🚣‍♂️';
    if (lower.contains('fondos') || lower.contains('tríceps') || lower.contains('extensión')) return '🦾';
    if (lower.contains('hombro') || lower.contains('militar') || lower.contains('elevaciones') || lower.contains('vuelos')) return '🦅';
    if (lower.contains('prensa')) return '💺🦵';
    if (lower.contains('gemelo') || lower.contains('talon')) return '🦶';
    
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
