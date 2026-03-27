import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../widgets/premium_card.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _nameController = TextEditingController(text: ApiService().userName);
  final _surnameController = TextEditingController(text: ApiService().surname);
  final _ageController = TextEditingController(text: ApiService().age?.toString());
  final _heightController = TextEditingController(text: ApiService().height?.toString());
  final _weightController = TextEditingController(text: ApiService().currentWeight?.toString());
  String _selectedObjective = ApiService().objective ?? 'Mantenimiento';
  
  bool _isLoading = false;
  List<dynamic> _measurements = [];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final data = await ApiService().getMeasurements(ApiService().userId ?? '');
    if (mounted) {
      setState(() => _measurements = data);
    }
  }

  Future<void> _handleSave() async {
    setState(() => _isLoading = true);
    try {
      await ApiService().updateProfile({
        'name': _nameController.text,
        'surname': _surnameController.text,
        'age': int.tryParse(_ageController.text),
        'height': double.tryParse(_heightController.text),
        'current_weight': double.tryParse(_weightController.text),
        'objective': _selectedObjective,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Perfil actualizado correctamente')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Perfil PRO'),
        actions: [
          if (!_isLoading)
            IconButton(
              icon: const Icon(LucideIcons.save, color: AppTheme.primary),
              onPressed: _handleSave,
            )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Stack(
                children: [
                  CircleAvatar(
                    radius: 50,
                    backgroundColor: AppTheme.primary.withOpacity(0.1),
                    child: const Icon(LucideIcons.user, size: 40, color: AppTheme.primary),
                  ),
                  Positioned(
                    bottom: 0, right: 0,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(color: AppTheme.primary, shape: BoxShape.circle),
                      child: const Icon(LucideIcons.camera, color: Colors.white, size: 16),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            
            if (_measurements.length >= 2) ...[
               const Text('EVOLUCIÓN DE PESO', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
               const SizedBox(height: 16),
               _buildChart(),
               const SizedBox(height: 32),
            ],

            const Text('DATOS PERSONALES', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
            const SizedBox(height: 16),
            PremiumCard(
              padding: 24,
              child: Column(
                children: [
                   TextField(controller: _nameController, decoration: const InputDecoration(labelText: 'Nombre')),
                   const SizedBox(height: 16),
                   TextField(controller: _surnameController, decoration: const InputDecoration(labelText: 'Apellidos')),
                   const SizedBox(height: 16),
                   Row(
                     children: [
                        Expanded(child: TextField(controller: _ageController, decoration: const InputDecoration(labelText: 'Edad'), keyboardType: TextInputType.number)),
                        const SizedBox(width: 16),
                        Expanded(child: TextField(controller: _heightController, decoration: const InputDecoration(labelText: 'Estatura (cm)'), keyboardType: TextInputType.number)),
                     ],
                   ),
                   const SizedBox(height: 16),
                   TextField(controller: _weightController, decoration: const InputDecoration(labelText: 'Peso Inicial (kg)'), keyboardType: TextInputType.number),
                   const SizedBox(height: 24),
                   const Align(alignment: Alignment.centerLeft, child: Text('Objetivo', style: TextStyle(fontSize: 12, color: AppTheme.textMuted))),
                   DropdownButton<String>(
                     value: _selectedObjective,
                     isExpanded: true,
                     dropdownColor: AppTheme.surface,
                     underline: Container(height: 1, color: AppTheme.border),
                     items: ['Bajar grasa', 'Subir masa muscular', 'Mantenimiento']
                        .map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                     onChanged: (v) => setState(() => _selectedObjective = v!),
                   ),
                ],
              ),
            ),
            const SizedBox(height: 48),
            ElevatedButton.icon(
              onPressed: () {
                ApiService().logout();
                Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (route) => false);
              },
              icon: const Icon(LucideIcons.logOut),
              label: const Text('Cerrar Sesión'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red.withOpacity(0.1),
                foregroundColor: Colors.red,
                side: const BorderSide(color: Colors.red, width: 0.5),
                minimumSize: const Size(double.infinity, 54),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildChart() {
    return Container(
      height: 200,
      padding: const EdgeInsets.only(right: 20, top: 20, left: 10, bottom: 10),
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
              spots: _measurements.asMap().entries.map((e) {
                return FlSpot(e.key.toDouble(), (e.value['weight'] as num).toDouble());
              }).toList(),
              isCurved: true,
              color: AppTheme.primary,
              barWidth: 4,
              dotData: const FlDotData(show: true),
              belowBarData: BarAreaData(
                show: true, 
                color: AppTheme.primary.withOpacity(0.1),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
