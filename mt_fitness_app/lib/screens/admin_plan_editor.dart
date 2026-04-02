import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../widgets/premium_card.dart';
import '../utils/icon_mapper.dart';

class AdminPlanEditor extends StatefulWidget {
  final String userId;
  final String userName;

  const AdminPlanEditor({super.key, required this.userId, required this.userName});

  @override
  State<AdminPlanEditor> createState() => _AdminPlanEditorState();
}

class _AdminPlanEditorState extends State<AdminPlanEditor> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _userWorkout = [];
  List<dynamic> _userDiet = [];
  List<dynamic> _userMeasurements = [];
  List<dynamic> _userReports = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => _isLoading = true);
    try {
      final workout = await ApiService().getWorkoutPlan(userId: widget.userId);
      final diet = await ApiService().getDietPlan(userId: widget.userId);
      final measurements = await ApiService().getMeasurements(widget.userId);
      final reports = await ApiService().getReportHistory(widget.userId);
      setState(() {
        _userWorkout = workout;
        _userDiet = diet;
        _userMeasurements = measurements;
        _userReports = reports;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Plan: ${widget.userName}'),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.calendarPlus, color: AppTheme.primary),
            onPressed: () async {
              await ApiService().addSubscription(widget.userId, 30);
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Plan extendido 30 días.')));
              _loadAll();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textMuted,
          tabs: const [
            Tab(icon: Icon(LucideIcons.dumbbell), text: 'Rutina'),
            Tab(icon: Icon(LucideIcons.utensils), text: 'Dieta'),
            Tab(icon: Icon(LucideIcons.lineChart), text: 'Medidas'),
            Tab(icon: Icon(LucideIcons.user), text: 'Perfil'),
          ],
        ),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
        : TabBarView(
            controller: _tabController,
            children: [
              _buildWorkoutTab(),
              _buildDietTab(),
              _buildMeasurementsTab(),
              _buildProfileTab(),
            ],
          ),
    );
  }

  Widget _buildWorkoutTab() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: _buildGroupedWorkout(),
            ),
          ),
        ),
        _buildAddItemButton('Añadir Ejercicio', () => _showExercisePicker()),
      ],
    );
  }

  List<Widget> _buildGroupedWorkout() {
    if (_userWorkout.isEmpty) return [const Center(child: Padding(padding: EdgeInsets.only(top: 20), child: Text('No hay rutina asignada', style: TextStyle(color: AppTheme.textMuted))))];
    
    Map<String, List<dynamic>> grouped = {};
    for (var ex in _userWorkout) {
      grouped.putIfAbsent(ex['day_of_week'] ?? 'General', () => []).add(ex);
    }
    
    final sortedKeys = grouped.keys.toList()..sort();
    List<Widget> children = [];
    
    for (var day in sortedKeys) {
      children.add(Container(
        margin: const EdgeInsets.only(top: 16, bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            const Icon(LucideIcons.calendar, color: AppTheme.primary, size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(day, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (grouped[day]!.isNotEmpty && grouped[day]!.first['target_muscles'] != null && grouped[day]!.first['target_muscles'].toString().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        "MÚSCULOS: ${grouped[day]!.first['target_muscles'].toString().toUpperCase()}", 
                        style: const TextStyle(fontSize: 12, color: AppTheme.primary, fontWeight: FontWeight.w900, letterSpacing: 0.5)
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ));
      
      final dayExercises = grouped[day]!;
      for (int i = 0; i < dayExercises.length; i++) {
        final ex = dayExercises[i];
        final bool isCombined = (ex['set_type'] == 'BISERIE' || ex['set_type'] == 'TRISERIE');
        
        bool nextIsSame = false;
        bool prevIsSame = false;
        if (isCombined) {
          if (i + 1 < dayExercises.length) nextIsSame = dayExercises[i+1]['set_type'] == ex['set_type'];
          if (i > 0) prevIsSame = dayExercises[i-1]['set_type'] == ex['set_type'];
        }

        children.add(Container(
          margin: EdgeInsets.symmetric(horizontal: isCombined ? 4 : 0),
          decoration: isCombined ? BoxDecoration(
            border: Border(
              left: BorderSide(color: AppTheme.primary.withOpacity(0.5), width: 2),
              right: BorderSide(color: AppTheme.primary.withOpacity(0.5), width: 2),
              top: prevIsSame ? BorderSide.none : BorderSide(color: AppTheme.primary.withOpacity(0.5), width: 2),
              bottom: nextIsSame ? BorderSide.none : BorderSide(color: AppTheme.primary.withOpacity(0.5), width: 2),
            ),
            borderRadius: BorderRadius.vertical(
              top: prevIsSame ? Radius.zero : const Radius.circular(24),
              bottom: nextIsSame ? Radius.zero : const Radius.circular(24),
            ),
            color: AppTheme.primary.withOpacity(0.02),
          ) : null,
          padding: isCombined ? const EdgeInsets.all(4) : EdgeInsets.zero,
          child: Padding(
            padding: EdgeInsets.only(bottom: nextIsSame ? 0 : 12.0),
            child: PremiumCard(
              margin: EdgeInsets.zero,
              child: ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                leading: Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(16)),
                  child: Builder(
                    builder: (context) {
                      final imgUrl = IconMapper.getExerciseImageUrl(ex['name'] ?? '');
                      if (imgUrl != null) {
                        return ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: Image.asset(imgUrl, fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Icon(LucideIcons.dumbbell, color: AppTheme.primary, size: 28),
                          ),
                        );
                      }
                      return Center(child: Text(IconMapper.getExerciseDrawing(ex['name'] ?? '', ex['muscle_group']), style: const TextStyle(fontSize: 28)));
                    },
                  ),
                ),
                title: Text(ex['name'] ?? 'Ejercicio', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${ex['sets']} x ${ex['reps']} | Descanso: ${ex['rest'] ?? '-'}'),
                    if (ex['set_type'] != null && ex['set_type'] != 'NORMAL')
                      Container(
                        margin: const EdgeInsets.only(top: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(4)),
                        child: Text(ex['set_type'], style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.black)),
                      ),
                  ],
                ),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(LucideIcons.edit, color: AppTheme.primary, size: 20),
                      onPressed: () => _editExerciseDetails(ex),
                    ),
                    IconButton(
                      icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
                      onPressed: () async {
                        await ApiService().removeExercise(ex['assignment_id']);
                        _loadAll();
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        ));
      }
    }
    return children;
  }

  List<Widget> _buildGroupedDiet() {
     if (_userDiet.isEmpty) return [const Center(child: Padding(padding: EdgeInsets.only(top: 20), child: Text('No hay dieta asignada', style: TextStyle(color: AppTheme.textMuted))))];
    
    Map<String, Map<String, List<dynamic>>> groupedByDayAndMeal = {};
    for (var food in _userDiet) {
      final dayName = food['day_name'] ?? 'Día 1';
      final mealName = food['meal_name'] ?? 'Comida';
      groupedByDayAndMeal.putIfAbsent(dayName, () => {});
      groupedByDayAndMeal[dayName]!.putIfAbsent(mealName, () => []).add(food);
    }
    
    List<Widget> children = [];
    final sortedDays = groupedByDayAndMeal.keys.toList()..sort();

    for (var day in sortedDays) {
      children.add(Padding(
        padding: const EdgeInsets.only(top: 16, bottom: 8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.2), borderRadius: BorderRadius.circular(8)),
          child: Text(day, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.primary)),
        ),
      ));

      final mealsMap = groupedByDayAndMeal[day]!;
      mealsMap.forEach((mealName, foods) {
        children.add(Padding(
          padding: const EdgeInsets.only(top: 8, bottom: 12),
          child: Row(
            children: [
              const Icon(LucideIcons.clock, color: Colors.white70, size: 16),
              const SizedBox(width: 8),
              Text(mealName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white70)),
            ],
          ),
        ));
        
        children.addAll(foods.map((food) => Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: PremiumCard(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                child: Center(child: Text(IconMapper.getFoodDrawing(food['name'] ?? '', food['category']), style: const TextStyle(fontSize: 20))),
              ),
              title: Text(food['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${food['grams']}g'),
                  Text('${food['calc_kcal']?.toStringAsFixed(0) ?? 0} kcal | P: ${food['calc_protein']?.toStringAsFixed(1) ?? 0}g | C: ${food['calc_carbs']?.toStringAsFixed(1) ?? 0}g | G: ${food['calc_fat']?.toStringAsFixed(1) ?? 0}g', 
                       style: const TextStyle(color: AppTheme.primary, fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(LucideIcons.edit, color: AppTheme.primary, size: 20),
                    onPressed: () => _editFoodDetails(food),
                  ),
                  IconButton(
                    icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
                    onPressed: () async {
                      await ApiService().removeFood(food['assignment_id']);
                      _loadAll();
                    },
                  ),
                ],
              ),
            ),
          ),
        )).toList());
      });
    }
    return children;
  }

  Widget _buildDietTab() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: _buildGroupedDiet(),
            ),
          ),
        ),
        _buildAddItemButton('Añadir Alimento', () => _showFoodPicker()),
      ],
    );
  }

  Widget _buildAddItemButton(String label, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 30),
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: const Icon(LucideIcons.plus, size: 20),
        label: Text(label),
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 54),
        ),
      ),
    );
  }

  void _showExercisePicker() async {
    final catalog = await ApiService().getAdminExercises();
    if (!mounted) return;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.bgColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => _CatalogPicker(
        title: 'Seleccionar Ejercicio',
        items: catalog,
        nameKey: 'name',
        subKey: 'muscle_group',
        onSelected: (item) => _assignExerciseDetails(item),
      ),
    );
  }

  void _showFoodPicker() async {
    final catalog = await ApiService().getAdminFoods();
    if (!mounted) return;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.bgColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => _CatalogPicker(
        title: 'Seleccionar Alimento',
        items: catalog,
        nameKey: 'name',
        subKey: 'category',
        onSelected: (item) => _assignFoodDetails(item),
      ),
    );
  }

  void _assignExerciseDetails(dynamic exercise) {
    final setsController = TextEditingController(text: '3');
    final repsController = TextEditingController(text: '12');
    final musclesController = TextEditingController();
    String selectedDay = 'Lunes';
    final days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    String selectedSetType = 'NORMAL';
    Map<int, dynamic> combinedExercises = {}; // 1 -> ex2, 2 -> ex3

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text('Detalles: ${exercise['name']}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: selectedDay,
                  decoration: const InputDecoration(labelText: 'Día de la semana'),
                  dropdownColor: AppTheme.bgColor,
                  items: days.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                  onChanged: (v) => setDialogState(() => selectedDay = v!),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: musclesController, 
                  decoration: const InputDecoration(
                    labelText: 'Grupos Musculares (Ej: Pecho & Bíceps)',
                    hintText: 'Máximo 2 grupos'
                  )
                ),
                TextField(controller: setsController, decoration: const InputDecoration(labelText: 'Series'), keyboardType: TextInputType.number),
                TextField(controller: repsController, decoration: const InputDecoration(labelText: 'Repeticiones / Mecánica')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedSetType,
                  decoration: const InputDecoration(labelText: 'Técnica / Tipo de Serie'),
                  dropdownColor: AppTheme.bgColor,
                  items: [
                    'NORMAL', 'BISERIE', 'TRISERIE', 'DROPSET', 'ASCENDENTE', 'DESCENDENTE'
                  ].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                  onChanged: (v) => setDialogState(() => selectedSetType = v!),
                ),
                if (selectedSetType == 'BISERIE' || selectedSetType == 'TRISERIE') ...[
                  const SizedBox(height: 16),
                  const Divider(color: AppTheme.primary),
                  Text('EJERCICIOS COMBINADOS', style: TextStyle(color: AppTheme.primary, fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ListTile(
                    title: Text(combinedExercises[1]?['name'] ?? 'Seleccionar 2º Ejercicio'),
                    trailing: const Icon(LucideIcons.plusCircle, color: AppTheme.primary),
                    onTap: () async {
                      final catalog = await ApiService().getAdminExercises();
                      if (!context.mounted) return;
                      showModalBottomSheet(
                        context: context,
                        backgroundColor: AppTheme.bgColor,
                        builder: (ctx) => _CatalogPicker(
                          title: '2º Ejercicio',
                          items: catalog,
                          nameKey: 'name',
                          subKey: 'muscle_group',
                          onSelected: (item) {
                            setDialogState(() => combinedExercises[1] = item);
                            Navigator.pop(ctx);
                          },
                        ),
                      );
                    },
                  ),
                  if (selectedSetType == 'TRISERIE')
                    ListTile(
                      title: Text(combinedExercises[2]?['name'] ?? 'Seleccionar 3º Ejercicio'),
                      trailing: const Icon(LucideIcons.plusCircle, color: AppTheme.primary),
                      onTap: () async {
                        final catalog = await ApiService().getAdminExercises();
                        if (!context.mounted) return;
                        showModalBottomSheet(
                          context: context,
                          backgroundColor: AppTheme.bgColor,
                          builder: (ctx) => _CatalogPicker(
                            title: '3º Ejercicio',
                            items: catalog,
                            nameKey: 'name',
                            subKey: 'muscle_group',
                            onSelected: (item) {
                              setDialogState(() => combinedExercises[2] = item);
                              Navigator.pop(ctx);
                            },
                          ),
                        );
                      },
                    ),
                ],
                if (['DROPSET', 'ASCENDENTE', 'DESCENDENTE'].contains(selectedSetType))
                   const Padding(
                     padding: EdgeInsets.only(top: 8.0),
                     child: Text('Hint: Indica 3 pesos en el campo Reps (ej: 40-30-20kg)', style: TextStyle(color: AppTheme.textMuted, fontSize: 11)),
                   ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            ElevatedButton(
              onPressed: () async {
                try {
                  // Primary Exercise
                  await ApiService().assignExercise(
                    widget.userId, exercise['id'], selectedDay, int.parse(setsController.text), repsController.text,
                    targetMuscles: musclesController.text, setType: selectedSetType,
                  );
                  
                  // Combined Exercises
                  if (combinedExercises.containsKey(1)) {
                    await ApiService().assignExercise(
                      widget.userId, combinedExercises[1]['id'], selectedDay, int.parse(setsController.text), repsController.text,
                      targetMuscles: musclesController.text, setType: selectedSetType,
                    );
                  }
                  if (selectedSetType == 'TRISERIE' && combinedExercises.containsKey(2)) {
                    await ApiService().assignExercise(
                      widget.userId, combinedExercises[2]['id'], selectedDay, int.parse(setsController.text), repsController.text,
                      targetMuscles: musclesController.text, setType: selectedSetType,
                    );
                  }
                  
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bloque de ejercicios asignado con éxito')));
                  Navigator.pop(context);
                  _loadAll();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error al asignar: $e')));
                }
              },
              child: const Text('Asignar Bloque'),
            ),
          ],
        ),
      ),
    );
  }

  void _assignFoodDetails(dynamic food) {
    String selectedDay = 'Día 1';
    final dietDays = ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'];
    
    final mealController = TextEditingController(text: 'Desayuno');
    final gramsController = TextEditingController(text: '100');

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text('Detalles: ${food['name']}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selectedDay,
                decoration: const InputDecoration(labelText: 'Día de Dieta'),
                dropdownColor: AppTheme.bgColor,
                items: dietDays.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                onChanged: (v) => setDialogState(() => selectedDay = v!),
              ),
              const SizedBox(height: 12),
              TextField(controller: mealController, decoration: const InputDecoration(labelText: 'Comida (Ej: Almuerzo)')),
              TextField(controller: gramsController, decoration: const InputDecoration(labelText: 'Gramos'), keyboardType: TextInputType.number),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            ElevatedButton(
              onPressed: () async {
                try {
                  await ApiService().assignFood(
                    widget.userId,
                    food['id'],
                    selectedDay,
                    mealController.text,
                    double.parse(gramsController.text),
                  );
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Alimento asignado con éxito')));
                  Navigator.pop(context);
                  _loadAll();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
                }
              },
              child: const Text('Asignar'),
            ),
          ],
        ),
      ),
    );
  }
  void _editExerciseDetails(dynamic ex) {
    final setsController = TextEditingController(text: ex['sets']?.toString() ?? '3');
    final repsController = TextEditingController(text: ex['reps']?.toString() ?? '');
    final musclesController = TextEditingController(text: ex['target_muscles']?.toString() ?? '');
    String selectedSetType = ex['set_type'] ?? 'NORMAL';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text('Editar: ${ex['name']}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: musclesController, 
                  decoration: const InputDecoration(labelText: 'Grupos Musculares')
                ),
                TextField(controller: setsController, decoration: const InputDecoration(labelText: 'Series'), keyboardType: TextInputType.number),
                TextField(controller: repsController, decoration: const InputDecoration(labelText: 'Repeticiones')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedSetType,
                  decoration: const InputDecoration(labelText: 'Técnica'),
                  dropdownColor: AppTheme.bgColor,
                  items: ['NORMAL', 'BISERIE', 'TRISERIE', 'DROPSET', 'ASCENDENTE', 'DESCENDENTE']
                      .map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                  onChanged: (v) => setDialogState(() => selectedSetType = v!),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            ElevatedButton(
              onPressed: () async {
                await ApiService().updateExercise(ex['assignment_id'], {
                  'sets': setsController.text,
                  'reps': repsController.text,
                  'target_muscles': musclesController.text,
                  'set_type': selectedSetType,
                });
                if (!mounted) return;
                Navigator.pop(context);
                _loadAll();
              },
              child: const Text('Guardar Cambios'),
            ),
          ],
        ),
      ),
    );
  }

  void _editFoodDetails(dynamic food) {
    final mealController = TextEditingController(text: food['meal_name'] ?? 'Comida');
    final gramsController = TextEditingController(text: food['grams']?.toString() ?? '100');
    String selectedDay = food['day_name'] ?? 'Día 1';
    final dietDays = ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'];

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text('Editar: ${food['name']}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selectedDay,
                decoration: const InputDecoration(labelText: 'Día de Dieta'),
                dropdownColor: AppTheme.bgColor,
                items: dietDays.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                onChanged: (v) => setDialogState(() => selectedDay = v!),
              ),
              const SizedBox(height: 12),
              TextField(controller: mealController, decoration: const InputDecoration(labelText: 'Comida (Ej: Almuerzo)')),
              TextField(controller: gramsController, decoration: const InputDecoration(labelText: 'Gramos'), keyboardType: TextInputType.number),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            ElevatedButton(
              onPressed: () async {
                await ApiService().updateFood(food['assignment_id'], {
                    'meal_name': mealController.text,
                    'grams': double.parse(gramsController.text),
                    'day_name': selectedDay,
                });
                if (!mounted) return;
                Navigator.pop(context);
                _loadAll();
              },
              child: const Text('Guardar Cambios'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMeasurementsTab() {
    if (_userMeasurements.isEmpty) {
      return const Center(child: Text('No hay registros de medidas aún.', style: TextStyle(color: AppTheme.textMuted)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: _userMeasurements.length,
      itemBuilder: (context, index) {
        final m = _userMeasurements[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: PremiumCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(m['date'] ?? '-', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
                    const Icon(LucideIcons.calendar, size: 16, color: AppTheme.textMuted),
                  ],
                ),
                const Divider(height: 24, color: AppTheme.border),
                Wrap(
                  spacing: 20,
                  runSpacing: 12,
                  children: [
                    _buildMeasureTag('Peso', '${m['weight']} kg'),
                    _buildMeasureTag('Cintura', '${m['waist']} cm'),
                    _buildMeasureTag('Pecho', '${m['chest']} cm'),
                    _buildMeasureTag('Cadera', '${m['hip']} cm'),
                    _buildMeasureTag('Muslo', '${m['thigh']} cm'),
                    _buildMeasureTag('Bíceps', '${m['biceps']} cm'),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildMeasureTag(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, 
             style: const TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold)),
        Text(value, 
             style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
      ],
    );
  }

  Widget _buildProfileTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_userMeasurements.length >= 2) ...[
            const Text('EVOLUCIÓN DE PESO',
                style:
                    TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
            const SizedBox(height: 16),
            _buildWeightChart(),
            const SizedBox(height: 32),
          ],
          const Text('DATOS DEL ATLETA',
              style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
          const SizedBox(height: 16),
          PremiumCard(
            padding: 20,
            child: Column(
              children: [
                _buildProfileRow('Nombre completo', widget.userName),
                const Divider(height: 24),
                const Text(
                    'Solicitar al alumno que complete su perfil para ver más datos biométricos.',
                    style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
              ],
            ),
          ),
          const SizedBox(height: 32),
          if (_userReports.isNotEmpty) ...[
             const Text('HISTORIAL DE REPORTES / FOTOS', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
             const SizedBox(height: 16),
             _buildReportsHistory(),
          ],
        ],
      ),
    );
  }

  Widget _buildReportsHistory() {
    final baseUrl = ApiService.baseUrl.replaceAll('/api/', '/');
    return Column(
      children: _userReports.map<Widget>((report) {
        return PremiumCard(
          margin: const EdgeInsets.only(bottom: 16),
          padding: 16,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Reporte ${report['date'].toString().split('T')[0]}',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('${report['weight']} kg',
                      style: const TextStyle(
                          color: AppTheme.primary, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  if (report['photo_front'] != null)
                    Expanded(
                        child: _buildReportThumb(
                            baseUrl + 'uploads/' + report['photo_front'])),
                  if (report['photo_side'] != null) ...[
                    const SizedBox(width: 8),
                    Expanded(
                        child: _buildReportThumb(
                            baseUrl + 'uploads/' + report['photo_side']))
                  ],
                  if (report['photo_back'] != null) ...[
                    const SizedBox(width: 8),
                    Expanded(
                        child: _buildReportThumb(
                            baseUrl + 'uploads/' + report['photo_back']))
                  ],
                ],
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildReportThumb(String url) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Image.network(url, height: 120, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Icon(LucideIcons.image, color: AppTheme.textMuted)),
    );
  }

  Widget _buildWeightChart() {
    return Container(
      height: 200,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: LineChart(
        LineChartData(
          gridData: const FlGridData(show: false),
          titlesData: const FlTitlesData(show: false),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: _userMeasurements.asMap().entries.map((e) {
                return FlSpot(
                    e.key.toDouble(), (e.value['weight'] as num).toDouble());
              }).toList(),
              isCurved: true,
              color: AppTheme.primary,
              barWidth: 4,
              dotData: const FlDotData(show: true),
              belowBarData:
                  BarAreaData(show: true, color: AppTheme.primary.withOpacity(0.1)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: AppTheme.textMuted)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class _CatalogPicker extends StatefulWidget {
  final String title;
  final List<dynamic> items;
  final String nameKey;
  final String subKey;
  final Function(dynamic) onSelected;

  const _CatalogPicker({
    required this.title,
    required this.items,
    required this.nameKey,
    required this.subKey,
    required this.onSelected,
  });

  @override
  State<_CatalogPicker> createState() => _CatalogPickerState();
}

class _CatalogPickerState extends State<_CatalogPicker> {
  String _query = '';

  void _createNewItem() async {
    final title = widget.title.contains('Ejercicio') ? 'Nuevo Ejercicio' : 'Nuevo Alimento';
    final nameController = TextEditingController();
    final subController = TextEditingController(); // muscle group or category
    
    // For food only
    final kcalController = TextEditingController(text: '0');
    final pController = TextEditingController(text: '0');
    final cController = TextEditingController(text: '0');
    final fController = TextEditingController(text: '0');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: Text(title),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Nombre')),
              TextField(controller: subController, decoration: InputDecoration(labelText: widget.title.contains('Ejercicio') ? 'Grupo Muscular' : 'Categoría')),
              if (widget.title.contains('Alimento')) ...[
                Row(
                  children: [
                    Expanded(child: TextField(controller: kcalController, decoration: const InputDecoration(labelText: 'Kcal/100g'), keyboardType: TextInputType.number)),
                    const SizedBox(width: 8),
                    Expanded(child: TextField(controller: pController, decoration: const InputDecoration(labelText: 'Prot/100g'), keyboardType: TextInputType.number)),
                  ],
                ),
                Row(
                  children: [
                    Expanded(child: TextField(controller: cController, decoration: const InputDecoration(labelText: 'Carbs/100g'), keyboardType: TextInputType.number)),
                    const SizedBox(width: 8),
                    Expanded(child: TextField(controller: fController, decoration: const InputDecoration(labelText: 'Grasas/100g'), keyboardType: TextInputType.number)),
                  ],
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              try {
                if (widget.title.contains('Ejercicio')) {
                  await ApiService().addToExerciseCatalog(nameController.text, subController.text);
                } else {
                  await ApiService().addToFoodCatalog({
                    'name': nameController.text,
                    'category': subController.text,
                    'kcal': double.parse(kcalController.text),
                    'protein': double.parse(pController.text),
                    'carbs': double.parse(cController.text),
                    'fat': double.parse(fController.text),
                  });
                }
                if (!mounted) return;
                Navigator.pop(context); // Close dialog
                Navigator.pop(context); // Close picker
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Añadido al catálogo. Vuelve a abrir para ver.'), backgroundColor: Colors.green));
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
              }
            },
            child: const Text('Crear'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filtered = widget.items.where((item) {
      return item[widget.nameKey].toString().toLowerCase().contains(_query.toLowerCase()) ||
             item[widget.subKey].toString().toLowerCase().contains(_query.toLowerCase());
    }).toList();

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        height: MediaQuery.of(context).size.height * 0.7,
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(widget.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                IconButton(icon: const Icon(LucideIcons.x), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              decoration: const InputDecoration(
                hintText: 'Buscar...',
                prefixIcon: Icon(LucideIcons.search, size: 20),
              ),
              onChanged: (v) => setState(() => _query = v),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => _createNewItem(),
              icon: const Icon(LucideIcons.plusCircle, size: 20),
              label: Text('Crear nuevo ${widget.title.contains('Ejercicio') ? 'ejercicio' : 'alimento'}'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppTheme.primary,
                side: const BorderSide(color: AppTheme.primary),
                minimumSize: const Size(double.infinity, 44),
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: filtered.length,
                itemBuilder: (context, index) {
                  final item = filtered[index];
                  return ListTile(
                    contentPadding: const EdgeInsets.symmetric(vertical: 4),
                    onTap: () => widget.onSelected(item),
                    leading: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                      child: Builder(
                        builder: (context) {
                          if (widget.title.contains('Ejercicio')) {
                            return Center(child: Text(IconMapper.getExerciseDrawing(item[widget.nameKey] ?? '', item[widget.subKey]), style: const TextStyle(fontSize: 24)));
                          }
                          return Center(child: Text(IconMapper.getFoodDrawing(item[widget.nameKey] ?? '', item[widget.subKey]), style: const TextStyle(fontSize: 24)));
                        },
                      ),
                    ),
                    title: Text(item[widget.nameKey] ?? '-', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    subtitle: Text(item[widget.subKey]?.toString().toUpperCase() ?? '-', style: const TextStyle(color: AppTheme.primary, fontSize: 11, fontWeight: FontWeight.bold)),
                    trailing: widget.title.contains('Ejercicio') ? IconButton(
                      icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
                      onPressed: () async {
                        final confirm = await showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            backgroundColor: AppTheme.surface,
                            title: const Text('Eliminar definitivamente?'),
                            content: Text('¿Deseas eliminar "${item[widget.nameKey]}" del catálogo maestro?'),
                            actions: [
                              TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
                              ElevatedButton(onPressed: () => Navigator.pop(context, true), style: ElevatedButton.styleFrom(backgroundColor: Colors.red), child: const Text('Eliminar')),
                            ],
                          ),
                        );
                        if (confirm == true) {
                          await ApiService().deleteCatalogExercise(item['id']);
                          if (!mounted) return;
                          Navigator.pop(context); // Close picker
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Eliminado permanentemente.')));
                        }
                      },
                    ) : null,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
