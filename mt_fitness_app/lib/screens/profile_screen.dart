import 'dart:io';
import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:image_picker/image_picker.dart';
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
  File? _imageFile;
  final ImagePicker _picker = ImagePicker();

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

  Future<void> _pickImage() async {
    final XFile? selected = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 50);
    if (selected != null) {
      setState(() => _imageFile = File(selected.path));
    }
  }

  Future<void> _handleSave() async {
    setState(() => _isLoading = true);
    try {
      final payload = {
        'name': _nameController.text,
        'surname': _surnameController.text,
        'age': int.tryParse(_ageController.text),
        'height': double.tryParse(_heightController.text),
        'current_weight': double.tryParse(_weightController.text),
        'objective': _selectedObjective,
      };

      await ApiService().updateProfile(payload, imagePath: _imageFile?.path);
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Perfil actualizado correctamente'),
          backgroundColor: Colors.green.shade800,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red.shade800),
      );
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
              child: GestureDetector(
                onTap: _pickImage,
                child: Stack(
                  children: [
                    CircleAvatar(
                      radius: 54,
                      backgroundColor: AppTheme.primary,
                      child: CircleAvatar(
                        radius: 52,
                        backgroundColor: AppTheme.surface,
                        backgroundImage: _imageFile != null 
                            ? FileImage(_imageFile!) 
                            : (ApiService().profileImage != null 
                                ? NetworkImage('${ApiService.uploadsUrl}${ApiService().profileImage}') 
                                : null) as ImageProvider?,
                        child: (_imageFile == null && ApiService().profileImage == null)
                            ? const Icon(LucideIcons.user, size: 40, color: AppTheme.primary)
                            : null,
                      ),
                    ),
                    Positioned(
                      bottom: 0, right: 0,
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppTheme.primary, 
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.bgColor, width: 2),
                        ),
                        child: const Icon(LucideIcons.camera, color: Colors.black, size: 16),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
            
            if (_measurements.length >= 2) ...[
               const Text('EVOLUCIÓN DE PESO', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary, fontSize: 12, letterSpacing: 1.2)),
               const SizedBox(height: 16),
               _buildChart(),
               const SizedBox(height: 32),
            ],

            const Text('DATOS PERSONALES', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary, fontSize: 12, letterSpacing: 1.2)),
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
                   const Align(alignment: Alignment.centerLeft, child: Text('Objetivo Actual', style: TextStyle(fontSize: 12, color: AppTheme.textMuted))),
                   const SizedBox(height: 8),
                   DropdownButton<String>(
                     value: _selectedObjective,
                     isExpanded: true,
                     dropdownColor: AppTheme.surface,
                     underline: Container(height: 1, color: AppTheme.border),
                     style: const TextStyle(color: Colors.white, fontSize: 16),
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
                backgroundColor: Colors.red.withOpacity(0.05),
                foregroundColor: Colors.redAccent,
                elevation: 0,
                side: BorderSide(color: Colors.redAccent.withOpacity(0.3), width: 1),
                minimumSize: const Size(double.infinity, 54),
              ),
            ),
            const SizedBox(height: 80), // More padding at bottom
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
