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
import 'admin_plan_editor.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  final List<Widget> _pages;
  
  _DashboardScreenState() : _pages = [];

  @override
  void initState() {
    super.initState();
    _pages.addAll([
      DashboardHome(onTabChange: _onTabTapped),
      const ChatScreen(),
      const WorkoutScreen(),
      const DietScreen(),
      const ProfileScreen(),
    ]);
  }

  void _onTabTapped(int index) {
    setState(() {
      if (index == 0) _pages[0] = DashboardHome(key: UniqueKey(), onTabChange: _onTabTapped);
      if (index == 2) _pages[2] = WorkoutScreen(key: UniqueKey());
      if (index == 3) _pages[3] = DietScreen(key: UniqueKey());
      if (index == 4) _pages[4] = ProfileScreen(key: UniqueKey());
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        index: _currentIndex,
        children: _pages,
      ),
      floatingActionButton: _currentIndex == 0 ? FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ReportScreen())).then((_) => _onTabTapped(0)),
        backgroundColor: AppTheme.primary,
        foregroundColor: Colors.black,
        icon: const Icon(LucideIcons.clipboardCheck),
        label: const Text('REPORTE VIP', style: TextStyle(fontWeight: FontWeight.w900)),
      ) : null,
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
  final Function(int) onTabChange;
  const DashboardHome({super.key, required this.onTabChange});

  @override
  State<DashboardHome> createState() => _DashboardHomeState();
}

