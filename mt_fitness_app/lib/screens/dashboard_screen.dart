import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../widgets/premium_card.dart';
import 'chat_screen.dart';
import 'workout_screen.dart';
import 'diet_screen.dart';
import 'profile_screen.dart';
import 'admin_users_screen.dart';
import '../services/api_service.dart';
import 'admin_plan_editor.dart';
import 'admin_social_screen.dart';
import 'report_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  final List<Widget> _pages;

  _DashboardScreenState() : _pages = [] {
    _pages.addAll([
      DashboardHome(onNavigate: _onTabTapped),
      const ChatScreen(),
      const WorkoutScreen(),
      const DietScreen(),
      const ProfileScreen(),
    ]);
  }

  void _onTabTapped(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: AppTheme.border, width: 0.5)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex >= 5 ? 0 : _currentIndex, // Safety check
          onTap: (index) {
            setState(() => _currentIndex = index);
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: AppTheme.bgColor,
          selectedItemColor: AppTheme.primary,
          unselectedItemColor: AppTheme.textMuted,
          showSelectedLabels: true,
          showUnselectedLabels: true,
          items: const [
            BottomNavigationBarItem(icon: Icon(LucideIcons.home, size: 20), label: 'Inicio'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.messageCircle, size: 20), label: 'Chat'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.dumbbell, size: 20), label: 'Entreno'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.utensils, size: 20), label: 'Dieta'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.user, size: 20), label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}

class DashboardHome extends StatefulWidget {
  final Function(int) onNavigate;
  const DashboardHome({super.key, required this.onNavigate});

  @override
  State<DashboardHome> createState() => _DashboardHomeState();
}

class _DashboardHomeState extends State<DashboardHome> {
  bool _isLoadingData = true;
  String _todayRoutine = 'Descanso';
  List<dynamic> _todayExercises = [];
  Map<String, dynamic>? _lastMeasurement;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    try {
      final workout = await ApiService().getWorkoutPlan();
      final measurements = await ApiService().getMeasurements(ApiService().userId ?? '');
      
      final now = DateTime.now();
      final days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
      final todayName = days[now.weekday - 1];
      final todayPlans = workout.where((e) => e['day_of_week'] == todayName).toList();

      setState(() {
        if (todayPlans.isNotEmpty) {
           _todayRoutine = todayPlans.first['target_muscles'] ?? todayPlans.map((e) => e['muscle_group']).toSet().join(' & ');
           _todayExercises = todayPlans;
        } else {
           _todayRoutine = 'Descanso';
           _todayExercises = [];
        }
        if (measurements.isNotEmpty) {
           _lastMeasurement = measurements.last;
        }
        _isLoadingData = false;
      });
    } catch (e) {
      if (mounted) setState(() => _isLoadingData = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final userName = ApiService().userName?.split(' ')[0] ?? 'Guerrero';
    final isCoach = ApiService().isCoach;
    final now = DateTime.now();
    final isFriday = now.weekday == DateTime.friday;
    final weekdayNames = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO'];
    final currentDayName = weekdayNames[now.weekday - 1];
    final weekProgress = now.weekday / 7.0;
    final progressPercentage = (weekProgress * 100).toInt();

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 60),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Text('Buen día PRO,', style: TextStyle(color: AppTheme.textMuted, fontSize: 16)),
                   Text(userName, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
                ],
              ),
              Row(
                children: [
                  const Icon(LucideIcons.bell, color: Colors.white, size: 24),
                  const SizedBox(width: 16),
                  Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                      boxShadow: [BoxShadow(color: AppTheme.primary.withOpacity(0.3), blurRadius: 10)],
                    ),
                    child: const Icon(LucideIcons.user, color: Colors.black, size: 24),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 32),

          if (isCoach) ...[
             _buildCoachPanelCard(),
             const SizedBox(height: 24),
          ],

          // Deluxe Weekly Progress
          _buildDeluxeProgressCard(currentDayName, progressPercentage, weekProgress),
          const SizedBox(height: 32),
          
