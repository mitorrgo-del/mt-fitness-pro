import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../widgets/premium_card.dart';
import '../services/api_service.dart';
import '../utils/icon_mapper.dart';

class DietScreen extends StatefulWidget {
  const DietScreen({super.key});

  @override
  State<DietScreen> createState() => _DietScreenState();
}

class _DietScreenState extends State<DietScreen> {
  bool _isLoading = true;
  List<dynamic> _meals = [];
  double _totalKcal = 0;
  double _totalProtein = 0;
  double _totalCarbs = 0;
  double _totalFat = 0;

  @override
  void initState() {
    super.initState();
    _loadDiet();
  }

  Future<void> _loadDiet() async {
    try {
      final data = await ApiService().getDietPlan();
      double kcal = 0, p = 0, c = 0, f = 0;
      for (var item in data) {
        kcal += (item['calc_kcal'] ?? 0).toDouble();
        p += (item['calc_protein'] ?? 0).toDouble();
        c += (item['calc_carbs'] ?? 0).toDouble();
        f += (item['calc_fat'] ?? 0).toDouble();
      }
      setState(() {
        _meals = data;
        _totalKcal = kcal;
        _totalProtein = p;
        _totalCarbs = c;
        _totalFat = f;
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
        title: const Text('Mi Plan Nutricional'),
        automaticallyImplyLeading: false,
        leading: Navigator.of(context).canPop() 
           ? IconButton(icon: const Icon(LucideIcons.chevronLeft), onPressed: () => Navigator.of(context).pop())
           : null,
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
        : SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Alimentación Inteligente',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  'Objetivo diario: ${_totalKcal.toStringAsFixed(0)} kcal',
                  style: const TextStyle(color: AppTheme.textMuted, fontSize: 14),
                ),
                const SizedBox(height: 24),
                
                // Macros summary
                Row(
                  children: [
                    Expanded(child: _MacroChip(label: 'Proteínas', value: '${_totalProtein.toStringAsFixed(0)}g', color: Colors.blue)),
                    const SizedBox(width: 8),
                    Expanded(child: _MacroChip(label: 'Carbos', value: '${_totalCarbs.toStringAsFixed(0)}g', color: Colors.orange)),
                    const SizedBox(width: 8),
                    Expanded(child: _MacroChip(label: 'Grasas', value: '${_totalFat.toStringAsFixed(0)}g', color: Colors.green)),
                  ],
                ),
                
                const SizedBox(height: 32),
                const Text('Tu Menú Personalizado', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                
                ..._buildGroupedMeals(),
              ],
            ),
          ),
    );
  }

  List<Widget> _buildGroupedMeals() {
    if (_meals.isEmpty) {
      return [const Center(child: Padding(padding: EdgeInsets.only(top: 20), child: Text('Consulta con tu Coach para asignar tu dieta.', style: TextStyle(color: AppTheme.textMuted))))];
    }
    
    // Grouping: Day Name -> Meal Name -> List of Foods
    Map<String, Map<String, List<dynamic>>> groupedByDayAndMeal = {};
    
    for (var m in _meals) {
      final dayName = m['day_name'] ?? 'Día 1';
      final mealName = m['meal_name'] ?? 'Comida';
      
      groupedByDayAndMeal.putIfAbsent(dayName, () => {});
      groupedByDayAndMeal[dayName]!.putIfAbsent(mealName, () => []).add(m);
    }

    List<Widget> children = [];
    final sortedDays = groupedByDayAndMeal.keys.toList()..sort();

    for (var day in sortedDays) {
      // 1. Day Header
      children.add(Padding(
        padding: const EdgeInsets.only(top: 16, bottom: 8),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppTheme.primary.withOpacity(0.15), 
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              const Icon(LucideIcons.calendar, color: AppTheme.primary, size: 22),
              const SizedBox(width: 10),
              Text(day, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.primary)),
            ],
          ),
        ),
      ));

      final mealsMap = groupedByDayAndMeal[day]!;
      
      // 2. Meal Header and Items
      mealsMap.forEach((mealName, foods) {
        children.add(Padding(
          padding: const EdgeInsets.only(top: 12, bottom: 12, left: 8),
          child: Row(
            children: [
              const Icon(LucideIcons.clock, color: Colors.white70, size: 18),
              const SizedBox(width: 8),
              Text(mealName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white70)),
            ],
          ),
        ));
        
        children.addAll(foods.map((food) => _buildMealCard(
          food['name'],
          '${food['grams']}g',
          '${food['calc_kcal']?.toStringAsFixed(0) ?? 0} kcal | P: ${food['calc_protein']?.toStringAsFixed(1) ?? 0}g | C: ${food['calc_carbs']?.toStringAsFixed(1) ?? 0}g | G: ${food['calc_fat']?.toStringAsFixed(1) ?? 0}g',
          IconMapper.getFoodDrawing(food['name'], food['category']),
        )).toList());
        
        children.add(const SizedBox(height: 8));
      });
    }
    
    return children;
  }

  Widget _buildMealCard(String title, String description, String macros, String iconText) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: PremiumCard(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
              child: Center(child: Text(iconText, style: const TextStyle(fontSize: 20))),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 4),
                  Text(description, style: const TextStyle(color: AppTheme.textMuted, fontSize: 14)),
                  const SizedBox(height: 4),
                  Text(macros, style: const TextStyle(color: AppTheme.primary, fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MacroChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _MacroChip({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 18)),
          Text(label, style: TextStyle(color: color.withOpacity(0.7), fontSize: 10, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
