import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../widgets/premium_card.dart';
import '../services/api_service.dart';
import '../utils/icon_mapper.dart';

class WorkoutScreen extends StatefulWidget {
  const WorkoutScreen({super.key});

  @override
  State<WorkoutScreen> createState() => _WorkoutScreenState();
}

class _WorkoutScreenState extends State<WorkoutScreen> {
  bool _isLoading = true;
  List<dynamic> _exercises = [];
  final Set<int> _completedAssignmentIds = {};
  final Map<int, List<TextEditingController>> _weightControllers = {};

  @override
  void initState() {
    super.initState();
    _loadWorkout();
  }

  Future<void> _loadWorkout() async {
    try {
      final workoutData = await ApiService().getWorkoutPlan();
      final statusData = await ApiService().getWorkoutStatus(DateTime.now());
      setState(() {
        _exercises = workoutData;
        _completedAssignmentIds.clear();
        _completedAssignmentIds.addAll(statusData);
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  void _toggleComplete(int assignmentId, dynamic ex) async {
     final bool currentlyDone = _completedAssignmentIds.contains(assignmentId);
     
     List<Map<String, dynamic>> weightLogs = [];
     if (!currentlyDone) {
       final controllers = _weightControllers[assignmentId];
       if (controllers != null) {
         for (int i = 0; i < controllers.length; i++) {
           final w = double.tryParse(controllers[i].text) ?? 0.0;
           weightLogs.add({'set': i + 1, 'weight': w});
         }
       }
     }

     setState(() {
       if (currentlyDone) {
         _completedAssignmentIds.remove(assignmentId);
       } else {
         _completedAssignmentIds.add(assignmentId);
       }
     });

     try {
       await ApiService().toggleWorkoutLog(assignmentId, !currentlyDone, logs: weightLogs);
     } catch (e) {
       // Rollback on error
       setState(() {
         if (currentlyDone) _completedAssignmentIds.add(assignmentId);
         else _completedAssignmentIds.remove(assignmentId);
       });
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Rutina Diaria'),
        leading: Navigator.of(context).canPop() 
           ? IconButton(icon: const Icon(LucideIcons.chevronLeft), onPressed: () => Navigator.of(context).pop())
           : null,
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
        : _exercises.isEmpty
          ? _buildEmptyState()
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: _buildGroupedExercises(),
              ),
            ),
    );
  }

  List<Widget> _buildGroupedExercises() {
    Map<String, List<dynamic>> grouped = {};
    for (int i = 0; i < _exercises.length; i++) {
        final ex = _exercises[i];
        final day = ex['day_of_week'] ?? 'Día 1';
        grouped.putIfAbsent(day, () => []).add({'data': ex, 'originalIndex': i});
    }

    // Sort by day if possible (Día 1, Día 2...)
    final sortedKeys = grouped.keys.toList()..sort((a, b) => a.compareTo(b));

    List<Widget> children = [];
    for (var day in sortedKeys) {
      children.add(Container(
        margin: const EdgeInsets.only(top: 12, bottom: 20),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [AppTheme.primary.withOpacity(0.2), Colors.transparent],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(10)),
              child: const Icon(LucideIcons.calendar, color: Colors.black, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(day, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (grouped[day]!.isNotEmpty && grouped[day]!.first['data']['target_muscles'] != null && grouped[day]!.first['data']['target_muscles'].toString().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        grouped[day]!.first['data']['target_muscles'].toString().toUpperCase(), 
                        style: const TextStyle(fontSize: 12, color: AppTheme.primary, fontWeight: FontWeight.w800, letterSpacing: 1.1)
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ));

      final dayItems = grouped[day]!;
      for (int i = 0; i < dayItems.length; i++) {
        final item = dayItems[i];
        final ex = item['data'];
        final assignmentId = ex['id'] ?? 0;
        final isDone = _completedAssignmentIds.contains(assignmentId);
        
        final bool isCombined = (ex['set_type'] == 'BISERIE' || ex['set_type'] == 'TRISERIE');
        
        // Cordon Logic: Check position in the block
        bool nextIsSame = false;
        bool prevIsSame = false;
        if (isCombined) {
          if (i + 1 < dayItems.length) nextIsSame = dayItems[i+1]['data']['set_type'] == ex['set_type'];
          if (i > 0) prevIsSame = dayItems[i-1]['data']['set_type'] == ex['set_type'];
        }

        // Initialize controllers for this assignment if not exists
        if (!_weightControllers.containsKey(assignmentId)) {
          String setsStr = ex['sets'].toString();
          int setsCount = 1;
          if (setsStr.contains('-')) {
            setsCount = int.tryParse(setsStr.split('-').last.trim()) ?? 1;
          } else {
            setsCount = int.tryParse(setsStr) ?? 1;
          }
          _weightControllers[assignmentId] = List.generate(setsCount, (_) => TextEditingController());
        }
        final controllers = _weightControllers[assignmentId];

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
            padding: EdgeInsets.only(bottom: nextIsSame ? 0 : 16.0),
            child: PremiumCard(
              padding: 0,
              margin: EdgeInsets.zero,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Column(
                  children: [
                    InkWell(
                      onTap: () => _showExerciseDetails(context, ex),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isDone ? Colors.green.withOpacity(0.05) : Colors.transparent,
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 60,
                              height: 60,
                              decoration: BoxDecoration(
                                color: isDone ? Colors.green.withOpacity(0.2) : AppTheme.primary.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: isDone
                                ? const Icon(LucideIcons.check, color: Colors.green, size: 28)
                                : ClipRRect(
                                    borderRadius: BorderRadius.circular(16),
                                    child: ex['icon_path'] != null 
                                      ? Image.network(
                                          '${ApiService.uploadsUrl}exercises/${ex['icon_path']}',
                                          height: 60,
                                          width: 60,
                                          fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => Center(
                                            child: Text(
                                              IconMapper.getExerciseDrawing(ex['name'] ?? '', ex['muscle_group']),
                                              style: const TextStyle(fontSize: 28)
                                            ),
                                          ),
                                        )
                                      : Center(
                                          child: Text(
                                            IconMapper.getExerciseDrawing(ex['name'] ?? '', ex['muscle_group']),
                                            style: const TextStyle(fontSize: 28)
                                          ),
                                        ),
                                  ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    ex['name'] ?? 'Ejercicio',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold, 
                                      fontSize: 16,
                                      decoration: isDone ? TextDecoration.lineThrough : null,
                                      color: isDone ? AppTheme.textMuted : Colors.white,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Row(
                                    children: [
                                      _buildInfoChip(LucideIcons.repeat, '${ex['sets']} series'),
                                      const SizedBox(width: 12),
                                      _buildInfoChip(LucideIcons.zap, '${ex['reps']} reps'),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            Checkbox(
                              value: isDone, 
                              onChanged: (v) => _toggleComplete(assignmentId, ex),
                              activeColor: Colors.green,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text("REGISTRO DE PESOS POR SERIE", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.primary, letterSpacing: 1.1)),
                              if (isDone) const Text("COMPLETADO", style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.green)),
                            ],
                          ),
                          const SizedBox(height: 12),
                          SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: List.generate(controllers!.length, (index) {
                                return Container(
                                  width: 75,
                                  margin: const EdgeInsets.only(right: 10),
                                  child: TextField(
                                    controller: controllers[index],
                                    keyboardType: TextInputType.number,
                                    enabled: !isDone,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      fontSize: 14, 
                                      fontWeight: FontWeight.w900,
                                      color: isDone ? Colors.green : Colors.white
                                    ),
                                    decoration: InputDecoration(
                                      labelText: 'Serie ${index + 1}',
                                      labelStyle: TextStyle(fontSize: 10, color: isDone ? Colors.green : AppTheme.primary),
                                      hintText: '0',
                                      suffixText: 'kg',
                                      suffixStyle: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                                      filled: true,
                                      fillColor: isDone ? Colors.green.withOpacity(0.05) : Colors.white.withOpacity(0.03),
                                      contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12), 
                                        borderSide: BorderSide(color: isDone ? Colors.green.withOpacity(0.3) : AppTheme.primary.withOpacity(0.2))
                                      ),
                                      disabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12), 
                                        borderSide: BorderSide(color: Colors.green.withOpacity(0.5))
                                      ),
                                    ),
                                  ),
                                );
                              }),
                            ),
                          ),
                        ],
                      ),
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

  Widget _buildInfoChip(IconData icon, String label) {
    return Row(
      children: [
        Icon(icon, size: 12, color: AppTheme.textMuted),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 11, fontWeight: FontWeight.w500)),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(LucideIcons.dumbbell, size: 64, color: AppTheme.border),
          const SizedBox(height: 16),
          const Text('Aún no tienes rutina asignada', style: TextStyle(color: AppTheme.textMuted, fontSize: 18)),
          const SizedBox(height: 8),
          const Text('Habla con tu coach para empezar.', style: TextStyle(color: AppTheme.textMuted, fontSize: 14)),
        ],
      ),
    );
  }