          // Hoy Section
          const Text('HOY', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 2, color: AppTheme.primary)),
          const SizedBox(height: 16),
          _buildTaskCard(
            title: 'Día de ${_todayRoutine}',
            subtitle: _todayExercises.isNotEmpty ? '${_todayExercises.length} ejercicios' : 'Recuperación activa',
            icon: LucideIcons.dumbbell,
            iconColor: Colors.blueAccent,
            onTap: () => widget.onNavigate(2),
          ),
          const SizedBox(height: 12),
          _buildTaskCard(
            title: 'Nutrición PRO',
            subtitle: 'Alimentación personalizada',
            icon: LucideIcons.utensils,
            iconColor: Colors.orangeAccent,
            onTap: () => widget.onNavigate(3),
          ),

          const SizedBox(height: 32),
          // REPORTE SEMANAL
          const Text('REPORTE SEMANAL', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 2, color: AppTheme.primary)),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: _buildMetricCard(
                'Peso actual', 
                '${_lastMeasurement?['weight'] ?? '--'} kg', 
                LucideIcons.scale, 
                Colors.greenAccent
              )),
              const SizedBox(width: 16),
              Expanded(child: _buildMetricCard(
                'Check-in', 
                isFriday ? '¡ENVIAR!' : 'Viernes', 
                isFriday ? LucideIcons.checkCircle : LucideIcons.lock, 
                isFriday ? Colors.blueAccent : AppTheme.textMuted,
                onTap: isFriday ? () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ReportScreen())) : null,
              )),
            ],
          ),
          const SizedBox(height: 48),
        ],
      ),
    );
  }

  Widget _buildDeluxeProgressCard(String dayName, int percentage, double progress) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 30)],
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppTheme.surface, AppTheme.surface.withOpacity(0.8)],
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(dayName, style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.bold, letterSpacing: 1.5, fontSize: 12)),
              const SizedBox(height: 4),
              const Text('Tu Semana', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22)),
              const SizedBox(height: 4),
              const Text('Consolidando hábitos PRO', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
            ],
          ),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 70, height: 70,
                child: CircularProgressIndicator(
                  value: progress,
                  strokeWidth: 8,
                  backgroundColor: Colors.white.withOpacity(0.05),
                  color: AppTheme.primary,
                ),
              ),
              Text('$percentage%', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCoachPanelCard() {
    return PremiumCard(
      padding: 20,
      child: InkWell(
        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminUsersScreen())),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white, shape: BoxShape.circle),
              child: const Icon(LucideIcons.settings, color: Colors.blueAccent, size: 24),
            ),
            const SizedBox(width: 16),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('PANEL COACH PRO', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                  Text('Gestión de tus atletas y altas', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                ],
              ),
            ),
            const Icon(LucideIcons.chevronRight, color: AppTheme.textMuted),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCard() {
    return PremiumCard(
      padding: 20,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Tu Semana', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              SizedBox(height: 4),
              Text('Consolidando hábitos PRO', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
            ],
          ),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 60, height: 60,
                child: CircularProgressIndicator(
                  value: 0.75,
                  strokeWidth: 6,
                  backgroundColor: Colors.white.withOpacity(0.05),
                  color: AppTheme.primary,
                ),
              ),
              const Text('75%', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTaskCard({required String title, required String subtitle, required IconData icon, required Color iconColor, required VoidCallback onTap}) {
    return PremiumCard(
      padding: 16,
      child: InkWell(
        onTap: onTap,
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [iconColor.withOpacity(0.3), iconColor.withOpacity(0.1)]),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: iconColor, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                  Text(subtitle, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                ],
              ),
            ),
            const Icon(LucideIcons.playCircle, color: Colors.white, size: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon, Color color, {VoidCallback? onTap}) {
    return PremiumCard(
      padding: 16,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 16),
            Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  void _showCheckInModal() {
    final weightController = TextEditingController();
    final waistController = TextEditingController();
    final chestController = TextEditingController();
    final hipController = TextEditingController();
    final thighController = TextEditingController();
    final bicepsController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Check-in Semanal (Viernes)'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: weightController, decoration: const InputDecoration(labelText: 'Peso (kg)'), keyboardType: TextInputType.number),
              TextField(controller: waistController, decoration: const InputDecoration(labelText: 'Cintura (cm)'), keyboardType: TextInputType.number),
              TextField(controller: chestController, decoration: const InputDecoration(labelText: 'Pecho (cm)'), keyboardType: TextInputType.number),
              TextField(controller: hipController, decoration: const InputDecoration(labelText: 'Cadera (cm)'), keyboardType: TextInputType.number),
              TextField(controller: thighController, decoration: const InputDecoration(labelText: 'Muslo (cm)'), keyboardType: TextInputType.number),
              TextField(controller: bicepsController, decoration: const InputDecoration(labelText: 'Bíceps (cm)'), keyboardType: TextInputType.number),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              await ApiService().logMeasurement({
                'weight': double.tryParse(weightController.text),
                'waist': double.tryParse(waistController.text),
                'chest': double.tryParse(chestController.text),
                'hip': double.tryParse(hipController.text),
                'thigh': double.tryParse(thighController.text),
                'biceps': double.tryParse(bicepsController.text),
              });
              Navigator.pop(context);
              _loadDashboardData();
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('¡Medidas enviadas al Coach!')));
            },
            child: const Text('Enviar'),
          ),
        ],
      ),
    );
  }
}
