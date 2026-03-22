import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
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
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => _isLoading = true);
    try {
      final workout = await ApiService().getWorkoutPlan(userId: widget.userId);
      final diet = await ApiService().getDietPlan(userId: widget.userId);
      final measurements = await ApiService().getMeasurements(widget.userId);
      setState(() {
        _userWorkout = workout;
        _userDiet = diet;
        _userMeasurements = measurements;
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
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textMuted,
          tabs: const [
            Tab(icon: Icon(LucideIcons.dumbbell), text: 'Rutina'),
            Tab(icon: Icon(LucideIcons.utensils), text: 'Dieta'),
            Tab(icon: Icon(LucideIcons.lineChart), text: 'Medidas'),
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
      
      children.addAll(grouped[day]!.map((ex) => Padding(
        padding: const EdgeInsets.only(bottom: 12.0),
        child: PremiumCard(
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
              child: Builder(
                builder: (context) {
                  final imgUrl = IconMapper.getExerciseImageUrl(ex['name'] ?? '');
                  if (imgUrl != null) {
                    return ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.network(imgUrl, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Icon(LucideIcons.dumbbell, color: AppTheme.primary)),
                    );
                  }
                  return Center(child: Text(IconMapper.getExerciseDrawing(ex['name'] ?? '', ex['muscle_group']), style: const TextStyle(fontSize: 20)));
                },
              ),
            ),
            title: Text(ex['name'] ?? 'Ejercicio', style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text('${ex['sets']} x ${ex['reps']} | Descanso: ${ex['rest'] ?? '-'}'),
            trailing: IconButton(
              icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
              onPressed: () async {
                await ApiService().removeExercise(ex['assignment_id']);
                _loadAll();
              },
            ),
          ),
        ),
      )).toList());
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
              trailing: IconButton(
                icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
                onPressed: () async {
                  await ApiService().removeFood(food['assignment_id']);
                  _loadAll();
                },
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
                TextField(controller: repsController, decoration: const InputDecoration(labelText: 'Repeticiones')),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            ElevatedButton(
              onPressed: () async {
                await ApiService().assignExercise(
                  widget.userId,
                  exercise['id'],
                  selectedDay,
                  int.parse(setsController.text),
                  repsController.text,
                  targetMuscles: musclesController.text,
                );
                Navigator.pop(context);
                _loadAll();
              },
              child: const Text('Asignar'),
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
                await ApiService().assignFood(
                  widget.userId,
                  food['id'],
                  selectedDay,
                  mealController.text,
                  double.parse(gramsController.text),
                );
                Navigator.pop(context);
                _loadAll();
              },
              child: const Text('Asignar'),
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
        Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
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
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: filtered.length,
                itemBuilder: (context, index) {
                  final item = filtered[index];
                  return ListTile(
                    contentPadding: const EdgeInsets.symmetric(vertical: 4),
                    leading: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                      child: Builder(
                        builder: (context) {
                          if (widget.title.contains('Ejercicio')) {
                            final imgUrl = IconMapper.getExerciseImageUrl(item[widget.nameKey] ?? '');
                            if (imgUrl != null) {
                              return ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: Image.network(imgUrl, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Icon(LucideIcons.dumbbell)),
                              );
                            }
                            return Center(child: Text(IconMapper.getExerciseDrawing(item[widget.nameKey] ?? '', item[widget.subKey]), style: const TextStyle(fontSize: 24)));
                          }
                          return Center(child: Text(IconMapper.getFoodDrawing(item[widget.nameKey] ?? '', item[widget.subKey]), style: const TextStyle(fontSize: 24)));
                        },
                      ),
                    ),
                    title: Text(item[widget.nameKey]),
                    subtitle: Text(item[widget.subKey], style: const TextStyle(color: AppTheme.textMuted)),
                    onTap: () {
                      Navigator.pop(context);
                      widget.onSelected(item);
                    },
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