  void _showExerciseDetails(BuildContext context, dynamic ex) {
    final imgUrl = IconMapper.getExerciseImageUrl(ex['name'] ?? '', ex['muscle_group']);

    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgColor,
      isScrollControlled: true,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      builder: (context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 40, height: 4, decoration: BoxDecoration(color: AppTheme.border, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 24),
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.asset(
                imgUrl ?? 'assets/images/logo.png', // Logo as absolute fallback
                height: 250,
                width: double.infinity,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const Icon(LucideIcons.image, size: 100, color: AppTheme.border),
              ),
            ),
            const SizedBox(height: 32),
            Text(ex['name'] ?? 'Ejercicio', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
            if (ex['set_type'] != null && ex['set_type'] != 'NORMAL') ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(8)),
                child: Text(ex['set_type'], style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.black)),
              ),
            ],
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
              decoration: BoxDecoration(color: AppTheme.surface, borderRadius: BorderRadius.circular(12)),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildDetailStat(LucideIcons.repeat, '${ex['sets']} Series'),
                  Container(width: 1, height: 30, color: AppTheme.border),
                  _buildDetailStat(LucideIcons.zap, '${ex['reps']} Reps'),
                  Container(width: 1, height: 30, color: AppTheme.border),
                  _buildDetailStat(LucideIcons.timer, ex['rest'] ?? '1 min'),
                ],
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 54), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
              child: const Text('Entendido', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailStat(IconData icon, String label) {
    return Column(
      children: [
        Icon(icon, color: AppTheme.primary, size: 20),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
