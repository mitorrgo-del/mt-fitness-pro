import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';
import '../widgets/premium_card.dart';
import 'chat_screen.dart';
import 'workout_screen.dart';
import 'diet_screen.dart';
import 'profile_screen.dart';
import 'admin_users_screen.dart';
import '../services/api_service.dart';
import 'report_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const DashboardHome(),
    const ChatScreen(),
    const WorkoutScreen(),
    const DietScreen(),
    const ProfileScreen(),
  ];

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
          color: AppTheme.bgColor,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.5),
              blurRadius: 20,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: _onTabTapped,
          type: BottomNavigationBarType.fixed,
          backgroundColor: AppTheme.bgColor.withOpacity(0.8),
          selectedItemColor: AppTheme.primary,
          unselectedItemColor: AppTheme.textMuted,
          showSelectedLabels: true,
          showUnselectedLabels: false,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(icon: Icon(LucideIcons.home, size: 22), label: 'Inicio'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.messageCircle, size: 22), label: 'Chat'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.dumbbell, size: 22), label: 'Rutina'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.utensils, size: 22), label: 'Dieta'),
            BottomNavigationBarItem(icon: Icon(LucideIcons.user, size: 22), label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}

class DashboardHome extends StatefulWidget {
  const DashboardHome({super.key});

  @override
  State<DashboardHome> createState() => _DashboardHomeState();
}

class _DashboardHomeState extends State<DashboardHome> {
  bool _isLoading = true;
  String _todayRoutine = 'Descanso';
  int _exerciseCount = 0;
  Map<String, dynamic>? _lastWeight;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    try {
      final workout = await ApiService().getWorkoutPlan();
      final measurements = await ApiService().getMeasurements(ApiService().userId ?? '');
      
      final now = DateTime.now();
      final days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
      final todayName = days[now.weekday - 1];
      final todayPlans = workout.where((e) => e['day_of_week'] == todayName).toList();

      if (mounted) {
        setState(() {
          if (todayPlans.isNotEmpty) {
            _todayRoutine = todayPlans.first['target_muscles'] ?? 'Entrenamiento';
            _exerciseCount = todayPlans.length;
          }
          if (measurements.isNotEmpty) {
            _lastWeight = measurements.last;
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = ApiService().userName?.split(' ')[0] ?? 'Atleta';
    final isCoach = ApiService().isCoach;

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.surfaceGradient,
      ),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          physics: const BouncingScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              _buildHeader(name, isCoach),
              const SizedBox(height: 32),

              if (isCoach) ...[
                _buildOptionCard(
                  title: 'PANEL DE CONTROL COACH',
                  subtitle: 'Gestionar atletas y planes',
                  icon: LucideIcons.shieldCheck,
                  color: AppTheme.accent,
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminUsersScreen())),
                ),
                const SizedBox(height: 20),
              ],

              // Main Status Card
              _buildStatusCard(),
              const SizedBox(height: 32),

              // Quick Actions
              _buildSectionTitle('MI PLAN DE HOY'),
              const SizedBox(height: 16),
              
              _buildOptionCard(
                title: 'Rutina: $_todayRoutine',
                subtitle: _exerciseCount > 0 ? '$_exerciseCount ejercicios hoy' : 'Día de recuperación',
                icon: LucideIcons.dumbbell,
                color: AppTheme.primary,
                onTap: () { /* Navigate via Tab */ },
              ),
              const SizedBox(height: 12),
              _buildOptionCard(
                title: 'Plan Nutricional',
                subtitle: 'Ver mis comidas y macros',
                icon: LucideIcons.utensils,
                color: Colors.orangeAccent,
                onTap: () { /* Navigate via Tab */ },
              ),

              const SizedBox(height: 32),
              _buildSectionTitle('PROGRESO Y MÉTRICAS'),
              const SizedBox(height: 16),
              
              Row(
                children: [
                  Expanded(
                    child: _buildMetricMiniCard(
                      label: 'Peso Actual',
                      value: '${_lastWeight?['weight'] ?? '--'} kg',
                      icon: LucideIcons.scale,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _buildMetricMiniCard(
                      label: 'Check-in',
                      value: 'Viernes',
                      icon: LucideIcons.camera,
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ReportScreen())),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(String name, bool isCoach) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bienvenido,',
              style: GoogleFonts.outfit(color: AppTheme.textMuted, fontSize: 16),
            ),
            Text(
              name.toUpperCase(),
              style: GoogleFonts.outfit(
                fontSize: 28, 
                fontWeight: FontWeight.w900, 
                letterSpacing: -0.5,
                color: Colors.white,
              ),
            ),
          ],
        ),
        Container(
          padding: const EdgeInsets.all(2),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: AppTheme.primaryGradient,
          ),
          child: const CircleAvatar(
            backgroundColor: AppTheme.surface,
            radius: 24,
            child: Icon(LucideIcons.user, color: AppTheme.primary),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusCard() {
    return PremiumCard(
      glass: true,
      gradient: LinearGradient(
        colors: [AppTheme.primary.withOpacity(0.2), Colors.transparent],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'ESTADO SEMANAL',
                style: TextStyle(color: AppTheme.primary, fontWeight: FontWeight.bold, letterSpacing: 2, fontSize: 12),
              ),
              Icon(LucideIcons.flame, color: AppTheme.primary, size: 20),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            '¡Vas por buen camino!',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Has completado el 75% de tus objetivos de esta semana.',
            style: TextStyle(color: AppTheme.textMuted, fontSize: 14),
          ),
          const SizedBox(height: 20),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: 0.75,
              minHeight: 8,
              backgroundColor: Colors.white.withOpacity(0.05),
              valueColor: const AlwaysStoppedAnimation(AppTheme.primary),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: GoogleFonts.outfit(
        fontSize: 14,
        fontWeight: FontWeight.w900,
        letterSpacing: 2.0,
        color: AppTheme.textMuted,
      ),
    );
  }

  Widget _buildOptionCard({required String title, required String subtitle, required IconData icon, required Color color, required VoidCallback onTap}) {
    return PremiumCard(
      padding: 16,
      child: InkWell(
        onTap: onTap,
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(subtitle, style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                ],
              ),
            ),
            const Icon(LucideIcons.chevronRight, color: AppTheme.textMuted, size: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricMiniCard({required String label, required String value, required IconData icon, VoidCallback? onTap}) {
    return PremiumCard(
      padding: 20,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: AppTheme.primary, size: 24),
            const SizedBox(height: 16),
            Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              value,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
