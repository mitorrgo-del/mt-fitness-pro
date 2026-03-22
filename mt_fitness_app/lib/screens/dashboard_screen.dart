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
  bool _isLoadingWorkout = true;
  String _todayRoutine = 'Descanso';
  List<dynamic> _todayExercises = [];
  
  @override
  void initState() {
    super.initState();
    _loadTodayWorkout();
  }

  Future<void> _loadTodayWorkout() async {
    try {
      final workout = await ApiService().getWorkoutPlan();
      final now = DateTime.now();
      final days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
      final todayName = days[now.weekday - 1];

      final todayPlans = workout.where((e) => e['day_of_week'] == todayName).toList();
      
      if (todayPlans.isNotEmpty) {
        String muscles = todayPlans.first['target_muscles'] ?? '';
        if (muscles.toString().isEmpty) {
          muscles = todayPlans.map((e) => e['muscle_group']).toSet().join(' & ');
        }
        setState(() {
          _todayRoutine = muscles;
          _todayExercises = todayPlans;
          _isLoadingWorkout = false;
        });
      } else {
        setState(() {
          _todayRoutine = 'Descanso';
          _todayExercises = [];
          _isLoadingWorkout = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingWorkout = false);
    }
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
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('¡Medidas enviadas al Coach!')));
            },
            child: const Text('Enviar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isFriday = DateTime.now().weekday == DateTime.friday;
    final userName = ApiService().userName ?? 'Guerrero';

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(userName),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 16),
                const Text(
                  'Acceso Rápido',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 1.1,
                  children: [
                    _buildActionCard(context, LucideIcons.dumbbell, 'Entrenamiento', 'Tu rutina de hoy', () {
                      widget.onNavigate(2); // Tab index for Workout
                    }),
                    _buildActionCard(context, LucideIcons.utensils, 'Nutrición', 'Plan de comidas', () {
                      widget.onNavigate(3); // Tab index for Diet
                    }),
                    _buildActionCard(context, LucideIcons.user, 'Mi Perfil', 'Datos personales', () {
                      widget.onNavigate(4); // Tab index for Profile
                    }),
                    _buildActionCard(context, LucideIcons.messageCircle, 'Chat', 'Hablar con Coach', () {
                      widget.onNavigate(1); // Tab index for Chat
                    }),
                    if (ApiService().isCoach) ...[
                      _buildActionCard(context, LucideIcons.settings, 'Panel Coach', 'Gestión PRO', () {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminUsersScreen()));
                      }),
                      _buildActionCard(context, LucideIcons.user, 'Mi Propio Plan', 'Autogestión', () {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => AdminPlanEditor(
                          userId: ApiService().userId ?? '', 
                          userName: 'Mi Plan',
                        )));
                      }),
                      _buildActionCard(context, LucideIcons.instagram, 'Redes (IA)', 'Gestión Social', () {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminSocialScreen()));
                      }),
                    ],
                  ],
                ),
                const SizedBox(height: 32),
                _buildPlanningSection(isFriday),
                const SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(String userName) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 72, 24, 32),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hola, $userName',
                style: TextStyle(color: AppTheme.textMuted, fontSize: 16),
              ),
              const SizedBox(height: 4),
              const Text(
                'MT FITNESS coach',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const CircleAvatar(
            radius: 24,
            backgroundImage: NetworkImage('https://via.placeholder.com/150'),
          ),
        ],
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, IconData icon, String title, String sub, VoidCallback onTap) {
    return PremiumCard(
      padding: 12,
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: AppTheme.primary, size: 28),
            const SizedBox(height: 12),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 2),
            Text(sub, style: TextStyle(color: AppTheme.textMuted, fontSize: 10)),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanningSection(bool isFriday) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Planificación de hoy', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        _isLoadingWorkout 
           ? const LinearProgressIndicator(color: AppTheme.primary, backgroundColor: Colors.transparent)
           : _buildPlanItem(
              _todayRoutine, 
              _todayRoutine == 'Descanso' ? 'Día de recuperación' : 'Toca entrenamiento', 
              LucideIcons.calendar,
              onTap: _todayRoutine == 'Descanso' ? null : () => widget.onNavigate(2),
             ),
        const SizedBox(height: 12),
        _buildPlanItem(
          'Check-in medidas', 
          isFriday ? '¡Es viernes! Toca pesarse' : 'Disponible los viernes', 
          LucideIcons.checkCircle,
          onTap: isFriday ? _showCheckInModal : null,
          isActive: isFriday,
        ),
      ],
    );
  }

  Widget _buildPlanItem(String title, String sub, IconData icon, {VoidCallback? onTap, bool isActive = true}) {
    final isRoutineToday = title != 'Check-in medidas' && title != 'Descanso';

    return PremiumCard(
      padding: 0,
      child: ListTile(
        onTap: onTap,
        enabled: isActive,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: (onTap != null ? AppTheme.primary : Colors.grey).withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: onTap != null ? AppTheme.primary : Colors.grey, size: 24),
        ),
        title: Text(
          title, 
          style: TextStyle(
            fontWeight: FontWeight.bold, 
            fontSize: isRoutineToday ? 20 : 16,
            color: isRoutineToday ? AppTheme.primary : (isActive ? Colors.white : Colors.grey),
            letterSpacing: isRoutineToday ? 0.5 : 0,
          )
        ),
        subtitle: Text(
          sub, 
          style: TextStyle(
            color: isRoutineToday ? AppTheme.primary.withOpacity(0.7) : AppTheme.textMuted, 
            fontSize: isRoutineToday ? 13 : 12,
            fontWeight: isRoutineToday ? FontWeight.w600 : FontWeight.normal,
          )
        ),
        trailing: onTap != null ? const Icon(LucideIcons.chevronRight, size: 20, color: AppTheme.textMuted) : null,
      ),
    );
  }
}