class _DashboardHomeState extends State<DashboardHome> {
  bool _isLoading = true;
  String _todayRoutine = 'Descanso';
  String _todayDiet = 'Pendiente';
  int _exerciseCount = 0;
  int _foodCount = 0;
  bool _reportSubmittedThisWeek = false;
  Map<String, dynamic>? _lastWeight;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    try {
      await ApiService().refreshProfile();
      final workout = await ApiService().getWorkoutPlan();
      final diet = await ApiService().getDietPlan();
      final measurements = await ApiService().getMeasurements(ApiService().userId ?? '');
      
      final now = DateTime.now();
      final days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
      final todayName = days[now.weekday - 1];
      
      final todayRoutine = workout.where((e) => 
        e['day_of_week'] == todayName || 
        e['day_of_week'] == 'Día ${now.weekday}'
      ).toList();

      if (mounted) {
        setState(() {
          if (todayRoutine.isNotEmpty) {
            final Set<String> muscles = {};
            for (var e in todayRoutine) {
                final tm = e['target_muscles']?.toString();
                if (tm != null && tm.isNotEmpty && tm != 'Gral') {
                    muscles.add(tm);
                } else {
                    final mg = e['muscle_group']?.toString();
                    if (mg != null && mg.isNotEmpty) muscles.add(mg);
                }
            }
            _todayRoutine = muscles.isNotEmpty ? muscles.take(2).join(' - ') : 'ENTRENAMIENTO PRO';
            _exerciseCount = todayRoutine.length;
          } else {
            // Check if there are ANY routines at all
            if (workout.isNotEmpty) {
              _todayRoutine = 'DÍA DE DESCANSO / RECUPERACIÓN';
              _exerciseCount = 0;
            } else {
              _todayRoutine = 'SIN RUTINA ASIGNADA';
              _exerciseCount = 0;
            }
          }
          
          final foodForToday = diet.where((f) => 
            f['day_name'] == todayName || 
            f['day_name'] == 'Día ${now.weekday}'
          ).toList();

          if (foodForToday.isNotEmpty) {
            _todayDiet = '${foodForToday.length} ALIMENTOS PARA HOY';
            _foodCount = foodForToday.length;
          } else {
            _todayDiet = diet.isNotEmpty ? 'REVISA TU PLAN NUTRICIONAL' : 'SIN DIETA ASIGNADA';
            _foodCount = 0;
          }
          
          if (measurements.isNotEmpty) {
            _lastWeight = measurements.last;
          }

          // Check if report was submitted this week (last 7 days and it's a Friday report)
          final history = await ApiService().getReportHistory(ApiService().userId ?? '');
          if (history.isNotEmpty) {
            final lastReportDate = DateTime.tryParse(history.first['date'] ?? '');
            if (lastReportDate != null) {
              final difference = DateTime.now().difference(lastReportDate).inDays;
              _reportSubmittedThisWeek = difference < 7;
            }
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
    final userEmail = ApiService().userEmail?.toLowerCase() ?? '';
    final isCoach = ApiService().isCoach || userEmail == 'mitorrgo@gmail.com' || userEmail == 'mtfitness2026@gmail.com';

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.surfaceGradient,
      ),
      child: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadAll,
          color: AppTheme.primary,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            physics: const AlwaysScrollableScrollPhysics(), // Important for RefreshIndicator
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(name, isCoach),
                const SizedBox(height: 24),

                // Reporte Semanal VIP (Movido arriba para máxima visibilidad)
                _buildOptionCard(
                  title: 'REPORTE SEMANAL VIP',
                  subtitle: _reportSubmittedThisWeek ? '¡REPORTE COMPLETADO!' : 'ENVIAR PESO Y FOTOS DE PROGRESO',
                  icon: _reportSubmittedThisWeek ? LucideIcons.checkCircle2 : LucideIcons.badgeAlert,
                  color: _reportSubmittedThisWeek ? Colors.greenAccent : Colors.amberAccent,
                  subtitleBold: true,
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ReportScreen())).then((_) => _loadAll()),
                ),
                const SizedBox(height: 32),

                if (isCoach) ...[
                  _buildSectionTitle('ZONA COACH'),
                  const SizedBox(height: 16),
                  _buildOptionCard(
                    title: 'GESTIONAR MI PLAN PERSONAL',
                    subtitle: 'Diseñar mi rutina y dieta propia',
                    icon: LucideIcons.userCheck,
                    color: AppTheme.primary,
                    onTap: () {
                      Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => AdminPlanEditor(userId: ApiService().userId!, userName: 'MI PLAN PERSONAL')
                      )).then((_) => _loadAll());
                    },
                  ),
                  const SizedBox(height: 12),
                  _buildOptionCard(
                    title: 'PANEL DE CONTROL ATLETAS',
                    subtitle: 'Gestionar clientes y aprobaciones',
                    icon: LucideIcons.shieldCheck,
                    color: AppTheme.accent,
                    onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminUsersScreen())).then((_) => _loadAll()),
                  ),
                  const SizedBox(height: 32),
                ],

                // Main Status Card
                _buildStatusCard(),
                const SizedBox(height: 32),

                _buildSectionTitle('MI PLAN DE HOY'),
                const SizedBox(height: 16),
                
                _buildOptionCard(
                  title: 'RUTINA DE HOY',
                  subtitle: _exerciseCount > 0 ? _todayRoutine.toUpperCase() : 'Día de recuperación',
                  icon: LucideIcons.dumbbell,
                  color: AppTheme.primary,
                  subtitleBold: true,
                  onTap: () => widget.onTabChange(2),
                ),
                const SizedBox(height: 12),
                _buildOptionCard(
                  title: 'PLAN NUTRICIONAL',
                  subtitle: _foodCount > 0 ? 'Ver mis $_foodCount alimentos de hoy' : 'Ver dieta completa y macros',
                  icon: LucideIcons.utensils,
                  color: Colors.orangeAccent,
                  onTap: () => widget.onTabChange(3),
                ),

                const SizedBox(height: 32),
                _buildSectionTitle('PROGRESO Y MÉTRICAS'),
                const SizedBox(height: 16),
                
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = (constraints.maxWidth - 24) / 3;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _buildSmallMetric('Peso', '${ApiService().currentWeight ?? '--'} kg', LucideIcons.scale, width, onTap: () => widget.onTabChange(4)),
                        _buildSmallMetric('Bíceps', '${ApiService().biceps ?? '--'} cm', LucideIcons.activity, width, onTap: () => widget.onTabChange(4)),
                        _buildSmallMetric('Cintura', '${ApiService().waist ?? '--'} cm', LucideIcons.activity, width, onTap: () => widget.onTabChange(4)),
                        _buildSmallMetric('Cadera', '${ApiService().hip ?? '--'} cm', LucideIcons.activity, width, onTap: () => widget.onTabChange(4)),
                        _buildSmallMetric('Muslo', '${ApiService().thigh ?? '--'} cm', LucideIcons.activity, width, onTap: () => widget.onTabChange(4)),
                        _buildSmallMetric('Perfil', 'Abrir', LucideIcons.user, width, onTap: () => widget.onTabChange(4)),
                      ],
                    );
                  }
                ),
                const SizedBox(height: 40),
                Center(
                  child: Text(
                    'MT FITNESS PRO v1.1.0 | ID: ${ApiService().userId}',
                    style: TextStyle(color: Colors.white.withOpacity(0.05), fontSize: 10),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
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
          child: CircleAvatar(
            backgroundColor: AppTheme.surface,
            radius: 24,
            backgroundImage: ApiService().profileImage != null ? NetworkImage('${ApiService.uploadsUrl}${ApiService().profileImage}') : null,
            child: ApiService().profileImage == null ? const Icon(LucideIcons.user, color: AppTheme.primary) : null,
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
              Text(
                ApiService().isCoach ? 'PANEL DE CONTROL' : 'ESTADO SEMANAL',
                style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.bold, letterSpacing: 2, fontSize: 12),
              ),
              Icon(ApiService().isCoach ? LucideIcons.award : LucideIcons.flame, color: AppTheme.primary, size: 20),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            ApiService().isCoach ? 'Dashboard de Coaching' : '¡Vas por buen camino!',
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            ApiService().isCoach 
              ? 'Tienes total control sobre los planes PRO.' 
              : 'Has completado el 75% de tus objetivos de esta semana.',
            style: const TextStyle(color: AppTheme.textMuted, fontSize: 14),
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

  Widget _buildOptionCard({required String title, required String subtitle, required IconData icon, required Color color, required VoidCallback onTap, bool subtitleBold = false}) {
    return PremiumCard(
      padding: 0,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: Padding(
          padding: const EdgeInsets.all(16),
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
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1.2, color: AppTheme.textMuted)),
                  const SizedBox(height: 4),
                  Text(
                    subtitle, 
                    style: TextStyle(
                      color: subtitleBold ? Colors.white : AppTheme.textMuted, 
                      fontSize: 16, 
                      fontWeight: subtitleBold ? FontWeight.w900 : FontWeight.normal
                    )
                  ),
                ],
              ),
            ),
            const Icon(LucideIcons.chevronRight, color: AppTheme.textMuted, size: 20),
          ],
        ),
      ),
    ),
  );
}

  Widget _buildSmallMetric(String label, String value, IconData icon, double width, {VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width,
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Icon(icon, color: AppTheme.primary, size: 20),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 10, letterSpacing: 1.0)),
          ],
        ),
      ),
    );
  }
}
